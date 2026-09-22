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

def test_fixes():
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

    matches = 0
    total = len(sample_requests)

    for req in sample_requests:
        rid = req.request_id
        gt = ground_truths[rid]
        prof = indexes.get_profile(req.user_id)
        u_events = indexes.get_events_for_user(req.user_id)
        opts = indexes.payment_options_by_request.get(rid, [])
        u_msgs = indexes.get_messages_for_user(req.user_id)

        cand = optimizer.evaluate_request(req, prof, u_events, opts, u_msgs)

        exp_method = gt.get('recommended_payment_method')
        exp_status = gt.get('affordability_status')

        calc_method = cand.recommended_payment_method
        calc_status = cand.affordability_status

        is_match = (exp_method == calc_method) and (exp_status == calc_status)
        if is_match:
            matches += 1
        else:
            print(f"{rid:<12} | GOT: method={calc_method:<16} status={calc_status:<20} | EXP: method={exp_method:<16} status={exp_status}")

    print(f"\nPhase 4.3 Exact Method + Status Matches: {matches} / {total}")

if __name__ == '__main__':
    test_fixes()
