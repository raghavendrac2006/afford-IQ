import sys, os
sys.path.insert(0, os.path.abspath('code'))

import pandas as pd
from data_loader import DataLoader
from indexes import DatasetIndexes
from currency import CurrencyConverter
from image_resolver import ImageResolver
from optimizer import PaymentPlanOptimizer
from safe_amount_engine import SafeAmountEngine
from main import format_amount

loader = DataLoader('dataset')
profiles = loader.load_financial_profiles('financial_profiles.csv')
events = loader.load_financial_events('financial_events.csv')
payment_options = loader.load_request_payment_options('request_payment_options.csv')
messages = loader.load_messages('messages.csv')
images = loader.load_images('images.csv')
exchange_rates = loader.load_exchange_rates('exchange_rates.csv')
sample_requests = loader.load_requests('sample_requests.csv')

indexes = DatasetIndexes(profiles, events, payment_options, messages, images, exchange_rates)
currency_converter = CurrencyConverter(exchange_rates)
image_resolver = ImageResolver('dataset', images)
safe_engine = SafeAmountEngine(currency_converter, image_resolver)
optimizer = PaymentPlanOptimizer(currency_converter, image_resolver)

sample_df = pd.read_csv('dataset/sample_requests.csv')
cols = ['request_id', 'amount_safe_to_pay', 'affordability_status', 'recommended_payment_method', 'payment_plan', 'earliest_date_for_full_payment', 'spending_changes_needed']

mismatches = []
exact_count = 0

for req in sample_requests:
    rid = req.request_id
    prof = indexes.get_profile(req.user_id)
    u_events = indexes.get_events_for_user(req.user_id)
    opts = indexes.get_payment_options(rid)
    u_msgs = indexes.get_messages_for_user(req.user_id)
    
    cand = optimizer.evaluate_request(req, prof, u_events, opts, u_msgs)
    safe_dec = safe_engine.evaluate_request(req, prof, u_events, u_msgs)
    
    amt_safe_formatted = format_amount(safe_dec.amount_safe_to_pay)
    
    if cand.affordability_status == 'not_affordable':
        earliest_date_str = ''
    elif cand.affordability_status == 'affordable_now':
        earliest_date_str = req.request_date
    elif cand.recommended_payment_method == 'partial_payment' and '|' in cand.payment_plan:
        p2 = cand.payment_plan.split('|')[1]
        earliest_date_str = p2.split(':')[0]
    else:
        earliest_date_str = safe_dec.earliest_date_for_full_payment or ''
        
    actual = {
        'request_id': rid,
        'amount_safe_to_pay': amt_safe_formatted,
        'affordability_status': cand.affordability_status,
        'recommended_payment_method': cand.recommended_payment_method,
        'payment_plan': cand.payment_plan,
        'earliest_date_for_full_payment': earliest_date_str,
        'spending_changes_needed': cand.spending_changes_needed,
    }
    
    expected_row = sample_df[sample_df['request_id'] == rid].iloc[0]
    diffs = {}
    is_exact = True
    for c in cols[1:]:
        exp_val = str(expected_row[c]) if pd.notna(expected_row[c]) else ''
        act_val = str(actual[c]) if pd.notna(actual[c]) else ''
        if exp_val != act_val:
            is_exact = False
            diffs[c] = (exp_val, act_val)
            
    if is_exact:
        exact_count += 1
    else:
        mismatches.append((rid, diffs))

print(f'Exact All-Columns Sample Agreement: {exact_count} / {len(sample_requests)}')
print('Mismatches breakdown:')
for rid, diffs in mismatches:
    print(f'=== {rid} ===')
    for k, v in diffs.items():
        print(f'  {k}: expected="{v[0]}" | actual="{v[1]}"')
