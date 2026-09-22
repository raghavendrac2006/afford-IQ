import sys, os
sys.path.insert(0, 'code')
import pandas as pd
from datetime import datetime, timedelta
from data_loader import DataLoader
from indexes import DatasetIndexes
from currency import CurrencyConverter
from image_resolver import ImageResolver
from models import FinancialProfile, FinancialEvent, Message, Request

loader = DataLoader('dataset')
profiles = loader.load_financial_profiles('financial_profiles.csv')
events = loader.load_financial_events('financial_events.csv')
payment_options = loader.load_request_payment_options('request_payment_options.csv')
messages = loader.load_messages('messages.csv')
images = loader.load_images('images.csv')
exchange_rates = loader.load_exchange_rates('exchange_rates.csv')
sample_requests = loader.load_requests('sample_requests.csv')

indexes = DatasetIndexes(profiles, events, payment_options, messages, images, exchange_rates)
cc = CurrencyConverter(exchange_rates)
ir = ImageResolver('dataset', images)

def compute_correct_pre_salary_outflows(profile: FinancialProfile, user_events: list, request_date_str: str, next_salary_date_str: str) -> float:
    home_curr = profile.home_currency
    outflows = 0.0
    
    req_dt = datetime.strptime(request_date_str, "%Y-%m-%d")
    limit_dt = datetime.strptime(next_salary_date_str, "%Y-%m-%d") if next_salary_date_str else req_dt + timedelta(days=30)
    
    # 1. Scheduled / pending debits between request_date and limit_date
    scheduled_cats = set()
    for e in user_events:
        if e.direction == 'debit' and e.status in ('scheduled', 'pending'):
            t_date = e.settlement_date if (e.settlement_date and e.settlement_date > request_date_str) else e.event_date
            if request_date_str < t_date <= limit_dt.strftime("%Y-%m-%d"):
                amt = e.amount or 0.0
                conv_amt = cc.convert(amt, e.currency, home_curr, request_date_str)
                if conv_amt:
                    outflows += conv_amt
                    scheduled_cats.add(e.category)
                    
    # 2. Historical settled debits between previous salary and request_date: check recurring frequency
    # Filter for settled debits in last 60 days
    recent_debits = [e for e in user_events if e.direction == 'debit' and e.status == 'settled' and e.event_date <= request_date_str]
    
    # Group by category and compute average weekly / monthly cadence
    cat_events = {}
    for e in recent_debits:
        cat_events.setdefault(e.category, []).append(e)
        
    for cat, evts in cat_events.items():
        if cat in scheduled_cats:
            continue
        evts.sort(key=lambda x: x.event_date, reverse=True)
        most_recent = evts[0]
        rec_dt = datetime.strptime(most_recent.event_date, "%Y-%m-%d")
        
        # Calculate interval if multiple
        if len(evts) >= 2:
            dates = [datetime.strptime(x.event_date, "%Y-%m-%d") for x in evts[:5]]
            diffs = [(dates[i] - dates[i+1]).days for i in range(len(dates)-1)]
            avg_days = max(1, sum(diffs) // len(diffs))
        else:
            avg_days = 30
            
        amt = most_recent.amount or 0.0
        conv_amt = cc.convert(amt, most_recent.currency, home_curr, request_date_str) or 0.0
        
        if conv_amt <= 0:
            continue
            
        # Project next occurrences from most_recent.event_date
        next_dt = rec_dt + timedelta(days=avg_days)
        while next_dt <= limit_dt:
            if next_dt > req_dt:
                outflows += conv_amt
            next_dt += timedelta(days=avg_days)
            
    return outflows

print("Testing pre-salary outflow calculations for target requests...")
for rid in ['request_06', 'request_10', 'request_13', 'request_19', 'request_21']:
    req = next(r for r in sample_requests if r.request_id == rid)
    prof = indexes.get_profile(req.user_id)
    u_events = indexes.get_events_for_user(req.user_id)
    
    # Next salary
    salary_events = [e for e in u_events if (e.category == 'salary' or e.event_type == 'income') and e.direction == 'credit' and e.status in ('settled', 'scheduled')]
    future_salary = [e for e in salary_events if (e.settlement_date and e.settlement_date > req.request_date) or e.event_date > req.request_date]
    if future_salary:
        next_sal_date = min(e.settlement_date if (e.settlement_date and e.settlement_date > req.request_date) else e.event_date for e in future_salary)
    else:
        next_sal_date = None
        
    out = compute_correct_pre_salary_outflows(prof, u_events, req.request_date, next_sal_date)
    start_bal = prof.current_available_balance  # minus pending debits
    for e in u_events:
        if e.direction == 'debit' and e.status == 'pending' and e.event_date <= req.request_date:
            c_amt = cc.convert(e.amount or 0.0, e.currency, prof.home_currency, req.request_date) or 0.0
            start_bal -= c_amt
            
    pre_trough = start_bal - out
    safe_amt = max(0.0, min(req.requested_amount, pre_trough - prof.minimum_balance_to_keep))
    print(f"[{rid}] req_amt={req.requested_amount}, start_bal={start_bal:.2f}, min_bal={prof.minimum_balance_to_keep:.2f}, pre_sal_out={out:.2f}, safe_amt={safe_amt:.2f}, next_sal={next_sal_date}")
