import sys, os
sys.path.insert(0, 'code')
import pandas as pd
from datetime import datetime, timedelta
from data_loader import DataLoader
from indexes import DatasetIndexes
from currency import CurrencyConverter
from image_resolver import ImageResolver
from models import FinancialProfile, FinancialEvent, Message, Request, PaymentOption

loader = DataLoader('dataset')
profiles = loader.load_financial_profiles('financial_profiles.csv')
events = loader.load_financial_events('financial_events.csv')
payment_options = loader.load_request_payment_options('request_payment_options.csv')
messages = loader.load_messages('messages.csv')
images = loader.load_images('images.csv')
exchange_rates = loader.load_exchange_rates('exchange_rates.csv')
sample_dict = loader.load_sample_requests('sample_requests.csv')
sample_requests = sample_dict['requests']
ground_truths = sample_dict['ground_truths']

indexes = DatasetIndexes(profiles, events, payment_options, messages, images, exchange_rates)
cc = CurrencyConverter(exchange_rates)
ir = ImageResolver('dataset', images)

def format_amount(amt: float) -> str:
    if abs(amt - round(amt)) < 1e-4:
        return str(int(round(amt)))
    return f"{amt:.2f}"

def get_next_salary_date(u_events: list, req_date_str: str) -> str:
    salary_events = [
        e for e in u_events
        if (e.category == 'salary' or e.event_type == 'income')
        and e.direction == 'credit'
        and e.status in ('settled', 'scheduled')
    ]
    future_salaries = []
    for e in salary_events:
        t_date = e.settlement_date if (e.settlement_date and e.settlement_date > req_date_str) else e.event_date
        if t_date > req_date_str:
            future_salaries.append(t_date)
            
    if future_salaries:
        return min(future_salaries)
        
    # Check if user has past salary to deduce standard monthly pay date
    past_salaries = [
        e for e in salary_events
        if (e.settlement_date and e.settlement_date <= req_date_str) or e.event_date <= req_date_str
    ]
    if past_salaries:
        # User has salary history but no scheduled future salary -> employment ongoing or monthly
        last_s = max(e.settlement_date if e.settlement_date else e.event_date for e in past_salaries)
        sal_day = int(last_s[8:10])
        req_dt = datetime.strptime(req_date_str, "%Y-%m-%d")
        sal_dt = datetime(req_dt.year, req_dt.month, min(sal_day, 28))
        if sal_dt <= req_dt:
            m = req_dt.month % 12 + 1
            y = req_dt.year + (req_dt.month // 12)
            sal_dt = datetime(y, m, min(sal_day, 28))
        return sal_dt.strftime("%Y-%m-%d")
        
    return None

def compute_pre_salary_outflows(prof: FinancialProfile, u_events: list, req_date_str: str, next_sal_date_str: str) -> float:
    home_curr = prof.home_currency
    outflows = 0.0
    
    req_dt = datetime.strptime(req_date_str, "%Y-%m-%d")
    limit_dt = datetime.strptime(next_sal_date_str, "%Y-%m-%d") if next_sal_date_str else req_dt + timedelta(days=30)
    
    # 1. Scheduled / pending debits between req_date and next_sal_date
    scheduled_cats = set()
    for e in u_events:
        if e.direction == 'debit' and e.status in ('scheduled', 'pending'):
            t_date = e.settlement_date if (e.settlement_date and e.settlement_date > req_date_str) else e.event_date
            if req_date_str < t_date <= limit_dt.strftime("%Y-%m-%d"):
                amt = e.amount or 0.0
                conv_amt = cc.convert(amt, e.currency, home_curr, req_date_str)
                if conv_amt:
                    outflows += conv_amt
                    scheduled_cats.add(e.category)
                    
    # 2. Monthly recurring essential expenses (rent, utilities, insurance, subscriptions, transport)
    # Check all debit events occurring in recent history and project next occurrences before limit_dt
    recent_debits = [e for e in u_events if e.direction == 'debit' and e.status == 'settled' and e.event_date <= req_date_str]
    cat_latest = {}
    for e in recent_debits:
        if e.category not in cat_latest or e.event_date > cat_latest[e.category].event_date:
            cat_latest[e.category] = e
            
    for cat, e in cat_latest.items():
        if cat in scheduled_cats:
            continue
        amt = e.amount or 0.0
        conv_amt = cc.convert(amt, e.currency, home_curr, req_date_str) or 0.0
        if conv_amt <= 0:
            continue
            
        e_dt = datetime.strptime(e.event_date, "%Y-%m-%d")
        flex = (e.flexibility or '').lower()
        
        # Determine cadence (monthly = 30 days, weekly = 7 days)
        if cat in ('rent', 'housing', 'utilities', 'insurance', 'debt_repayment', 'education', 'cloud_storage', 'streaming'):
            cadence = 30
        elif cat in ('groceries', 'transport', 'dining'):
            cadence = 14
        else:
            cadence = 30
            
        next_dt = e_dt + timedelta(days=cadence)
        while next_dt <= limit_dt:
            if next_dt > req_dt:
                outflows += conv_amt
            next_dt += timedelta(days=cadence)
            
    return outflows

print("Checking 25 sample requests with refined pre-salary engine...")
cols = ['request_id', 'amount_safe_to_pay', 'affordability_status', 'recommended_payment_method', 'payment_plan', 'earliest_date_for_full_payment', 'spending_changes_needed']

sample_df = pd.read_csv('dataset/sample_requests.csv')
mismatches = []
method_status_matches = 0

for req in sample_requests:
    rid = req.request_id
    prof = indexes.get_profile(req.user_id)
    u_events = indexes.get_events_for_user(req.user_id)
    opts = indexes.get_payment_options(rid)
    u_msgs = indexes.get_messages_for_user(req.user_id)
    gt = ground_truths[rid]
    
    next_sal = get_next_salary_date(u_events, req.request_date)
    outflows = compute_pre_salary_outflows(prof, u_events, req.request_date, next_sal)
    
    # Starting safe balance
    start_bal = prof.current_available_balance
    for e in u_events:
        if e.direction == 'debit' and e.status == 'pending' and e.event_date <= req.request_date:
            c_amt = cc.convert(e.amount or 0.0, e.currency, prof.home_currency, req.request_date) or 0.0
            start_bal -= c_amt
            
    pre_trough = start_bal - outflows
    safe_amt = max(0.0, min(req.requested_amount, pre_trough - prof.minimum_balance_to_keep))
    
    ms_match = False
    exp_m = gt['recommended_payment_method']
    exp_s = gt['affordability_status']
    
    print(f"[{rid}] req_amt={req.requested_amount}, start_bal={start_bal:.2f}, min_bal={prof.minimum_balance_to_keep:.2f}, safe_amt={safe_amt:.2f}, next_sal={next_sal} | GT: {exp_m} / {exp_s}")
