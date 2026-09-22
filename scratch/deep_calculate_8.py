import os
import sys

repo_root = r"a:\Hackerrank"
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.join(repo_root, "code"))

from data_loader import DataLoader
from indexes import DatasetIndexes
from currency import CurrencyConverter
from image_resolver import ImageResolver
from optimizer import PaymentPlanOptimizer
from safe_amount_engine import SafeAmountEngine

def analyze_8_requests():
    loader = DataLoader(os.path.join(repo_root, "dataset"))
    sample_dict = loader.load_sample_requests("sample_requests.csv")
    sample_requests = sample_dict['requests']
    ground_truths = sample_dict['ground_truths']
    profiles = loader.load_financial_profiles("financial_profiles.csv")
    events = loader.load_financial_events("financial_events.csv")
    payment_options = loader.load_request_payment_options("request_payment_options.csv")
    messages = loader.load_messages("messages.csv")
    images = loader.load_images("images.csv")
    rates = loader.load_exchange_rates("exchange_rates.csv")

    indexes = DatasetIndexes(profiles, events, payment_options, messages, images, rates)
    cc = CurrencyConverter(rates)
    img_res = ImageResolver(os.path.join(repo_root, "dataset"), images)
    engine = SafeAmountEngine(cc, img_res)
    optimizer = PaymentPlanOptimizer(cc, img_res)

    target_rids = ['request_03', 'request_05', 'request_06', 'request_08', 'request_10', 'request_11', 'request_13', 'request_21']

    for rid in target_rids:
        req = [r for r in sample_requests if r.request_id == rid][0]
        gt = ground_truths[rid]
        prof = indexes.get_profile(req.user_id)
        u_events = indexes.get_events_for_user(req.user_id)
        u_msgs = indexes.get_messages_for_user(req.user_id)
        opts = indexes.payment_options_by_request.get(rid, [])

        print("="*90)
        print(f"EVIDENCE ANALYSIS FOR {rid} (User: {req.user_id})")
        print(f"Ground Truth Method: {gt.get('recommended_payment_method')}, Status: {gt.get('affordability_status')}, SafeAmt: {gt.get('amount_safe_to_pay')}, EarliestFullDate: {gt.get('earliest_date_for_full_payment')}")
        print(f"1. Request Date: {req.request_date}")
        print(f"2. Desired Completion Date: {req.desired_completion_date}")
        print(f"3. Requested Amount: {req.requested_amount} {prof.home_currency}")
        print(f"4. Starting Available Balance: {prof.current_available_balance} {prof.home_currency}")
        print(f"5. Minimum Balance: {prof.minimum_balance_to_keep} {prof.home_currency}")

        # Pending debits
        pending_debits = [e for e in u_events if e.event_type in ('debit', 'expense', 'payment', 'transfer_out') and e.status == 'pending']
        print(f"6. Pending Debit Reservations: {[f'{e.event_id}:{e.amount}{e.currency}:{e.event_date}' for e in pending_debits]}")

        # Incomes
        credits = [e for e in u_events if e.direction == 'credit' and e.status in ('settled', 'scheduled', 'confirmed')]
        print(f"7. Credit Events in history/future:")
        for c in credits:
            print(f"   - {c.event_id}: date={c.event_date}, set_date={c.settlement_date}, amt={c.amount} {c.currency}, status={c.status}, cat={c.category}, desc='{c.description}'")

        # Permitted spending changes
        print(f"8. Permitted Spending Changes: reduce={prof.expense_categories_user_is_willing_to_reduce}, stop={prof.expense_categories_user_is_willing_to_stop}, protect={prof.expense_categories_to_protect}")

        # Current Engine Decision
        safe_dec = engine.evaluate_request(req, prof, u_events, u_msgs)
        cand = optimizer.evaluate_request(req, prof, u_events, opts, u_msgs)
        print(f"Engine safe_amount_to_pay: {safe_dec.amount_safe_to_pay}")
        print(f"Engine earliest_full_date: {safe_dec.earliest_date_for_full_payment}")
        print(f"Engine selected candidate: method={cand.recommended_payment_method}, status={cand.affordability_status}, plan={cand.payment_plan}, changes={cand.spending_changes_needed}")

if __name__ == '__main__':
    analyze_8_requests()
