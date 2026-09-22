"""
Data Loader for Afford IQ On-Device Financial Decision Agent
Loads and parses CSV files into strongly typed Pydantic models.
"""
import os
import pandas as pd
from typing import List, Dict, Any, Optional

try:
    from models import (
        Request,
        FinancialProfile,
        FinancialEvent,
        PaymentOption,
        Message,
        ImageReference,
        ExchangeRate
    )
except ImportError:
    from code.models import (
        Request,
        FinancialProfile,
        FinancialEvent,
        PaymentOption,
        Message,
        ImageReference,
        ExchangeRate
    )


def _safe_str(val: Any) -> Optional[str]:
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip()
    return s if s else None


def _safe_float(val: Any) -> Optional[float]:
    if pd.isna(val) or val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_int(val: Any) -> Optional[int]:
    if pd.isna(val) or val is None:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _safe_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    return s in ('true', '1', 't', 'yes')


def _split_list(val: Any, sep: str = '|') -> List[str]:
    s = _safe_str(val)
    if not s or s == 'none':
        return []
    return [item.strip() for item in s.split(sep) if item.strip()]


class DataLoader:
    def __init__(self, dataset_dir: str):
        self.dataset_dir = dataset_dir

    def load_requests(self, filename: str = "requests.csv") -> List[Request]:
        filepath = os.path.join(self.dataset_dir, filename)
        df = pd.read_csv(filepath)
        expected_cols = {
            'request_id', 'user_id', 'request_date', 'request_type',
            'requested_amount', 'desired_completion_date',
            'allows_partial_payment', 'request_text'
        }
        missing = expected_cols - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns in {filename}: {missing}")

        requests = []
        for _, row in df.iterrows():
            req = Request(
                request_id=str(row['request_id']).strip(),
                user_id=str(row['user_id']).strip(),
                request_date=str(row['request_date']).strip(),
                request_type=str(row['request_type']).strip(),
                requested_amount=float(row['requested_amount']),
                desired_completion_date=str(row['desired_completion_date']).strip(),
                allows_partial_payment=_safe_bool(row['allows_partial_payment']),
                request_text=str(row['request_text']).strip()
            )
            requests.append(req)
        return requests

    def load_sample_requests(self, filename: str = "sample_requests.csv") -> Dict[str, Any]:
        filepath = os.path.join(self.dataset_dir, filename)
        df = pd.read_csv(filepath)
        requests = self.load_requests(filename)
        ground_truths = {}
        for _, row in df.iterrows():
            rid = str(row['request_id']).strip()
            ground_truths[rid] = {
                'amount_safe_to_pay': _safe_float(row['amount_safe_to_pay']),
                'affordability_status': _safe_str(row['affordability_status']),
                'recommended_payment_method': _safe_str(row['recommended_payment_method']),
                'payment_plan': _safe_str(row['payment_plan']),
                'earliest_date_for_full_payment': _safe_str(row['earliest_date_for_full_payment']),
                'spending_changes_needed': _safe_str(row['spending_changes_needed']),
                'decision_explanation': _safe_str(row['decision_explanation'])
            }
        return {'requests': requests, 'ground_truths': ground_truths}

    def load_financial_profiles(self, filename: str = "financial_profiles.csv") -> List[FinancialProfile]:
        filepath = os.path.join(self.dataset_dir, filename)
        df = pd.read_csv(filepath)
        expected_cols = {
            'user_id', 'home_currency', 'current_available_balance',
            'minimum_balance_to_keep', 'financial_priorities',
            'expense_categories_to_protect',
            'expense_categories_user_is_willing_to_reduce',
            'expense_categories_user_is_willing_to_stop',
            'payment_methods_user_will_consider', 'max_installment_months'
        }
        missing = expected_cols - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns in {filename}: {missing}")

        profiles = []
        for _, row in df.iterrows():
            prof = FinancialProfile(
                user_id=str(row['user_id']).strip(),
                home_currency=str(row['home_currency']).strip(),
                current_available_balance=float(row['current_available_balance']),
                minimum_balance_to_keep=float(row['minimum_balance_to_keep']),
                financial_priorities=_split_list(row['financial_priorities']),
                expense_categories_to_protect=_split_list(row['expense_categories_to_protect']),
                expense_categories_user_is_willing_to_reduce=_split_list(row['expense_categories_user_is_willing_to_reduce']),
                expense_categories_user_is_willing_to_stop=_split_list(row['expense_categories_user_is_willing_to_stop']),
                payment_methods_user_will_consider=_split_list(row['payment_methods_user_will_consider']),
                max_installment_months=_safe_float(row['max_installment_months'])
            )
            profiles.append(prof)
        return profiles

    def load_financial_events(self, filename: str = "financial_events.csv") -> List[FinancialEvent]:
        filepath = os.path.join(self.dataset_dir, filename)
        df = pd.read_csv(filepath)
        expected_cols = {
            'event_id', 'user_id', 'event_type', 'description', 'category',
            'direction', 'amount', 'currency', 'event_date', 'settlement_date',
            'status', 'linked_event_id', 'flexibility', 'minimum_allowed_amount'
        }
        missing = expected_cols - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns in {filename}: {missing}")

        events = []
        for _, row in df.iterrows():
            evt = FinancialEvent(
                event_id=str(row['event_id']).strip(),
                user_id=str(row['user_id']).strip(),
                event_type=str(row['event_type']).strip(),
                description=str(row['description']).strip() if pd.notna(row['description']) else "",
                category=str(row['category']).strip(),
                direction=str(row['direction']).strip(),
                amount=_safe_float(row['amount']),  # Preserves None when NaN
                currency=str(row['currency']).strip(),
                event_date=str(row['event_date']).strip(),
                settlement_date=str(row['settlement_date']).strip(),
                status=str(row['status']).strip(),
                linked_event_id=_safe_str(row['linked_event_id']),
                flexibility=str(row['flexibility']).strip(),
                minimum_allowed_amount=_safe_float(row['minimum_allowed_amount'])
            )
            events.append(evt)
        return events

    def load_request_payment_options(self, filename: str = "request_payment_options.csv") -> List[PaymentOption]:
        filepath = os.path.join(self.dataset_dir, filename)
        df = pd.read_csv(filepath)
        expected_cols = {
            'payment_option_id', 'request_id', 'payment_method',
            'payment_amount', 'number_of_payments', 'first_payment_date',
            'payment_frequency_days', 'financing_fee', 'total_payable_amount'
        }
        missing = expected_cols - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns in {filename}: {missing}")

        options = []
        for _, row in df.iterrows():
            opt = PaymentOption(
                payment_option_id=str(row['payment_option_id']).strip(),
                request_id=str(row['request_id']).strip(),
                payment_method=str(row['payment_method']).strip(),
                payment_amount=float(row['payment_amount']),
                number_of_payments=int(row['number_of_payments']),
                first_payment_date=str(row['first_payment_date']).strip(),
                payment_frequency_days=_safe_float(row['payment_frequency_days']),
                financing_fee=float(row['financing_fee']),
                total_payable_amount=float(row['total_payable_amount'])
            )
            options.append(opt)
        return options

    def load_messages(self, filename: str = "messages.csv") -> List[Message]:
        filepath = os.path.join(self.dataset_dir, filename)
        df = pd.read_csv(filepath)
        expected_cols = {
            'message_id', 'user_id', 'request_id', 'related_event_id',
            'sent_at', 'source_type', 'message_text'
        }
        missing = expected_cols - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns in {filename}: {missing}")

        messages = []
        for _, row in df.iterrows():
            msg = Message(
                message_id=str(row['message_id']).strip(),
                user_id=str(row['user_id']).strip(),
                request_id=_safe_str(row['request_id']),
                related_event_id=_safe_str(row['related_event_id']),
                sent_at=str(row['sent_at']).strip(),
                source_type=str(row['source_type']).strip(),
                message_text=str(row['message_text']).strip()
            )
            messages.append(msg)
        return messages

    def load_images(self, filename: str = "images.csv") -> List[ImageReference]:
        filepath = os.path.join(self.dataset_dir, filename)
        df = pd.read_csv(filepath)
        expected_cols = {'image_id', 'user_id', 'request_id', 'related_event_id'}
        missing = expected_cols - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns in {filename}: {missing}")

        images = []
        for _, row in df.iterrows():
            img = ImageReference(
                image_id=str(row['image_id']).strip(),
                user_id=str(row['user_id']).strip(),
                request_id=str(row['request_id']).strip(),
                related_event_id=str(row['related_event_id']).strip()
            )
            images.append(img)
        return images

    def load_exchange_rates(self, filename: str = "exchange_rates.csv") -> List[ExchangeRate]:
        filepath = os.path.join(self.dataset_dir, filename)
        df = pd.read_csv(filepath)
        expected_cols = {'rate_date', 'from_currency', 'to_currency', 'rate'}
        missing = expected_cols - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns in {filename}: {missing}")

        rates = []
        for _, row in df.iterrows():
            rate = ExchangeRate(
                rate_date=str(row['rate_date']).strip(),
                from_currency=str(row['from_currency']).strip(),
                to_currency=str(row['to_currency']).strip(),
                rate=float(row['rate'])
            )
            rates.append(rate)
        return rates
