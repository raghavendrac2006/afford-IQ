"""
Relationship Indexes for HackerRank Orchestrate: Buy or Wait?
Provides fast O(1) lookups for dataset relationships.
"""
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

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


class DatasetIndexes:
    def __init__(
        self,
        profiles: List[FinancialProfile],
        events: List[FinancialEvent],
        payment_options: List[PaymentOption],
        messages: List[Message],
        images: List[ImageReference],
        exchange_rates: List[ExchangeRate]
    ):
        self.profiles_by_user: Dict[str, FinancialProfile] = {p.user_id: p for p in profiles}

        self.events_by_user: Dict[str, List[FinancialEvent]] = defaultdict(list)
        self.events_by_id: Dict[str, FinancialEvent] = {}
        for e in events:
            self.events_by_user[e.user_id].append(e)
            self.events_by_id[e.event_id] = e

        self.messages_by_user: Dict[str, List[Message]] = defaultdict(list)
        self.messages_by_event: Dict[str, List[Message]] = defaultdict(list)
        self.messages_by_request: Dict[str, List[Message]] = defaultdict(list)
        for m in messages:
            self.messages_by_user[m.user_id].append(m)
            if m.related_event_id:
                self.messages_by_event[m.related_event_id].append(m)
            if m.request_id:
                self.messages_by_request[m.request_id].append(m)

        for user_id in self.messages_by_user:
            self.messages_by_user[user_id].sort(key=lambda x: x.sent_at)
        for evt_id in self.messages_by_event:
            self.messages_by_event[evt_id].sort(key=lambda x: x.sent_at)
        for req_id in self.messages_by_request:
            self.messages_by_request[req_id].sort(key=lambda x: x.sent_at)

        self.images_by_event: Dict[str, ImageReference] = {}
        self.images_by_request: Dict[str, List[ImageReference]] = defaultdict(list)
        for img in images:
            self.images_by_event[img.related_event_id] = img
            self.images_by_request[img.request_id].append(img)

        self.payment_options_by_request: Dict[str, List[PaymentOption]] = defaultdict(list)
        for opt in payment_options:
            self.payment_options_by_request[opt.request_id].append(opt)

        self.exchange_rates_by_date_and_currency_pair: Dict[Tuple[str, str, str], float] = {}
        for r in exchange_rates:
            key = (r.rate_date, r.from_currency, r.to_currency)
            self.exchange_rates_by_date_and_currency_pair[key] = r.rate

    def get_profile(self, user_id: str) -> Optional[FinancialProfile]:
        return self.profiles_by_user.get(user_id)

    def get_events_for_user(self, user_id: str) -> List[FinancialEvent]:
        return self.events_by_user.get(user_id, [])

    def get_event(self, event_id: str) -> Optional[FinancialEvent]:
        return self.events_by_id.get(event_id)

    def get_payment_options(self, request_id: str) -> List[PaymentOption]:
        return self.payment_options_by_request.get(request_id, [])

    def get_messages_for_user(self, user_id: str) -> List[Message]:
        return self.messages_by_user.get(user_id, [])

    def get_messages_for_request(self, request_id: str) -> List[Message]:
        return self.messages_by_request.get(request_id, [])

    def get_messages_for_event(self, event_id: str) -> List[Message]:
        return self.messages_by_event.get(event_id, [])

    def get_image_for_event(self, event_id: str) -> Optional[ImageReference]:
        return self.images_by_event.get(event_id)

    def get_exchange_rate(self, rate_date: str, from_curr: str, to_curr: str) -> Optional[float]:
        if from_curr == to_curr:
            return 1.0
        return self.exchange_rates_by_date_and_currency_pair.get((rate_date, from_curr, to_curr))
