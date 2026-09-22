"""
Phase 1 Unit Tests for HackerRank Orchestrate: Buy or Wait?
Uses Python's standard unittest framework.
"""
import unittest
import os
import sys

# Ensure repo root and code folder are on sys.path
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
code_dir = os.path.join(repo_root, "code")
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from data_loader import DataLoader
from indexes import DatasetIndexes
from validation.data_integrity import DataIntegrityValidator
from event_classifier import EventClassifier, EventClassification
from currency import CurrencyConverter
from image_resolver import ImageResolver
from message_resolver import MessageResolver
from payment_options import PaymentOptionResolver


class TestPhase1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset_dir = os.path.join(repo_root, "dataset")
        cls.loader = DataLoader(cls.dataset_dir)

        # Load datasets
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

        # Build indexes and components
        cls.indexes = DatasetIndexes(
            cls.profiles, cls.events, cls.payment_options,
            cls.messages, cls.images, cls.exchange_rates
        )
        cls.validator = DataIntegrityValidator(
            cls.dataset_dir, cls.requests, cls.profiles, cls.events,
            cls.payment_options, cls.messages, cls.images, cls.exchange_rates,
            sample_requests=cls.sample_requests
        )
        cls.currency_converter = CurrencyConverter(cls.exchange_rates)
        cls.image_resolver = ImageResolver(cls.dataset_dir, cls.images)
        cls.message_resolver = MessageResolver(cls.messages)
        cls.payment_resolver = PaymentOptionResolver(cls.payment_options)

    def test_csv_loading_counts(self):
        self.assertEqual(len(self.requests), 250)
        self.assertEqual(len(self.sample_requests), 25)
        self.assertEqual(len(self.profiles), 275)
        self.assertEqual(len(self.events), 25342)
        self.assertEqual(len(self.payment_options), 790)
        self.assertEqual(len(self.messages), 215)
        self.assertEqual(len(self.images), 16)
        self.assertEqual(len(self.exchange_rates), 134)

    def test_data_integrity_validation(self):
        errors, warnings = self.validator.validate_all()
        self.assertEqual(len(errors), 0, f"Integrity errors found: {errors}")

    def test_relationship_indexing(self):
        p1 = self.indexes.get_profile("user_01")
        self.assertIsNotNone(p1)
        self.assertEqual(p1.home_currency, "ZAR")

        user_events = self.indexes.get_events_for_user("user_01")
        self.assertGreater(len(user_events), 0)

        opts = self.indexes.get_payment_options("request_01")
        self.assertGreater(len(opts), 0)

    def test_event_classification(self):
        classifier = EventClassifier()

        settled_evt = next(e for e in self.events if e.status == 'settled' and e.direction == 'debit')
        pending_debit = next(e for e in self.events if e.status == 'pending' and e.direction == 'debit')
        unrealized_evt = next(e for e in self.events if e.status == 'unrealized' or e.direction == 'non_cash')
        cancelled_evt = next(e for e in self.events if e.status == 'cancelled')

        cl_settled = classifier.classify_event(settled_evt)
        self.assertEqual(cl_settled.category, 'settled_cash')
        self.assertTrue(cl_settled.is_cash_flow_effective)

        cl_pending_debit = classifier.classify_event(pending_debit)
        self.assertEqual(cl_pending_debit.category, 'pending_debit_reservation')
        self.assertTrue(cl_pending_debit.is_cash_flow_effective)

        cl_unrealized = classifier.classify_event(unrealized_evt)
        self.assertEqual(cl_unrealized.category, 'unrealized_non_cash')
        self.assertFalse(cl_unrealized.is_cash_flow_effective)

        cl_cancelled = classifier.classify_event(cancelled_evt)
        self.assertEqual(cl_cancelled.category, 'cancelled')
        self.assertFalse(cl_cancelled.is_cash_flow_effective)

    def test_currency_conversion(self):
        self.assertEqual(self.currency_converter.convert(100.0, "EUR", "EUR", "2023-10-15"), 100.0)

        rate = self.currency_converter.get_rate("2023-10-15", "EUR", "ZAR")
        self.assertEqual(rate, 20.0)
        converted = self.currency_converter.convert(10.0, "EUR", "ZAR", "2023-10-15")
        self.assertEqual(converted, 200.0)

    def test_image_infrastructure(self):
        all_exist, missing = self.image_resolver.verify_all_images_exist()
        self.assertTrue(all_exist, f"Missing image files: {missing}")

        img1 = self.image_resolver.by_image_id.get("image_01")
        self.assertIsNotNone(img1)
        self.assertEqual(img1.related_event_id, "event_253")

        evt_253 = self.indexes.get_event("event_253")
        self.assertIsNotNone(evt_253)
        self.assertIsNone(evt_253.amount)

        res = self.image_resolver.resolve_event_amount(evt_253)
        self.assertIn(res['source'], ['linked_image', 'ocr_image'])
        self.assertEqual(res['image_id'], 'image_01')

    def test_message_infrastructure(self):
        u2_msgs = self.message_resolver.get_messages_for_user("user_02")
        self.assertGreater(len(u2_msgs), 0)

        dates = [m.sent_at for m in u2_msgs]
        self.assertEqual(dates, sorted(dates))

        facts = self.message_resolver.extract_financial_facts_only(u2_msgs[0])
        self.assertTrue(facts['untrusted'])

    def test_payment_option_lookup(self):
        opts = self.payment_resolver.get_payment_options("request_01")
        self.assertGreater(len(opts), 0)
        for opt in opts:
            self.assertEqual(opt.request_id, "request_01")
            self.assertGreater(opt.number_of_payments, 0)
            self.assertGreater(opt.total_payable_amount, 0)

    def test_all_25_sample_requests_loadable(self):
        self.assertEqual(len(self.sample_requests), 25)
        for req in self.sample_requests:
            prof = self.indexes.get_profile(req.user_id)
            self.assertIsNotNone(prof, f"Profile missing for sample user {req.user_id}")

    def test_all_250_eval_requests_loadable(self):
        self.assertEqual(len(self.requests), 250)
        for req in self.requests:
            prof = self.indexes.get_profile(req.user_id)
            self.assertIsNotNone(prof, f"Profile missing for eval user {req.user_id}")


if __name__ == "__main__":
    unittest.main()
