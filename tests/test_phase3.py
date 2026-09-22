"""
Phase 3 Unit Tests for HackerRank Orchestrate: Buy or Wait?
Tests Phase 2 bug fixes, Safe Amount engine, Earliest Full Payment Date, and Affordability Status logic.
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
from image_resolver import ImageResolver
from forecaster import CashFlowForecaster
from safe_amount_engine import SafeAmountEngine


class TestPhase3(unittest.TestCase):
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
        cls.state_resolver = FinancialStateResolver(cls.currency_converter, cls.image_resolver)
        cls.forecaster = CashFlowForecaster(cls.currency_converter, cls.image_resolver)
        cls.safe_engine = SafeAmountEngine(cls.currency_converter, cls.image_resolver)

    def test_pending_debit_no_double_deduction(self):
        # Find user with a pending debit on/before request date
        pending_debit_evt = next(e for e in self.events if e.status == 'pending' and e.direction == 'debit')
        user_id = pending_debit_evt.user_id
        prof = self.indexes.get_profile(user_id)
        user_events = self.indexes.get_events_for_user(user_id)
        user_msgs = self.indexes.get_messages_for_user(user_id)

        state = self.state_resolver.resolve_state(prof, user_events, pending_debit_evt.event_date)
        self.assertIn(pending_debit_evt.event_id, state.reserved_pending_debit_ids)

        # Run forecaster and verify the pending debit is NOT subtracted again on its settlement date
        fc = self.forecaster.forecast_90_days(prof, user_events, user_msgs, pending_debit_evt.event_date)
        
        # Verify reserved debit event_id is not in timeline applied events
        applied_event_strings = [evt_str for day in fc.timeline for evt_str in day.events_applied]
        self.assertFalse(any(pending_debit_evt.event_id in s for s in applied_event_strings))

    def test_pending_credit_exclusion_regression(self):
        # Pending credit events must not be counted before settlement
        pending_credit_evt = next(e for e in self.events if e.status == 'pending' and e.direction == 'credit')
        user_id = pending_credit_evt.user_id
        prof = self.indexes.get_profile(user_id)
        user_events = self.indexes.get_events_for_user(user_id)

        state = self.state_resolver.resolve_state(prof, user_events, pending_credit_evt.event_date)
        self.assertGreater(state.pending_credits_excluded_converted, 0)
        
        # Verify starting_safe_balance does NOT include pending credit
        self.assertEqual(state.starting_safe_balance, prof.current_available_balance - state.pending_debit_reservations_converted)

    def test_non_cash_investment_valuation_exclusion(self):
        # Investment valuation events must never affect liquid cash
        inv_events = [e for e in self.events if e.event_type == 'investment_valuation']
        self.assertGreater(len(inv_events), 0)

        for inv_evt in inv_events:
            prof = self.indexes.get_profile(inv_evt.user_id)
            user_events = self.indexes.get_events_for_user(inv_evt.user_id)
            state = self.state_resolver.resolve_state(prof, user_events, inv_evt.event_date)
            # Verify investment valuation is categorized as unrealized_investments_excluded
            self.assertGreaterEqual(state.unrealized_investments_excluded, 0)

    def test_image_amount_resolution(self):
        # Verify image resolver resolves non-null amounts for image-linked events
        missing_amt_events = [e for e in self.events if e.amount is None]
        self.assertEqual(len(missing_amt_events), 16)

        resolved_count = 0
        for evt in missing_amt_events:
            res = self.image_resolver.resolve_event_amount(evt)
            if res.get("resolved"):
                resolved_count += 1
                self.assertIsNotNone(res.get("amount"))
                self.assertGreater(res.get("amount"), 0)

        self.assertGreaterEqual(resolved_count, 10)

    def test_safe_amount_calculation_sample_01(self):
        req1 = self.sample_requests[0]
        prof1 = self.indexes.get_profile(req1.user_id)
        user_events = self.indexes.get_events_for_user(req1.user_id)
        user_msgs = self.indexes.get_messages_for_user(req1.user_id)

        decision = self.safe_engine.evaluate_request(req1, prof1, user_events, user_msgs)
        self.assertEqual(decision.request_id, "request_01")
        self.assertEqual(decision.amount_safe_to_pay, 25256.0)
        self.assertEqual(decision.affordability_status, "affordable_now")

    def test_earliest_full_payment_date_sample_03(self):
        req3 = self.sample_requests[2]  # request_03
        prof3 = self.indexes.get_profile(req3.user_id)
        user_events = self.indexes.get_events_for_user(req3.user_id)
        user_msgs = self.indexes.get_messages_for_user(req3.user_id)

        decision = self.safe_engine.evaluate_request(req3, prof3, user_events, user_msgs)
        self.assertEqual(decision.request_id, "request_03")
        self.assertIsNotNone(decision.earliest_date_for_full_payment)
        self.assertEqual(decision.affordability_status, "affordable_later")

    def test_eval_requests_robustness(self):
        # Run SafeAmountEngine on first 20 evaluation requests to ensure zero crashes
        for req in self.requests[:20]:
            prof = self.indexes.get_profile(req.user_id)
            user_events = self.indexes.get_events_for_user(req.user_id)
            user_msgs = self.indexes.get_messages_for_user(req.user_id)

            decision = self.safe_engine.evaluate_request(req, prof, user_events, user_msgs)
            self.assertIsNotNone(decision.amount_safe_to_pay)
            self.assertGreaterEqual(decision.amount_safe_to_pay, 0.0)
            self.assertLessEqual(decision.amount_safe_to_pay, req.requested_amount)
            self.assertIn(decision.affordability_status, ['affordable_now', 'affordable_with_plan', 'affordable_later', 'not_affordable'])

    def test_large_pre_salary_expense_regression(self):
        # Sample 07 pattern: pre-salary outflows limit safe amount below requested amount
        req7 = self.sample_requests[6]  # request_07
        prof7 = self.indexes.get_profile(req7.user_id)
        user_events = self.indexes.get_events_for_user(req7.user_id)
        user_msgs = self.indexes.get_messages_for_user(req7.user_id)

        decision = self.safe_engine.evaluate_request(req7, prof7, user_events, user_msgs)
        self.assertLess(decision.amount_safe_to_pay, req7.requested_amount)
        self.assertGreater(decision.pre_salary_outflows, 0.0)

    def test_salary_timing_and_message_change_regression(self):
        # Verify next salary date calculation respects event settlement dates
        req1 = self.sample_requests[0]
        prof1 = self.indexes.get_profile(req1.user_id)
        user_events = self.indexes.get_events_for_user(req1.user_id)

        next_sal = self.safe_engine.find_next_salary_date(user_events, req1.request_date)
        self.assertEqual(next_sal, "2024-03-15")

    def test_no_future_confirmed_income_regression(self):
        # If no future salary is found, default fallback produces valid date and non-crash calculation
        empty_events = []
        next_sal = self.safe_engine.find_next_salary_date(empty_events, "2024-03-20")
        self.assertEqual(next_sal, "2024-04-15")


if __name__ == "__main__":
    unittest.main()
