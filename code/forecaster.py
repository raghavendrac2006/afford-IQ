"""
Cash Flow Forecaster for Afford IQ On-Device Financial Decision Agent
Projects conservative 90-day daily cash balance timelines with pre-salary troughs.
"""
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime, timedelta

try:
    from models import FinancialProfile, FinancialEvent, Message
    from financial_state import FinancialStateResolver, UserFinancialState
    from recurrence import RecurrenceDetector, RecurringPattern
    from message_fact_extractor import MessageFactExtractor, MessageFinancialFact
    from currency import CurrencyConverter
    from event_classifier import EventClassifier
    from image_resolver import ImageResolver
except ImportError:
    from code.models import FinancialProfile, FinancialEvent, Message
    from code.financial_state import FinancialStateResolver, UserFinancialState
    from code.recurrence import RecurrenceDetector, RecurringPattern
    from code.message_fact_extractor import MessageFactExtractor, MessageFinancialFact
    from code.currency import CurrencyConverter
    from code.event_classifier import EventClassifier
    from code.image_resolver import ImageResolver


@dataclass
class DailyCashFlow:
    date_str: str
    starting_balance: float
    inflows: float
    outflows: float
    ending_balance: float
    events_applied: List[str]


@dataclass
class ForecastResult:
    user_id: str
    home_currency: str
    request_date: str
    horizon_days: int
    minimum_balance_to_keep: float
    starting_balance: float
    daily_balances: Dict[str, float]
    minimum_projected_balance: float
    minimum_projected_date: str
    projected_inflows_total: float
    projected_outflows_total: float
    assumptions_used: List[str]
    timeline: List[DailyCashFlow]


class CashFlowForecaster:
    def __init__(self, currency_converter: CurrencyConverter, image_resolver: Optional[ImageResolver] = None):
        self.currency_converter = currency_converter
        self.image_resolver = image_resolver
        self.state_resolver = FinancialStateResolver(currency_converter, image_resolver)
        self.recurrence_detector = RecurrenceDetector(image_resolver)
        self.fact_extractor = MessageFactExtractor()
        self.classifier = EventClassifier()

    def forecast_90_days(
        self,
        profile: FinancialProfile,
        user_events: List[FinancialEvent],
        user_messages: List[Message],
        request_date_str: str,
        horizon_days: int = 90,
        custom_outflows: Optional[List[Tuple[str, float]]] = None
    ) -> ForecastResult:
        home_curr = profile.home_currency
        req_date = datetime.strptime(request_date_str, "%Y-%m-%d")

        # 1. Reconstruct initial baseline financial state
        state = self.state_resolver.resolve_state(profile, user_events, request_date_str)
        current_bal = state.starting_safe_balance
        reserved_debit_ids = set(state.reserved_pending_debit_ids)

        # 2. Extract message financial facts up to request_date
        msg_facts = self.fact_extractor.extract_facts(user_messages, request_date_str)
        assumptions: List[str] = []

        # 3. Detect historical recurring patterns
        recurring_patterns = self.recurrence_detector.detect_patterns(user_events, profile, request_date_str)

        explicit_future_by_date = {}

        # Add custom outflows if provided
        if custom_outflows:
            for c_date, c_amt in custom_outflows:
                c_evt = FinancialEvent(
                    event_id=f"custom_pmt_{c_date}",
                    user_id=profile.user_id,
                    event_type='expense',
                    description='Custom payment plan installment',
                    category='payment_plan',
                    direction='debit',
                    amount=c_amt,
                    currency=home_curr,
                    event_date=c_date,
                    settlement_date=c_date,
                    status='scheduled',
                    linked_event_id=None,
                    flexibility='fixed',
                    minimum_allowed_amount=None
                )
                explicit_future_by_date.setdefault(c_date, []).append((c_evt, 'outflow', c_amt))

        # 4. Apply message updates to recurring patterns
        for fact in msg_facts:
            if fact.fact_type == 'salary_update':
                assumptions.append(f"Message {fact.message_id}: Monthly salary updated to {fact.new_amount} {fact.currency} starting {fact.effective_date}")
                for pat in recurring_patterns:
                    if pat.category == 'salary' or pat.event_type == 'income':
                        if fact.new_amount is not None:
                            pat.amount = fact.new_amount
                        if fact.currency:
                            pat.currency = fact.currency

            elif fact.fact_type == 'employment_ended':
                assumptions.append(f"Message {fact.message_id}: Employment ended; future salary projections halted")
                recurring_patterns = [p for p in recurring_patterns if p.category != 'salary' and p.event_type != 'income']

            elif fact.fact_type == 'rent_increase':
                assumptions.append(f"Message {fact.message_id}: Rent increased by multiplier {fact.multiplier}")
                for pat in recurring_patterns:
                    if pat.category in ('rent', 'housing'):
                        if fact.multiplier:
                            pat.amount *= fact.multiplier

            elif fact.fact_type == 'pending_income_unconfirmed':
                assumptions.append(f"Message {fact.message_id}: Pending credit unconfirmed; excluded from cash flow")
                recurring_patterns = [p for p in recurring_patterns if p.category not in ('gig', 'bonus', 'commission', 'freelance', 'payout')]

            elif fact.fact_type == 'one_time_credit' and fact.new_amount and fact.effective_date:
                conv_b = self.currency_converter.convert(fact.new_amount, fact.currency or home_curr, home_curr, request_date_str)
                if conv_b and conv_b > 0:
                    assumptions.append(f"Message {fact.message_id}: Confirmed one-time credit of {fact.new_amount} {fact.currency} on {fact.effective_date}")
                    dummy_evt = FinancialEvent(
                        event_id=f"msg_credit_{fact.message_id}",
                        user_id=profile.user_id,
                        event_type='income',
                        description=f"Confirmed message credit ({fact.message_id})",
                        category='one_time_income',
                        direction='credit',
                        amount=fact.new_amount,
                        currency=fact.currency or home_curr,
                        event_date=fact.effective_date,
                        settlement_date=fact.effective_date,
                        status='settled',
                        linked_event_id=None,
                        flexibility='fixed',
                        minimum_allowed_amount=None
                    )
                    explicit_future_by_date.setdefault(fact.effective_date, []).append((dummy_evt, 'inflow', conv_b))

        # Check if employment ended from events or messages
        emp_ended_events = any(('final' in (e.description or '').lower() and ('payroll' in (e.description or '').lower() or 'salary' in (e.description or '').lower() or 'paycheck' in (e.description or '').lower())) for e in user_events if e.event_date <= request_date_str)
        emp_ended_msgs = any(f.fact_type == 'employment_ended' for f in msg_facts)
        employment_ended_total = emp_ended_events or emp_ended_msgs

        # 5. Build explicit future event schedule
        for evt in user_events:
            cl = self.classifier.classify_event(evt)
            # Rule: Exclude unrealized/non-cash events and pending credits
            if not cl.is_cash_flow_effective or cl.category in ('unrealized_non_cash', 'pending_credit_not_counted'):
                continue

            if employment_ended_total and (evt.category == 'salary' or cl.direction_category == 'inflow' and evt.event_type == 'income'):
                continue

            # Rule: Pending debits reserved at Day 0 must NOT be re-deducted on settlement date
            if evt.event_id in reserved_debit_ids:
                continue

            # Target date is settlement_date or event_date strictly > request_date
            target_date = evt.settlement_date if (evt.settlement_date and evt.settlement_date > request_date_str) else evt.event_date
            if target_date > request_date_str:
                conv_amt = self.state_resolver.resolve_event_amount_converted(evt, home_curr)
                if conv_amt > 0:
                    explicit_future_by_date.setdefault(target_date, []).append((evt, cl.direction_category, conv_amt))

        # 6. Build recurring projections by date
        recurring_by_date = {}
        end_date = req_date + timedelta(days=horizon_days)

        for pat in recurring_patterns:
            conv_pat_amt = self.currency_converter.convert(pat.amount, pat.currency, home_curr, request_date_str)
            if conv_pat_amt is None or conv_pat_amt <= 0:
                continue

            freq_days = max(1, int(pat.frequency_days or 30))
            try:
                curr_pdate = datetime.strptime(pat.next_expected_date, "%Y-%m-%d")
            except ValueError:
                continue

            def _add_months_local(dt: datetime, m: int) -> datetime:
                month = dt.month - 1 + m
                year = dt.year + month // 12
                month = month % 12 + 1
                day = min(dt.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
                return datetime(year, month, day)

            while curr_pdate <= req_date:
                curr_pdate = _add_months_local(curr_pdate, 1) if freq_days == 30 else (curr_pdate + timedelta(days=freq_days))

            while curr_pdate <= end_date:
                pdate_str = curr_pdate.strftime("%Y-%m-%d")
                dir_cat = 'inflow' if pat.direction == 'credit' else 'outflow'
                recurring_by_date.setdefault(pdate_str, []).append((pat, dir_cat, conv_pat_amt))
                curr_pdate = _add_months_local(curr_pdate, 1) if freq_days == 30 else (curr_pdate + timedelta(days=freq_days))

        # 7. Simulate daily cash flow trajectory
        daily_balances: Dict[str, float] = {}
        timeline: List[DailyCashFlow] = []
        running_bal = current_bal

        min_bal = running_bal
        min_date = request_date_str
        total_inflows = 0.0
        total_outflows = 0.0

        for day in range(horizon_days + 1):
            curr_day_date = req_date + timedelta(days=day)
            curr_day_str = curr_day_date.strftime("%Y-%m-%d")

            day_inflows = 0.0
            day_outflows = 0.0
            events_applied: List[str] = []

            # Explicit future events
            if curr_day_str in explicit_future_by_date:
                for evt, dcat, amt in explicit_future_by_date[curr_day_str]:
                    if dcat == 'inflow':
                        day_inflows += amt
                        events_applied.append(f"Explicit Inflow ({evt.category}): +{amt:.2f} {home_curr}")
                    elif dcat == 'outflow':
                        day_outflows += amt
                        events_applied.append(f"Explicit Outflow ({evt.category}): -{amt:.2f} {home_curr}")

            # Recurring events
            if curr_day_str in recurring_by_date:
                explicit_cats = set(e[0].category for e in explicit_future_by_date.get(curr_day_str, []))
                for pat, dcat, amt in recurring_by_date[curr_day_str]:
                    if pat.category not in explicit_cats:
                        if dcat == 'inflow':
                            day_inflows += amt
                            events_applied.append(f"Recurring Inflow ({pat.category}): +{amt:.2f} {home_curr}")
                        elif dcat == 'outflow':
                            day_outflows += amt
                            events_applied.append(f"Recurring Outflow ({pat.category}): -{amt:.2f} {home_curr}")

            start_b = running_bal
            running_bal = start_b + day_inflows - day_outflows
            end_b = running_bal

            total_inflows += day_inflows
            total_outflows += day_outflows

            daily_balances[curr_day_str] = end_b
            timeline.append(DailyCashFlow(
                date_str=curr_day_str,
                starting_balance=start_b,
                inflows=day_inflows,
                outflows=day_outflows,
                ending_balance=end_b,
                events_applied=events_applied
            ))

            if end_b < min_bal:
                min_bal = end_b
                min_date = curr_day_str

        return ForecastResult(
            user_id=profile.user_id,
            home_currency=home_curr,
            request_date=request_date_str,
            horizon_days=horizon_days,
            minimum_balance_to_keep=profile.minimum_balance_to_keep,
            starting_balance=current_bal,
            daily_balances=daily_balances,
            minimum_projected_balance=min_bal,
            minimum_projected_date=min_date,
            projected_inflows_total=total_inflows,
            projected_outflows_total=total_outflows,
            assumptions_used=assumptions,
            timeline=timeline
        )
