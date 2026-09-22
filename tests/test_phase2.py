"""
Phase 2 Unit Tests for HackerRank Orchestrate: Buy or Wait?
Tests Financial State, Recurrence Detection, Message Fact Extraction, and 90-Day Cash Flow Forecasting.
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
from financial_state import FinancialStateResolver
from recurrence import RecurrenceDetector
from message_fact_extractor import MessageFactExtractor
from forecaster import CashFlowForecaster


class TestPhase2(unittest.TestCase):
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
        cls.state_resolver = FinancialStateResolver(cls.currency_converter)
        cls.recurrence_detector = RecurrenceDetector()
        cls.fact_extractor = MessageFactExtractor()
        cls.forecaster = CashFlowForecaster(cls.currency_converter)

    def test_financial_state_reconstruction(self):
        req1 = self.sample_requests[0]
        prof1 = self.indexes.get_profile(req1.user_id)
        user_events = self.indexes.get_events_for_user(req1.user_id)

        state = self.state_resolver.resolve_state(prof1, user_events, req1.request_date)
        self.assertEqual(state.user_id, "user_01")
        self.assertEqual(state.home_currency, "ZAR")
        self.assertGreater(state.starting_safe_balance, 0)
        self.assertEqual(state.minimum_balance_to_keep, 18000.0)

    def test_pending_debit_vs_credit(self):
        # Find user with pending debit and user with pending credit
        pending_debit_evt = next(e for e in self.events if e.status == 'pending' and e.direction == 'debit')
        prof_pd = self.indexes.get_profile(pending_debit_evt.user_id)
        events_pd = self.indexes.get_events_for_user(pending_debit_evt.user_id)

        state_pd = self.state_resolver.resolve_state(prof_pd, events_pd, pending_debit_evt.event_date)
        self.assertGreater(state_pd.pending_debit_reservations_converted, 0)

        pending_credit_evt = next(e for e in self.events if e.status == 'pending' and e.direction == 'credit')
        prof_pc = self.indexes.get_profile(pending_credit_evt.user_id)
        events_pc = self.indexes.get_events_for_user(pending_credit_evt.user_id)

        state_pc = self.state_resolver.resolve_state(prof_pc, events_pc, pending_credit_evt.event_date)
        self.assertGreater(state_pc.pending_credits_excluded_converted, 0)

    def test_recurrence_detection(self):
        req1 = self.sample_requests[0]
        prof1 = self.indexes.get_profile(req1.user_id)
        user_events = self.indexes.get_events_for_user(req1.user_id)

        patterns = self.recurrence_detector.detect_patterns(user_events, prof1, req1.request_date)
        self.assertGreater(len(patterns), 0)

        # Confirm essential vs flexible classification
        categories = [p.category for p in patterns]
        self.assertIn("rent", categories)

        rent_pattern = next(p for p in patterns if p.category == "rent")
        self.assertTrue(rent_pattern.is_essential)
        self.assertEqual(rent_pattern.flexibility, "fixed")

    def test_message_fact_extraction_salary(self):
        # Test user_02 salary increase message (IDR 42,750,000)
        u2_msgs = self.indexes.get_messages_for_user("user_02")
        facts = self.fact_extractor.extract_facts(u2_msgs, "2025-08-05")

        sal_facts = [f for f in facts if f.fact_type == 'salary_update']
        self.assertGreater(len(sal_facts), 0)
        self.assertEqual(sal_facts[0].new_amount, 42750000.0)
        self.assertEqual(sal_facts[0].currency, "IDR")

    def test_90_day_forecasting_sample_01(self):
        req1 = self.sample_requests[0]
        prof1 = self.indexes.get_profile(req1.user_id)
        user_events = self.indexes.get_events_for_user(req1.user_id)
        user_msgs = self.indexes.get_messages_for_user(req1.user_id)

        res = self.forecaster.forecast_90_days(prof1, user_events, user_msgs, req1.request_date)
        self.assertEqual(len(res.daily_balances), 91)  # Day 0 to Day 90 inclusive
        self.assertGreater(res.minimum_projected_balance, prof1.minimum_balance_to_keep)

    def test_forecasting_across_all_25_samples(self):
        for req in self.sample_requests:
            prof = self.indexes.get_profile(req.user_id)
            user_events = self.indexes.get_events_for_user(req.user_id)
            user_msgs = self.indexes.get_messages_for_user(req.user_id)

            res = self.forecaster.forecast_90_days(prof, user_events, user_msgs, req.request_date)
            self.assertEqual(len(res.daily_balances), 91)
            self.assertIsNotNone(res.minimum_projected_balance)
            self.assertIsNotNone(res.minimum_projected_date)

    def test_forecasting_eval_requests(self):
        # Sample test 10 eval requests to verify robustness
        for req in self.requests[:10]:
            prof = self.indexes.get_profile(req.user_id)
            user_events = self.indexes.get_events_for_user(req.user_id)
            user_msgs = self.indexes.get_messages_for_user(req.user_id)

            res = self.forecaster.forecast_90_days(prof, user_events, user_msgs, req.request_date)
            self.assertEqual(len(res.daily_balances), 91)


if __name__ == "__main__":
    unittest.main()
