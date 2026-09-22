import sys, os
sys.path.insert(0, 'code')
import pandas as pd
from data_loader import DataLoader
from indexes import DatasetIndexes
from currency import CurrencyConverter
from image_resolver import ImageResolver
from safe_amount_engine import SafeAmountEngine
from optimizer import PaymentPlanOptimizer

dataset_dir = 'dataset'
loader = DataLoader(dataset_dir)
sample_dict = loader.load_sample_requests('sample_requests.csv')
sample_requests = sample_dict['requests']
ground_truths = sample_dict['ground_truths']
profiles = loader.load_financial_profiles('financial_profiles.csv')
events = loader.load_financial_events('financial_events.csv')
payment_options = loader.load_request_payment_options('request_payment_options.csv')
messages = loader.load_messages('messages.csv')
images = loader.load_images('images.csv')
exchange_rates = loader.load_exchange_rates('exchange_rates.csv')

indexes = DatasetIndexes(profiles, events, payment_options, messages, images, exchange_rates)
cc = CurrencyConverter(exchange_rates)
ir = ImageResolver(dataset_dir, images)
safe_engine = SafeAmountEngine(cc, ir)
optimizer = PaymentPlanOptimizer(cc, ir)

target_ids = ['request_02', 'request_06', 'request_08', 'request_10', 'request_13', 'request_19', 'request_21']

for rid in target_ids:
    req = next(r for r in sample_requests if r.request_id == rid)
    prof = indexes.get_profile(req.user_id)
    u_events = indexes.get_events_for_user(req.user_id)
    opts = indexes.get_payment_options(rid)
    u_msgs = indexes.get_messages_for_user(req.user_id)
    gt = ground_truths[rid]
    
    print('='*80)
    print(f"REQUEST {rid} (User: {req.user_id}, Date: {req.request_date}, Amt: {req.requested_amount}, Completion: {req.desired_completion_date})")
    print(f"GT: method={gt['recommended_payment_method']}, status={gt['affordability_status']}, plan={gt['payment_plan']}, spend={gt['spending_changes_needed']}, earliest={gt['earliest_date_for_full_payment']}")
    
    cand = optimizer.evaluate_request(req, prof, u_events, opts, u_msgs)
    safe_dec = safe_engine.evaluate_request(req, prof, u_events, u_msgs)
    
    print(f"SAFE DECISION: safe_amt={safe_dec.amount_safe_to_pay}, earliest={safe_dec.earliest_date_for_full_payment}")
    print(f"OPTIMIZER CANDIDATE: method={cand.recommended_payment_method}, status={cand.affordability_status}, plan={cand.payment_plan}, spend={cand.spending_changes_needed}")
    print(f"Explanation: {cand.explanation}")
