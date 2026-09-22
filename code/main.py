"""
Main Production Entry Point for HackerRank Orchestrate: Buy or Wait?
Generates dataset/output.csv and output.csv for all 250 evaluation requests.
"""
import sys
import os
import pandas as pd
from typing import Dict, List, Any

# Ensure local code directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_loader import DataLoader
from indexes import DatasetIndexes
from currency import CurrencyConverter
from image_resolver import ImageResolver
from optimizer import PaymentPlanOptimizer
from safe_amount_engine import SafeAmountEngine


def format_amount(amt: float) -> str:
    """Format monetary amount: integer if whole number, else 2 decimal places."""
    if abs(amt - round(amt)) < 1e-4:
        return str(int(round(amt)))
    return f"{amt:.2f}"


def run_pipeline(dataset_dir: str = "dataset") -> pd.DataFrame:
    """Runs full pipeline for all requests in dataset/requests.csv and returns DataFrame."""
    loader = DataLoader(dataset_dir)
    
    profiles = loader.load_financial_profiles("financial_profiles.csv")
    events = loader.load_financial_events("financial_events.csv")
    payment_options = loader.load_request_payment_options("request_payment_options.csv")
    messages = loader.load_messages("messages.csv")
    images = loader.load_images("images.csv")
    exchange_rates = loader.load_exchange_rates("exchange_rates.csv")
    requests = loader.load_requests("requests.csv")
    
    indexes = DatasetIndexes(
        profiles, events, payment_options,
        messages, images, exchange_rates
    )
    currency_converter = CurrencyConverter(exchange_rates)
    image_resolver = ImageResolver(dataset_dir, images)
    
    safe_engine = SafeAmountEngine(currency_converter, image_resolver)
    optimizer = PaymentPlanOptimizer(currency_converter, image_resolver)
    
    output_rows = []
    
    for req in requests:
        rid = req.request_id
        prof = indexes.get_profile(req.user_id)
        u_events = indexes.get_events_for_user(req.user_id)
        opts = indexes.get_payment_options(rid)
        u_msgs = indexes.get_messages_for_user(req.user_id)
        
        cand = optimizer.evaluate_request(req, prof, u_events, opts, u_msgs)
        safe_dec = safe_engine.evaluate_request(req, prof, u_events, u_msgs)
        
        amt_safe_formatted = format_amount(safe_dec.amount_safe_to_pay)
        
        # Earliest date for full payment logic
        if cand.affordability_status == 'not_affordable':
            earliest_date_str = ""
        elif cand.affordability_status == 'affordable_now':
            earliest_date_str = req.request_date
        elif cand.recommended_payment_method == 'partial_payment' and '|' in cand.payment_plan:
            p2 = cand.payment_plan.split('|')[1]
            earliest_date_str = p2.split(':')[0]
        else:
            earliest_date_str = safe_dec.earliest_date_for_full_payment or ""
            
        row = {
            'request_id': rid,
            'amount_safe_to_pay': amt_safe_formatted,
            'affordability_status': cand.affordability_status,
            'recommended_payment_method': cand.recommended_payment_method,
            'payment_plan': cand.payment_plan,
            'earliest_date_for_full_payment': earliest_date_str,
            'spending_changes_needed': cand.spending_changes_needed,
            'decision_explanation': cand.explanation
        }
        output_rows.append(row)
        
    cols = [
        'request_id',
        'amount_safe_to_pay',
        'affordability_status',
        'recommended_payment_method',
        'payment_plan',
        'earliest_date_for_full_payment',
        'spending_changes_needed',
        'decision_explanation'
    ]
    
    df = pd.DataFrame(output_rows)[cols]
    return df


def validate_output(df: pd.DataFrame, expected_count: int = 250) -> bool:
    """Strictly validates generated output DataFrame according to challenge contract."""
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
    
    assert list(df.columns) == expected_cols, f"Column mismatch: {df.columns.tolist()}"
    assert len(df) == expected_count, f"Row count mismatch: expected {expected_count}, got {len(df)}"
    assert df['request_id'].nunique() == expected_count, "Duplicate request_id found!"
    
    valid_statuses = {'affordable_now', 'affordable_with_plan', 'affordable_later', 'not_affordable'}
    valid_methods = {'full_payment', 'partial_payment', 'installments', 'wait', 'not_recommended'}
    
    for idx, row in df.iterrows():
        assert row['affordability_status'] in valid_statuses, f"Invalid status: {row['affordability_status']} in {row['request_id']}"
        assert row['recommended_payment_method'] in valid_methods, f"Invalid method: {row['recommended_payment_method']} in {row['request_id']}"
        
        safe_val = float(row['amount_safe_to_pay'])
        assert safe_val >= 0, f"Negative safe amount in {row['request_id']}"
        
        if row['affordability_status'] == 'not_affordable':
            assert row['recommended_payment_method'] == 'not_recommended', f"Mismatched method for not_affordable in {row['request_id']}"
            assert row['payment_plan'] == 'none', f"Non-none plan for not_affordable in {row['request_id']}"
            assert row['spending_changes_needed'] == 'none', f"Non-none changes for not_affordable in {row['request_id']}"
            
    print(f"Output validation PASSED: {len(df)} rows verified clean!")
    return True


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dataset_dir = os.path.join(repo_root, "dataset")
    
    print(f"Executing Buy or Wait? financial decision pipeline...")
    df = run_pipeline(dataset_dir)
    validate_output(df, len(df))
    
    # Save to dataset/output.csv and root output.csv
    dataset_out_path = os.path.join(dataset_dir, "output.csv")
    root_out_path = os.path.join(repo_root, "output.csv")
    
    df.to_csv(dataset_out_path, index=False)
    df.to_csv(root_out_path, index=False)
    
    print(f"Successfully generated {dataset_out_path}")
    print(f"Successfully generated {root_out_path}")


if __name__ == "__main__":
    main()
