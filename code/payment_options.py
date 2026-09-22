"""
Payment Option Infrastructure for HackerRank Orchestrate: Buy or Wait?
Provides deterministic lookup of payment options by request_id.
"""
from typing import List, Dict
from collections import defaultdict

try:
    from models import PaymentOption
except ImportError:
    from code.models import PaymentOption


class PaymentOptionResolver:
    def __init__(self, payment_options: List[PaymentOption]):
        self.payment_options = payment_options
        self.by_request: Dict[str, List[PaymentOption]] = defaultdict(list)
        for opt in payment_options:
            self.by_request[opt.request_id].append(opt)

    def get_payment_options(self, request_id: str) -> List[PaymentOption]:
        """
        Returns all candidate seller payment options for a given request_id.
        Phase 1: Pure lookup. Does not select or rank options.
        """
        return self.by_request.get(request_id, [])
