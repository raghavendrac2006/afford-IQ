"""
Recurrence Detection & Spending Classification for HackerRank Orchestrate: Buy or Wait?
Detects recurring income and expense patterns from historical financial events.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter

try:
    from models import FinancialEvent, FinancialProfile
    from event_classifier import EventClassifier
    from image_resolver import ImageResolver
except ImportError:
    from code.models import FinancialEvent, FinancialProfile
    from code.event_classifier import EventClassifier
    from code.image_resolver import ImageResolver


def _add_months(sourcedate: datetime, months: int) -> datetime:
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return datetime(year, month, day)


@dataclass
class RecurringPattern:
    category: str
    event_type: str
    description: str
    currency: str
    direction: str
    frequency_days: int
    last_event_date: str
    next_expected_date: str
    amount: float
    flexibility: str
    minimum_allowed_amount: Optional[float]
    confidence: str
    is_essential: bool


class RecurrenceDetector:
    def __init__(self, image_resolver: Optional[ImageResolver] = None):
        self.classifier = EventClassifier()
        self.image_resolver = image_resolver

    def _get_effective_amount(self, evt: FinancialEvent) -> Optional[float]:
        if evt.amount is not None:
            return evt.amount
        if self.image_resolver:
            res = self.image_resolver.resolve_event_amount(evt)
            if res.get("resolved") and res.get("amount") is not None:
                return res["amount"]
        return None

    def detect_patterns(
        self,
        user_events: List[FinancialEvent],
        profile: FinancialProfile,
        request_date_str: str
    ) -> List[RecurringPattern]:
        req_date = datetime.strptime(request_date_str, "%Y-%m-%d")

        # 1. Filter settled historical events up to request_date
        past_events = []
        employment_ended = False

        for evt in user_events:
            if evt.event_date <= request_date_str:
                cl = self.classifier.classify_event(evt)
                eff_amt = self._get_effective_amount(evt)
                desc_lower = (evt.description or '').lower()

                if 'final' in desc_lower and ('payroll' in desc_lower or 'salary' in desc_lower or 'paycheck' in desc_lower):
                    employment_ended = True

                if cl.category == 'settled_cash' and eff_amt is not None and eff_amt > 0:
                    past_events.append((evt, eff_amt))

        # 2. Group by category and direction
        groups = defaultdict(list)
        for evt, eff_amt in past_events:
            desc_lower = (evt.description or '').lower()
            # Ignore clear one-off items from recurring stream detection
            if any(kw in desc_lower for kw in ('arrears', 'bonus', 'one-off', 'lottery', 'refund', 'severance', 'promotion arrears')):
                continue
            key = (evt.category, evt.direction)
            groups[key].append((evt, eff_amt))

        patterns: List[RecurringPattern] = []

        for (cat, direction), evts_with_amt in groups.items():
            if employment_ended and (cat == 'salary' or direction == 'credit'):
                continue

            evts_with_amt.sort(key=lambda x: x[0].event_date)
            evts = [x[0] for x in evts_with_amt]
            amounts = [x[1] for x in evts_with_amt]
            etype = evts[-1].event_type

            count = len(evts)
            last_evt = evts[-1]
            last_date = datetime.strptime(last_evt.event_date, "%Y-%m-%d")

            # Determine frequency and next expected date
            if count >= 2:
                dates = [datetime.strptime(e.event_date, "%Y-%m-%d") for e in evts]
                intervals = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
                avg_interval = sum(intervals) / len(intervals)

                if 25 <= avg_interval <= 35:
                    freq_days = 30
                    confidence = "high"
                    days_of_month = [d.day for d in dates]
                    most_common_day = Counter(days_of_month).most_common(1)[0][0]

                    # Find next occurrence of most_common_day on or after req_date
                    curr_year = req_date.year
                    curr_month = req_date.month
                    max_d = [31, 29 if curr_year % 4 == 0 and (curr_year % 100 != 0 or curr_year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][curr_month - 1]
                    target_d = min(most_common_day, max_d)
                    cand_date = datetime(curr_year, curr_month, target_d)

                    if cand_date < req_date:
                        cand_date = _add_months(cand_date, 1)
                        max_d2 = [31, 29 if cand_date.year % 4 == 0 and (cand_date.year % 100 != 0 or cand_date.year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][cand_date.month - 1]
                        cand_date = datetime(cand_date.year, cand_date.month, min(most_common_day, max_d2))

                    next_date_str = cand_date.strftime("%Y-%m-%d")
                elif 5 <= avg_interval <= 10:
                    freq_days = 7
                    confidence = "medium"
                    curr_date = last_date + timedelta(days=7)
                    while curr_date <= req_date:
                        curr_date += timedelta(days=7)
                    next_date_str = curr_date.strftime("%Y-%m-%d")
                elif 11 <= avg_interval <= 20:
                    freq_days = 14
                    confidence = "medium"
                    curr_date = last_date + timedelta(days=14)
                    while curr_date <= req_date:
                        curr_date += timedelta(days=14)
                    next_date_str = curr_date.strftime("%Y-%m-%d")
                else:
                    freq_days = 30
                    confidence = "low"
                    curr_date = _add_months(last_date, 1)
                    while curr_date <= req_date:
                        curr_date = _add_months(curr_date, 1)
                    next_date_str = curr_date.strftime("%Y-%m-%d")
            else:
                if cat in ('salary', 'rent', 'housing', 'utilities', 'debt_repayment', 'education', 'insurance') or etype in ('subscription', 'debt_payment'):
                    freq_days = 30
                    confidence = "medium"
                    curr_date = _add_months(last_date, 1)
                    while curr_date <= req_date:
                        curr_date = _add_months(curr_date, 1)
                    next_date_str = curr_date.strftime("%Y-%m-%d")
                else:
                    continue

            pattern_amt = amounts[-1] if amounts else 0.0
            flex = last_evt.flexibility
            protected_cats = profile.expense_categories_to_protect
            is_essential = (flex == 'fixed') or (cat in protected_cats) or (cat in ('rent', 'housing', 'education', 'debt_repayment', 'healthcare', 'insurance', 'utilities', 'salary', 'groceries'))

            pattern = RecurringPattern(
                category=cat,
                event_type=etype,
                description=last_evt.description,
                currency=last_evt.currency,
                direction=last_evt.direction,
                frequency_days=freq_days,
                last_event_date=last_evt.event_date,
                next_expected_date=next_date_str,
                amount=pattern_amt,
                flexibility=flex,
                minimum_allowed_amount=last_evt.minimum_allowed_amount,
                confidence=confidence,
                is_essential=is_essential
            )
            patterns.append(pattern)

        return patterns
