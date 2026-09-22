import sys, os
sys.path.insert(0, 'code')
import pandas as pd
from data_loader import DataLoader
from indexes import DatasetIndexes
from currency import CurrencyConverter
from image_resolver import ImageResolver
from safe_amount_engine import SafeAmountEngine
from optimizer import PaymentPlanOptimizer
from main import format_amount

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

sample_df = pd.read_csv('dataset/sample_requests.csv')

exact_method_status = 0
exact_all_fields = 0

for req in sample_requests:
    rid = req.request_id
    prof = indexes.get_profile(req.user_id)
    u_events = indexes.get_events_for_user(req.user_id)
    opts = indexes.get_payment_options(rid)
    u_msgs = indexes.get_messages_for_user(req.user_id)
    gt = ground_truths[rid]
    
    cand = optimizer.evaluate_request(req, prof, u_events, opts, u_msgs)
    safe_dec = safe_engine.evaluate_request(req, prof, u_events, u_msgs)
    
    amt_safe_str = format_amount(safe_dec.amount_safe_to_pay)
    if cand.affordability_status == 'not_affordable':
        earliest_date_str = ""
    elif cand.affordability_status == 'affordable_now':
        earliest_date_str = req.request_date
    elif cand.recommended_payment_method == 'partial_payment' and '|' in cand.payment_plan:
        p2 = cand.payment_plan.split('|')[1]
        earliest_date_str = p2.split(':')[0]
    else:
        earliest_date_str = safe_dec.earliest_date_for_full_payment or ""
        
    ms_match = (cand.recommended_payment_method == gt['recommended_payment_method']) and (cand.affordability_status == gt['affordability_status'])
    if ms_match:
        exact_method_status += 1
        
    plan_match = (cand.payment_plan == gt['payment_plan'])
    spend_match = (cand.spending_changes_needed == gt['spending_changes_needed'])
    earliest_match = (earliest_date_str == str(gt['earliest_date_for_full_payment']) if pd.notna(gt['earliest_date_for_full_payment']) else earliest_date_str == "")
    
    all_match = ms_match and plan_match and spend_match and earliest_match
    if all_match:
        exact_all_fields += 1
        
    status_symbol = "OK" if ms_match else "MISMATCH"
    print(f"[{status_symbol}] {rid}: method={cand.recommended_payment_method} (exp: {gt['recommended_payment_method']}), status={cand.affordability_status} (exp: {gt['affordability_status']})")
    if not ms_match or not plan_match or not spend_match:
        print(f"    PLAN: actual='{cand.payment_plan}' | expected='{gt['payment_plan']}'")
        print(f"    SPEND: actual='{cand.spending_changes_needed}' | expected='{gt['spending_changes_needed']}'")
        print(f"    EARLIEST: actual='{earliest_date_str}' | expected='{gt.get('earliest_date_for_full_payment')}'")

print(f"\nTotal Method + Status Matches: {exact_method_status} / {len(sample_requests)}")
print(f"Total All Fields (method, status, plan, spend, earliest) Matches: {exact_all_fields} / {len(sample_requests)}")
