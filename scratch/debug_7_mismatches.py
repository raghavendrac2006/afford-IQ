import sys, os
sys.path.insert(0, 'code')
from data_loader import DataLoader
from indexes import DatasetIndexes
from currency import CurrencyConverter
from image_resolver import ImageResolver
from safe_amount_engine import SafeAmountEngine
from optimizer import PaymentPlanOptimizer

dataset_dir = 'dataset'
loader = DataLoader(dataset_dir)
sample_dict = loader.load_sample_requests('sample_requests.csv')
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
optimizer = PaymentPlanOptimizer(cc, ir)

mismatch_ids = ['request_02', 'request_06', 'request_08', 'request_10', 'request_13', 'request_19', 'request_21']

for rid in mismatch_ids:
    req = next(r for r in sample_dict['requests'] if r.request_id == rid)
    prof = indexes.get_profile(req.user_id)
    u_events = indexes.get_events_for_user(req.user_id)
    opts = indexes.get_payment_options(rid)
    u_msgs = indexes.get_messages_for_user(req.user_id)
    gt = ground_truths[rid]
    
    cand = optimizer.evaluate_request(req, prof, u_events, opts, u_msgs)
    
    print('='*80)
    print(f"REQUEST: {rid} (user: {req.user_id}, date: {req.request_date}, amt: {req.requested_amount}, completion: {req.desired_completion_date}, partial: {req.allows_partial_payment})")
    print(f"PROFILE: curr: {prof.home_currency}, avail_bal: {prof.current_available_balance}, min_bal: {prof.minimum_balance_to_keep}, max_inst: {prof.max_installment_months}")
    print(f"GT:   method={gt['recommended_payment_method']}, status={gt['affordability_status']}, plan={gt['payment_plan']}")
    print(f"CAND: method={cand.recommended_payment_method}, status={cand.affordability_status}, plan={cand.payment_plan}, spending={cand.spending_changes_needed}")
