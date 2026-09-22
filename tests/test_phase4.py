"""
Phase 4 Unit Tests for HackerRank Orchestrate: Buy or Wait?
Tests Payment Plan & Spending Change Optimizer: candidate generation,
installment validation, partial payment formatting, spending change search,
plan ranking, affordability status classification, and 90-day safety.
"""
import unittest
import os
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
code_dir = os.path.join(repo_root, "code")
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from data_loader import DataLoader
from indexes import DatasetIndexes
from currency import CurrencyConverter
from image_resolver import ImageResolver
from optimizer import PaymentPlanOptimizer, PlanCandidate


class TestPhase4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset_dir = os.path.join(repo_root, "dataset")
        cls.loader = DataLoader(cls.dataset_dir)

        cls.requests = cls.loader.load_requests("requests.csv")
        cls.sample_dict = cls.loader.load_sample_requests("sample_requests.csv")
        cls.sample_requests = cls.sample_dict['requests']
        cls.ground_truths = cls.sample_dict['ground_truths']
        cls.profiles = cls.loader.load_financial_profiles("financial_profiles.csv")
        cls.events = cls.loader.load_financial_events("financial_events.csv")
        cls.payment_options = cls.loader.load_request_payment_options("request_payment_options.csv")
        cls.messages = cls.loader.load_messages("messages.csv")
        cls.images = cls.loader.load_images("images.csv")
        cls.exchange_rates = cls.loader.load_exchange_rates("exchange_rates.csv")

        cls.indexes = DatasetIndexes(
            cls.profiles, cls.events, cls.payment_options,
            cls.messages, cls.images, cls.exchange_rates
        )
        cls.currency_converter = CurrencyConverter(cls.exchange_rates)
        cls.image_resolver = ImageResolver(cls.dataset_dir, cls.images)
        cls.optimizer = PaymentPlanOptimizer(cls.currency_converter, cls.image_resolver)

    def test_full_payment_affordable_now(self):
        req1 = self.sample_requests[0]  # request_01
        prof1 = self.indexes.get_profile(req1.user_id)
        user_events = self.indexes.get_events_for_user(req1.user_id)
        opts = self.indexes.payment_options_by_request.get(req1.request_id, [])
        user_msgs = self.indexes.get_messages_for_user(req1.user_id)

        candidate = self.optimizer.evaluate_request(req1, prof1, user_events, opts, user_msgs)
        self.assertEqual(candidate.recommended_payment_method, "full_payment")
        self.assertEqual(candidate.affordability_status, "affordable_now")
        self.assertEqual(candidate.spending_changes_needed, "none")
        self.assertTrue(candidate.completes_by_deadline)

    def test_installments_option_validation(self):
        req12 = self.sample_requests[11]  # request_12
        prof12 = self.indexes.get_profile(req12.user_id)
        user_events = self.indexes.get_events_for_user(req12.user_id)
        opts = self.indexes.payment_options_by_request.get(req12.request_id, [])
        user_msgs = self.indexes.get_messages_for_user(req12.user_id)

        self.assertGreater(len(opts), 0)
        candidate = self.optimizer.evaluate_request(req12, prof12, user_events, opts, user_msgs)
        self.assertIn(candidate.recommended_payment_method, ["installments", "full_payment"])
        self.assertIn(candidate.affordability_status, ["affordable_with_plan", "affordable_now"])

    def test_partial_payment_format(self):
        req19 = self.sample_requests[18]  # request_19
        prof19 = self.indexes.get_profile(req19.user_id)
        user_events = self.indexes.get_events_for_user(req19.user_id)
        opts = self.indexes.payment_options_by_request.get(req19.request_id, [])
        user_msgs = self.indexes.get_messages_for_user(req19.user_id)

        candidate = self.optimizer.evaluate_request(req19, prof19, user_events, opts, user_msgs)
        self.assertIsNotNone(candidate.payment_plan)
        if candidate.recommended_payment_method == "partial_payment":
            self.assertIn("|", candidate.payment_plan)
            parts = candidate.payment_plan.split("|")
            self.assertEqual(len(parts), 2)

    def test_not_recommended_unaffordable(self):
        req14 = self.sample_requests[13]  # request_14
        prof14 = self.indexes.get_profile(req14.user_id)
        user_events = self.indexes.get_events_for_user(req14.user_id)
        opts = self.indexes.payment_options_by_request.get(req14.request_id, [])
        user_msgs = self.indexes.get_messages_for_user(req14.user_id)

        candidate = self.optimizer.evaluate_request(req14, prof14, user_events, opts, user_msgs)
        self.assertEqual(candidate.recommended_payment_method, "not_recommended")
        self.assertEqual(candidate.affordability_status, "not_affordable")
        self.assertEqual(candidate.payment_plan, "none")
        self.assertEqual(candidate.spending_changes_needed, "none")

    def test_spending_change_search_authorization(self):
        req21 = self.sample_requests[20]  # request_21
        prof21 = self.indexes.get_profile(req21.user_id)
        user_events = self.indexes.get_events_for_user(req21.user_id)

        applied, changes_str, released = self.optimizer.find_spending_changes(
            prof21, user_events, req21.request_date, needed_amount=50.0
        )
        self.assertIsNotNone(changes_str)
        if applied:
            for ch in applied:
                evt = next(e for e in user_events if e.event_id == ch['event_id'])
                # Verify protected categories are never modified
                self.assertNotIn(evt.category, prof21.expense_categories_to_protect)

    def test_optimizer_robustness_eval_requests(self):
        # Run PaymentPlanOptimizer on first 30 evaluation requests to ensure zero crashes
        for req in self.requests[:30]:
            prof = self.indexes.get_profile(req.user_id)
            user_events = self.indexes.get_events_for_user(req.user_id)
            opts = self.indexes.payment_options_by_request.get(req.request_id, [])
            user_msgs = self.indexes.get_messages_for_user(req.user_id)

            candidate = self.optimizer.evaluate_request(req, prof, user_events, opts, user_msgs)
            self.assertIsNotNone(candidate.recommended_payment_method)
            self.assertIn(candidate.recommended_payment_method, ['full_payment', 'partial_payment', 'installments', 'wait', 'not_recommended'])
            self.assertIn(candidate.affordability_status, ['affordable_now', 'affordable_with_plan', 'affordable_later', 'not_affordable'])
            self.assertIsNotNone(candidate.payment_plan)


    def test_spending_changes_affordable_with_plan_status_mapping(self):
        # Verify that when spending changes are required for full payment, status is affordable_with_plan
        req6 = self.sample_requests[5] # request_06
        prof6 = self.indexes.get_profile(req6.user_id)
        user_events = self.indexes.get_events_for_user(req6.user_id)
        opts = self.indexes.payment_options_by_request.get(req6.request_id, [])
        user_msgs = self.indexes.get_messages_for_user(req6.user_id)

        candidate = self.optimizer.evaluate_request(req6, prof6, user_events, opts, user_msgs)
        self.assertIn(candidate.recommended_payment_method, ["full_payment", "wait"])
        if candidate.spending_changes_needed != "none":
            self.assertEqual(candidate.affordability_status, "affordable_with_plan")

    def test_installment_first_payment_capacity_protection(self):
        # Verify that an installment option is rejected if 1st payment exceeds safe_amt
        req5 = self.sample_requests[4] # request_05
        prof5 = self.indexes.get_profile(req5.user_id)
        user_events = self.indexes.get_events_for_user(req5.user_id)
        opts = self.indexes.payment_options_by_request.get(req5.request_id, [])
        user_msgs = self.indexes.get_messages_for_user(req5.user_id)

        candidate = self.optimizer.evaluate_request(req5, prof5, user_events, opts, user_msgs)
        # Verify invalid / unsafe options are not recommended
        self.assertIn(candidate.recommended_payment_method, ["full_payment", "not_recommended", "wait"])


if __name__ == "__main__":
    unittest.main()
