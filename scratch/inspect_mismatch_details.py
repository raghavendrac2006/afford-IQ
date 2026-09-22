import sys, os
sys.path.insert(0, 'code')
import pandas as pd
from data_loader import DataLoader
from indexes import DatasetIndexes

loader = DataLoader('dataset')
profiles = loader.load_financial_profiles('financial_profiles.csv')
events = loader.load_financial_events('financial_events.csv')
payment_options = loader.load_request_payment_options('request_payment_options.csv')
messages = loader.load_messages('messages.csv')
images = loader.load_images('images.csv')
exchange_rates = loader.load_exchange_rates('exchange_rates.csv')
sample_requests = loader.load_requests('sample_requests.csv')

indexes = DatasetIndexes(profiles, events, payment_options, messages, images, exchange_rates)

def inspect_req(rid):
    req = next(r for r in sample_requests if r.request_id == rid)
    prof = indexes.get_profile(req.user_id)
    u_events = indexes.get_events_for_user(req.user_id)
    u_msgs = indexes.get_messages_for_user(req.user_id)
    
    print('='*80)
    print(f"ID: {rid} | User: {req.user_id} | Req Date: {req.request_date} | Amt: {req.requested_amount} | Completion: {req.desired_completion_date} | Partial: {req.allows_partial_payment}")
    print(f"Profile: curr={prof.home_currency}, avail_bal={prof.current_available_balance}, min_bal={prof.minimum_balance_to_keep}, max_inst={prof.max_installment_months}, protect={prof.expense_categories_to_protect}, stop={prof.expense_categories_user_is_willing_to_stop}, reduce={prof.expense_categories_user_is_willing_to_reduce}")
    print("User Events:")
    for e in u_events:
        print(f"  {e.event_id}: date={e.event_date}, cat={e.category}, type={e.event_type}, dir={e.direction}, amt={e.amount} {e.currency}, status={e.status}, flex={e.flexibility}, min_allowed={e.minimum_allowed_amount}")
    print("User Messages:")
    for m in u_msgs:
        print(f"  {m.message_id}: date={m.sent_at}, text='{m.message_text}'")

for rid in ['request_06', 'request_10', 'request_11', 'request_13', 'request_19', 'request_21']:
    inspect_req(rid)
