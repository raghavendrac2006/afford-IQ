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

def trace():
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
    optimizer = PaymentPlanOptimizer(cc, img_res)

    target_rids = ['request_03', 'request_05', 'request_06', 'request_08', 'request_10', 'request_11', 'request_13', 'request_21']

    for req in sample_requests:
        if req.request_id not in target_rids:
            continue
        rid = req.request_id
        gt = ground_truths[rid]
        prof = indexes.get_profile(req.user_id)
        u_events = indexes.get_events_for_user(req.user_id)
        opts = indexes.payment_options_by_request.get(rid, [])
        u_msgs = indexes.get_messages_for_user(req.user_id)

        print("\n" + "="*90)
        exp_m = gt.get('recommended_payment_method')
        exp_s = gt.get('affordability_status')
        print(f"REQUEST ID: {rid} | User: {req.user_id} | GROUND TRUTH -> Method: {exp_m}, Status: {exp_s}")
        print(f"1. request_date: {req.request_date}")
        print(f"2. desired_completion_date: {req.desired_completion_date}")
        print(f"3. requested_amount: {req.requested_amount} {prof.home_currency}")
        print(f"4. current available balance: {prof.current_available_balance} {prof.home_currency}")
        print(f"5. minimum_balance_to_keep: {prof.minimum_balance_to_keep} {prof.home_currency}")
        
        # Pending/scheduled debits
        p_debits = [e for e in u_events if e.event_type in ('debit', 'expense', 'payment', 'transfer_out') and e.status in ('pending', 'scheduled')]
        print("6. pending/scheduled debits:")
        if not p_debits:
            print("   None")
        for pd in p_debits:
            print(f"   - {pd.event_id}: date={pd.event_date}, amount={pd.amount} {pd.currency}, status={pd.status}, category={pd.category}, flex={pd.flexibility}")

        # Recurring streams
        print("7. recurring debit streams projected during horizon:")
        patterns = optimizer.safe_engine.recurrence_detector.detect_patterns(u_events, prof, req.request_date)
        for pat in patterns:
            if pat.direction == 'debit':
                print(f"   - Stream cat={pat.category}, flex={pat.flexibility}, amount={pat.amount} {pat.currency}, freq_days={pat.frequency_days}, next_date={pat.next_expected_date}")

        # Confirmed future income
        incomes = [e for e in u_events if e.event_type in ('credit', 'income', 'salary', 'transfer_in') and e.status in ('settled', 'scheduled', 'confirmed')]
        print("8. confirmed future income:")
        for inc in incomes:
            s_date = inc.settlement_date if inc.settlement_date else inc.event_date
            print(f"   - {inc.event_id}: date={inc.event_date}, settlement_date={s_date}, amount={inc.amount} {inc.currency}, status={inc.status}, cat={inc.category}")

        # Spending changes permitted
        print("9. spending changes explicitly permitted:")
        print(f"   - reduce: {prof.expense_categories_user_is_willing_to_reduce}")
        print(f"   - stop: {prof.expense_categories_user_is_willing_to_stop}")
        print(f"   - protect: {prof.expense_categories_to_protect}")

        safe_dec = optimizer.safe_engine.evaluate_request(req, prof, u_events, u_msgs)
        print(f"10. Phase 3 amount_safe_to_pay: {safe_dec.amount_safe_to_pay}")
        print(f"11. Phase 3 earliest_date_for_full_payment: {safe_dec.earliest_date_for_full_payment}")

        # Optimizer candidate selection
        cand = optimizer.evaluate_request(req, prof, u_events, opts, u_msgs)
        print("12. optimizer candidates inspection:")
        print(f"   - Selected Candidate: method={cand.recommended_payment_method}, status={cand.affordability_status}, plan={cand.payment_plan}, completion={cand.completion_date}, changes={cand.spending_changes_needed}")
        print(f"13. Final selected candidate: method={cand.recommended_payment_method}, status={cand.affordability_status}")

if __name__ == '__main__':
    trace()
