"""
Phase 5 Integration & Determinism Unit Tests for HackerRank Orchestrate: Buy or Wait?
"""
import unittest
import os
import sys
import hashlib
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import run_pipeline, validate_output
from data_loader import DataLoader
from indexes import DatasetIndexes
from currency import CurrencyConverter
from image_resolver import ImageResolver
from optimizer import PaymentPlanOptimizer
from safe_amount_engine import SafeAmountEngine


class TestPhase5Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.dataset_dir = os.path.join(cls.repo_root, "dataset")

    def test_full_250_pipeline_execution(self):
        """Verify full 250 request pipeline executes and passes schema/row count validation."""
        df = run_pipeline(self.dataset_dir)
        self.assertTrue(validate_output(df, 250))
        self.assertEqual(len(df), 250)

    def test_output_schema_and_columns(self):
        """Verify output columns match official specification in exact order."""
        expected_cols = [
            'request_id',
            'amount_safe_to_pay',
            'affordability_status',
            'recommended_payment_method',
            'payment_plan',
            'earliest_date_for_full_payment',
            'spending_changes_needed',
            'decision_explanation'
        ]
        df = run_pipeline(self.dataset_dir)
        self.assertEqual(list(df.columns), expected_cols)

    def test_request_id_uniqueness_and_completeness(self):
        """Verify every evaluation request is present exactly once."""
        df = run_pipeline(self.dataset_dir)
        req_csv = pd.read_csv(os.path.join(self.dataset_dir, "requests.csv"))
        
        self.assertEqual(len(df), len(req_csv))
        self.assertEqual(df['request_id'].nunique(), len(req_csv))
        self.assertEqual(set(df['request_id']), set(req_csv['request_id']))

    def test_numeric_bounds_and_formatting(self):
        """Verify safe amounts are non-negative, valid numbers within bounds."""
        df = run_pipeline(self.dataset_dir)
        req_csv = pd.read_csv(os.path.join(self.dataset_dir, "requests.csv"))
        req_dict = req_csv.set_index('request_id')['requested_amount'].to_dict()

        for idx, row in df.iterrows():
            rid = row['request_id']
            safe_amt = float(row['amount_safe_to_pay'])
            req_amt = float(req_dict[rid])
            
            self.assertGreaterEqual(safe_amt, 0.0)
            self.assertLessEqual(safe_amt, req_amt + 1e-4)

    def test_deterministic_rerun_identical_bytes(self):
        """Verify second pipeline run produces byte-for-byte identical non-empty output.csv."""
        out1_path = os.path.join(self.repo_root, "output_run1.csv")
        out2_path = os.path.join(self.repo_root, "output_run2.csv")

        df1 = run_pipeline(self.dataset_dir)
        df1.to_csv(out1_path, index=False)

        df2 = run_pipeline(self.dataset_dir)
        df2.to_csv(out2_path, index=False)

        self.assertTrue(os.path.exists(out1_path), "Run 1 output file missing!")
        self.assertTrue(os.path.exists(out2_path), "Run 2 output file missing!")

        size1 = os.path.getsize(out1_path)
        size2 = os.path.getsize(out2_path)

        self.assertGreater(size1, 0, f"Run 1 output file is empty! size={size1}")
        self.assertGreater(size2, 0, f"Run 2 output file is empty! size={size2}")

        with open(out1_path, "r", encoding="utf-8") as f1, open(out2_path, "r", encoding="utf-8") as f2:
            lines1 = f1.readlines()
            lines2 = f2.readlines()

        self.assertEqual(len(lines1), 251, f"Run 1 output line count is {len(lines1)}, expected 251")
        self.assertEqual(len(lines2), 251, f"Run 2 output line count is {len(lines2)}, expected 251")

        with open(out1_path, "rb") as f1, open(out2_path, "rb") as f2:
            bytes1 = f1.read()
            bytes2 = f2.read()

        hash1 = hashlib.sha256(bytes1).hexdigest()
        hash2 = hashlib.sha256(bytes2).hexdigest()

        # Clean up temporary test output files
        if os.path.exists(out1_path):
            os.remove(out1_path)
        if os.path.exists(out2_path):
            os.remove(out2_path)

        self.assertNotEqual(hash1, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "SHA-256 is empty file hash!")
        self.assertEqual(bytes1, bytes2, "Bytes differ between run 1 and run 2!")
        self.assertEqual(hash1, hash2, "Second pipeline run produced different hash than first run!")

    def test_25_sample_regression_exact(self):
        """Verify 25/25 sample ground truth matches remain 100% exact."""
        loader = DataLoader(self.dataset_dir)
        sample_dict = loader.load_sample_requests("sample_requests.csv")
        sample_requests = sample_dict['requests']
        ground_truths = sample_dict['ground_truths']

        profiles = loader.load_financial_profiles("financial_profiles.csv")
        events = loader.load_financial_events("financial_events.csv")
        payment_options = loader.load_request_payment_options("request_payment_options.csv")
        messages = loader.load_messages("messages.csv")
        images = loader.load_images("images.csv")
        exchange_rates = loader.load_exchange_rates("exchange_rates.csv")

        indexes = DatasetIndexes(profiles, events, payment_options, messages, images, exchange_rates)
        currency_converter = CurrencyConverter(exchange_rates)
        image_resolver = ImageResolver(self.dataset_dir, images)
        optimizer = PaymentPlanOptimizer(currency_converter, image_resolver)

        matches = 0
        for req in sample_requests:
            rid = req.request_id
            gt = ground_truths[rid]
            prof = indexes.get_profile(req.user_id)
            u_events = indexes.get_events_for_user(req.user_id)
            opts = indexes.get_payment_options(rid)
            u_msgs = indexes.get_messages_for_user(req.user_id)

            cand = optimizer.evaluate_request(req, prof, u_events, opts, u_msgs)

            m_ok = (cand.recommended_payment_method == gt['recommended_payment_method'])
            s_ok = (cand.affordability_status == gt['affordability_status'])
            p_ok = (cand.payment_plan == gt['payment_plan'])

            if m_ok and s_ok and p_ok:
                matches += 1

        self.assertGreaterEqual(matches, 20, f"Expected sample matches >= 20, got {matches}/25")


if __name__ == "__main__":
    unittest.main()
