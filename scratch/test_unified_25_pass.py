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

from safe_amount_engine import SafeAmountEngine
from optimizer import PaymentPlanOptimizer, format_amount

se = SafeAmountEngine(cc, ir)
opt = PaymentPlanOptimizer(cc, ir)

# Override find_spending_changes to include future candidate events
def find_spending_changes_fixed(profile, u_events, request_date_str, needed_amount):
    stop_cats = set(profile.expense_categories_user_is_willing_to_stop or [])
    reduce_cats = set(profile.expense_categories_user_is_willing_to_reduce or [])
    protect_cats = set(profile.expense_categories_to_protect or [])

    candidate_events = []
    for e in u_events:
        if e.user_id != profile.user_id or e.direction != 'debit' or e.category in protect_cats:
            continue

        amt = e.amount
        if amt is None and ir:
            res = ir.resolve_event_amount(e)
            if res.get("resolved") and res.get("amount") is not None:
                amt = res["amount"]

        if amt is None or amt <= 0:
            continue

        flex = (e.flexibility or '').lower()
        can_stop = (e.category in stop_cats) and ('stop' in flex or flex in ('optional', 'flexible', 'adjustable', 'stoppable'))
        can_reduce = (e.category in reduce_cats) and ('reduc' in flex or flex in ('flexible', 'adjustable')) and (e.minimum_allowed_amount is not None) and (e.minimum_allowed_amount < amt)

        if can_stop or can_reduce:
            candidate_events.append(e)

    if not candidate_events:
        return [], "none", 0.0

    cats_most_recent = {}
    for e in candidate_events:
        cat = e.category
        if cat not in cats_most_recent or e.event_date > cats_most_recent[cat].event_date:
            cats_most_recent[cat] = e

    recent_candidates = list(cats_most_recent.values())
    sub_cats = {'streaming', 'cloud_storage', 'music_subscription', 'delivery_membership', 'software', 'hobbies', 'entertainment'}

    def rank_key(e):
        cat = e.category
        is_stop = (cat in stop_cats)
        is_sub = (cat in sub_cats)
        return (0 if is_stop else 1, 0 if is_sub else 1, e.event_date, e.event_id)

    recent_candidates.sort(key=rank_key)

    applied = []
    change_strs = []
    released_total = 0.0

    for e in recent_candidates:
        amt = e.amount or 0.0
        flex = (e.flexibility or '').lower()
        if e.category in stop_cats and ('stop' in flex or flex in ('optional', 'flexible', 'adjustable', 'stoppable')):
            applied.append({'event_id': e.event_id, 'action': 'stop'})
            change_strs.append(f"stop:{e.event_id}")
            released_total += amt
        elif e.category in reduce_cats and e.minimum_allowed_amount is not None:
            min_amt = e.minimum_allowed_amount
            savings = amt - min_amt
            applied.append({'event_id': e.event_id, 'action': 'reduce', 'new_amount': min_amt})
            change_strs.append(f"reduce_to:{e.event_id}:{format_amount(min_amt)}")
            released_total += savings

        if released_total >= needed_amount - 1e-4:
            break

    if applied:
        return applied, "|".join(change_strs), released_total

    return [], "none", 0.0

opt.find_spending_changes = find_spending_changes_fixed

print("Testing 25 sample evaluation...")
ms_matches = 0
total = len(sample_requests)

for req in sample_requests:
    rid = req.request_id
    prof = indexes.get_profile(req.user_id)
    u_events = indexes.get_events_for_user(req.user_id)
    opts = indexes.get_payment_options(rid)
    u_msgs = indexes.get_messages_for_user(req.user_id)
    gt = ground_truths[rid]
    
    cand = opt.evaluate_request(req, prof, u_events, opts, u_msgs)
    
    exp_m = gt['recommended_payment_method']
    exp_s = gt['affordability_status']
    
    m_ok = (cand.recommended_payment_method == exp_m)
    s_ok = (cand.affordability_status == exp_s)
    
    if m_ok and s_ok:
        ms_matches += 1
        st_icon = "OK"
    else:
        st_icon = "MISMATCH"
        
    print(f"[{st_icon}] {rid}: method={cand.recommended_payment_method} (exp: {exp_m}), status={cand.affordability_status} (exp: {exp_s})")

print(f"\nMethod + Status Matches: {ms_matches} / {total}")
