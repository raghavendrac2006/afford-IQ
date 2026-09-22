"""
Dataset Integrity Validator for HackerRank Orchestrate: Buy or Wait?
Verifies data integrity, uniqueness, foreign keys, dates, and media files.
"""
import os
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

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

VALID_STATUSES = {'settled', 'pending', 'scheduled', 'cancelled', 'failed', 'unrealized'}
VALID_DIRECTIONS = {'debit', 'credit', 'non_cash'}
VALID_FLEXIBILITIES = {'fixed', 'reducible', 'stoppable', 'reducible_or_stoppable'}
VALID_CURRENCIES = {'INR', 'EUR', 'IDR', 'ZAR', 'USD'}


def _parse_date(date_str: Optional[str]) -> bool:
    if not date_str or date_str.lower() in ('nan', 'none', 'null'):
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


class DataIntegrityValidator:
    def __init__(
        self,
        dataset_dir: str,
        requests: List[Request],
        profiles: List[FinancialProfile],
        events: List[FinancialEvent],
        payment_options: List[PaymentOption],
        messages: List[Message],
        images: List[ImageReference],
        exchange_rates: List[ExchangeRate],
        sample_requests: Optional[List[Request]] = None
    ):
        self.dataset_dir = dataset_dir
        self.requests = requests
        self.sample_requests = sample_requests or []
        self.profiles = profiles
        self.events = events
        self.payment_options = payment_options
        self.messages = messages
        self.images = images
        self.exchange_rates = exchange_rates

        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all(self) -> Tuple[List[str], List[str]]:
        self.errors.clear()
        self.warnings.clear()

        user_ids = {p.user_id for p in self.profiles}
        all_requests = self.requests + self.sample_requests
        request_ids = {r.request_id for r in all_requests}
        event_ids = {e.event_id for e in self.events}

        # 1. Validate Profiles
        profile_ids = set()
        for p in self.profiles:
            if p.user_id in profile_ids:
                self.errors.append(f"Duplicate user_id in profiles: {p.user_id}")
            profile_ids.add(p.user_id)
            if p.home_currency not in VALID_CURRENCIES:
                self.errors.append(f"Invalid home_currency in profile for {p.user_id}: {p.home_currency}")
            if p.minimum_balance_to_keep < 0:
                self.errors.append(f"Negative minimum_balance_to_keep for {p.user_id}: {p.minimum_balance_to_keep}")

        # 2. Validate Requests
        req_id_set = set()
        for r in all_requests:
            if r.request_id in req_id_set:
                self.errors.append(f"Duplicate request_id in requests: {r.request_id}")
            req_id_set.add(r.request_id)

            if r.user_id not in user_ids:
                self.errors.append(f"Request {r.request_id} references missing user_id: {r.user_id}")

            if r.requested_amount <= 0:
                self.errors.append(f"Request {r.request_id} has invalid requested_amount: {r.requested_amount}")

            if not _parse_date(r.request_date):
                self.errors.append(f"Request {r.request_id} has invalid request_date: {r.request_date}")

            if not _parse_date(r.desired_completion_date):
                self.errors.append(f"Request {r.request_id} has invalid desired_completion_date: {r.desired_completion_date}")

        # 3. Validate Financial Events
        evt_id_set = set()
        for e in self.events:
            if e.event_id in evt_id_set:
                self.errors.append(f"Duplicate event_id in financial_events: {e.event_id}")
            evt_id_set.add(e.event_id)

            if e.user_id not in user_ids:
                self.errors.append(f"Event {e.event_id} references missing user_id: {e.user_id}")

            if e.linked_event_id and e.linked_event_id not in event_ids:
                self.errors.append(f"Event {e.event_id} references missing linked_event_id: {e.linked_event_id}")

            if not _parse_date(e.event_date):
                self.errors.append(f"Event {e.event_id} has invalid event_date: {e.event_date}")

            # Note: settlement_date may be blank/nan for unrealized non-cash investment valuations
            if e.status != 'unrealized' and e.direction != 'non_cash':
                if not _parse_date(e.settlement_date):
                    self.errors.append(f"Event {e.event_id} has invalid settlement_date: {e.settlement_date}")

            if e.status not in VALID_STATUSES:
                self.errors.append(f"Event {e.event_id} has unknown status: {e.status}")

            if e.direction not in VALID_DIRECTIONS:
                self.errors.append(f"Event {e.event_id} has unknown direction: {e.direction}")

            if e.flexibility not in VALID_FLEXIBILITIES:
                self.errors.append(f"Event {e.event_id} has unknown flexibility: {e.flexibility}")

            if e.currency not in VALID_CURRENCIES:
                self.errors.append(f"Event {e.event_id} has unknown currency: {e.currency}")

        # 4. Validate Payment Options
        opt_id_set = set()
        for opt in self.payment_options:
            if opt.payment_option_id in opt_id_set:
                self.errors.append(f"Duplicate payment_option_id: {opt.payment_option_id}")
            opt_id_set.add(opt.payment_option_id)

            if opt.request_id not in request_ids:
                self.errors.append(f"Payment option {opt.payment_option_id} references missing request_id: {opt.request_id}")

            if opt.number_of_payments < 1:
                self.errors.append(f"Payment option {opt.payment_option_id} has invalid number_of_payments: {opt.number_of_payments}")

            if not _parse_date(opt.first_payment_date):
                self.errors.append(f"Payment option {opt.payment_option_id} has invalid first_payment_date: {opt.first_payment_date}")

        # 5. Validate Messages
        msg_id_set = set()
        for m in self.messages:
            if m.message_id in msg_id_set:
                self.errors.append(f"Duplicate message_id: {m.message_id}")
            msg_id_set.add(m.message_id)

            if m.user_id not in user_ids:
                self.errors.append(f"Message {m.message_id} references missing user_id: {m.user_id}")

            if m.request_id and m.request_id not in request_ids:
                self.errors.append(f"Message {m.message_id} references missing request_id: {m.request_id}")

            if m.related_event_id and m.related_event_id not in event_ids:
                self.errors.append(f"Message {m.message_id} references missing related_event_id: {m.related_event_id}")

        # 6. Validate Images & Disk Files
        img_id_set = set()
        images_dir = os.path.join(self.dataset_dir, "media", "images")
        for img in self.images:
            if img.image_id in img_id_set:
                self.errors.append(f"Duplicate image_id: {img.image_id}")
            img_id_set.add(img.image_id)

            if img.related_event_id not in event_ids:
                self.errors.append(f"Image {img.image_id} references missing related_event_id: {img.related_event_id}")

            if img.request_id not in request_ids:
                self.errors.append(f"Image {img.image_id} references missing request_id: {img.request_id}")

            img_file_path = os.path.join(images_dir, f"{img.image_id}.png")
            if not os.path.isfile(img_file_path):
                self.errors.append(f"Image file missing on disk: {img_file_path}")

        # 7. Validate Exchange Rates
        for r in self.exchange_rates:
            if not _parse_date(r.rate_date):
                self.errors.append(f"Exchange rate has invalid date: {r.rate_date}")
            if r.from_currency not in VALID_CURRENCIES:
                self.errors.append(f"Exchange rate has invalid from_currency: {r.from_currency}")
            if r.to_currency not in VALID_CURRENCIES:
                self.errors.append(f"Exchange rate has invalid to_currency: {r.to_currency}")
            if r.rate <= 0:
                self.errors.append(f"Exchange rate has non-positive rate: {r.rate}")

        return self.errors, self.warnings
