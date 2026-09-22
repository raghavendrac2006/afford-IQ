"""
Safe Amount & Affordability Engine for HackerRank Orchestrate: Buy or Wait?
Provides deterministic calculation of:
- amount_safe_to_pay
- earliest_date_for_full_payment
- affordability_status
"""
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime, timedelta

try:
    from models import FinancialProfile, FinancialEvent, Message, Request
    from financial_state import FinancialStateResolver, UserFinancialState
    from recurrence import RecurrenceDetector
    from currency import CurrencyConverter
    from event_classifier import EventClassifier
    from image_resolver import ImageResolver
    from forecaster import CashFlowForecaster, ForecastResult
except ImportError:
    from code.models import FinancialProfile, FinancialEvent, Message, Request
    from code.financial_state import FinancialStateResolver, UserFinancialState
    from code.recurrence import RecurrenceDetector
    from code.currency import CurrencyConverter
    from code.event_classifier import EventClassifier
    from code.image_resolver import ImageResolver
    from code.forecaster import CashFlowForecaster, ForecastResult


@dataclass
class SafeAmountDecision:
    request_id: str
    user_id: str
    request_date: str
    requested_amount: float
    home_currency: str
    current_available_balance: float
    minimum_balance_to_keep: float
    starting_safe_balance: float
    next_salary_date: Optional[str]
    pre_salary_outflows: float
    pre_salary_trough: float
    amount_safe_to_pay: float
    earliest_date_for_full_payment: Optional[str]
    affordability_status: str


class SafeAmountEngine:
    def __init__(self, currency_converter: CurrencyConverter, image_resolver: Optional[ImageResolver] = None):
        self.currency_converter = currency_converter
        self.image_resolver = image_resolver
        self.state_resolver = FinancialStateResolver(currency_converter, image_resolver)
        self.recurrence_detector = RecurrenceDetector(image_resolver)
        self.classifier = EventClassifier()
        self.forecaster = CashFlowForecaster(currency_converter, image_resolver)

    def find_next_salary_date(
        self,
        user_events: List[FinancialEvent],
        request_date_str: str,
        profile: Optional[FinancialProfile] = None,
        user_messages: Optional[List[Message]] = None
    ) -> Optional[str]:
        for e in user_events:
            desc_lower = (e.description or '').lower()
            if 'final' in desc_lower and ('payroll' in desc_lower or 'salary' in desc_lower or 'paycheck' in desc_lower):
                return None

        salary_events = [
            e for e in user_events
            if (e.category == 'salary' or e.event_type == 'income')
            and e.direction == 'credit'
            and e.status in ('settled', 'scheduled')
        ]
        
        future_salary_dates = []
        for e in salary_events:
            target = e.settlement_date if (e.settlement_date and e.settlement_date > request_date_str) else e.event_date
            if target > request_date_str:
                future_salary_dates.append(target)

        if future_salary_dates:
            return min(future_salary_dates)

        req_dt = datetime.strptime(request_date_str, "%Y-%m-%d")
        sal_dt = datetime(req_dt.year, req_dt.month, 15)
        if sal_dt <= req_dt:
            m = req_dt.month % 12 + 1
            y = req_dt.year + (req_dt.month // 12)
            sal_dt = datetime(y, m, 15)

        return sal_dt.strftime("%Y-%m-%d")

    def compute_pre_salary_outflows(
        self,
        profile: FinancialProfile,
        user_events: List[FinancialEvent],
        request_date_str: str,
        next_salary_date_str: Optional[str]
    ) -> float:
        home_curr = profile.home_currency
        pre_sal_outflows = 0.0
        if next_salary_date_str:
            limit_date = next_salary_date_str
        else:
            req_dt_tmp = datetime.strptime(request_date_str, "%Y-%m-%d")
            limit_date = (req_dt_tmp + timedelta(days=30)).strftime("%Y-%m-%d")

        scheduled_cats = set()
        for evt in user_events:
            cl = self.classifier.classify_event(evt)
            if cl.direction_category == 'outflow' and evt.status in ('scheduled', 'pending'):
                if evt.status == 'pending' and evt.event_date <= request_date_str:
                    continue
                target_date = evt.settlement_date if (evt.settlement_date and evt.settlement_date > request_date_str) else evt.event_date
                if request_date_str < target_date <= limit_date:
                    amt = self.state_resolver.resolve_event_amount_converted(evt, home_curr)
                    if amt > 0:
                        pre_sal_outflows += amt
                        scheduled_cats.add(evt.category)

        patterns = self.recurrence_detector.detect_patterns(user_events, profile, request_date_str)
        req_dt = datetime.strptime(request_date_str, "%Y-%m-%d")
        limit_dt = datetime.strptime(limit_date, "%Y-%m-%d")

        for pat in patterns:
            if pat.direction == 'debit' and pat.category not in scheduled_cats:
                conv_amt = self.currency_converter.convert(pat.amount, pat.currency, home_curr, request_date_str)
                if conv_amt and conv_amt > 0:
                    freq_days = max(1, int(pat.frequency_days or 30))
                    try:
                        next_dt = datetime.strptime(pat.next_expected_date, "%Y-%m-%d")
                    except ValueError:
                        continue

                    while next_dt < req_dt:
                        next_dt += timedelta(days=freq_days)

                    while next_dt <= limit_dt:
                        pre_sal_outflows += conv_amt
                        next_dt += timedelta(days=freq_days)

        return pre_sal_outflows

    def calculate_earliest_full_payment_date(
        self,
        profile: FinancialProfile,
        user_events: List[FinancialEvent],
        user_messages: List[Message],
        request_date_str: str,
        requested_amount: float,
        horizon_days: int = 90,
        desired_completion_date: Optional[str] = None
    ) -> Optional[str]:
        fc = self.forecaster.forecast_90_days(profile, user_events, user_messages, request_date_str, horizon_days=horizon_days)
        min_bal = profile.minimum_balance_to_keep
        req_dt = datetime.strptime(request_date_str, "%Y-%m-%d")
        daily_bals = fc.daily_balances

        max_check_days = horizon_days
        if desired_completion_date:
            try:
                comp_dt = datetime.strptime(desired_completion_date, "%Y-%m-%d")
                days_to_comp = (comp_dt - req_dt).days
                if days_to_comp >= 0:
                    max_check_days = min(horizon_days, max(days_to_comp, 30))
            except ValueError:
                pass

        for day in range(horizon_days + 1):
            eval_dt = req_dt + timedelta(days=day)
            eval_date_str = eval_dt.strftime("%Y-%m-%d")

            if eval_date_str not in daily_bals:
                continue

            is_feasible = True
            for future_day in range(day, max_check_days + 1):
                f_dt = req_dt + timedelta(days=future_day)
                f_date_str = f_dt.strftime("%Y-%m-%d")
                if f_date_str in daily_bals:
                    bal_after_payment = daily_bals[f_date_str] - requested_amount
                    if bal_after_payment < min_bal - 1e-5:
                        is_feasible = False
                        break

            if is_feasible:
                return eval_date_str

        return None

    def evaluate_request(
        self,
        request: Request,
        profile: FinancialProfile,
        user_events: List[FinancialEvent],
        user_messages: List[Message]
    ) -> SafeAmountDecision:
        user_id = request.user_id
        req_id = request.request_id
        req_date = request.request_date
        req_amt = request.requested_amount
        home_curr = profile.home_currency
        min_bal = profile.minimum_balance_to_keep

        state = self.state_resolver.resolve_state(profile, user_events, req_date)
        cur_bal = profile.current_available_balance
        start_bal = state.starting_safe_balance

        next_sal_date = self.find_next_salary_date(user_events, req_date, profile)
        pre_sal_outflows = self.compute_pre_salary_outflows(profile, user_events, req_date, next_sal_date)

        pre_sal_trough = start_bal - pre_sal_outflows
        if next_sal_date is None:
            fc_baseline = self.forecaster.forecast_90_days(profile, user_events, user_messages, req_date)
            amount_safe = max(0.0, min(req_amt, pre_sal_trough - min_bal, fc_baseline.minimum_projected_balance - min_bal))
        else:
            amount_safe = max(0.0, min(req_amt, pre_sal_trough - min_bal))

        if abs(amount_safe - req_amt) < 0.01:
            earliest_full_date = req_date
            status = 'affordable_now'
        else:
            earliest_full_date = self.calculate_earliest_full_payment_date(
                profile, user_events, user_messages, req_date, req_amt,
                desired_completion_date=request.desired_completion_date
            )

        if abs(amount_safe - req_amt) >= 0.01:
            if earliest_full_date is not None:
                if earliest_full_date == req_date:
                    status = 'affordable_now'
                else:
                    status = 'affordable_later'
            elif amount_safe > 0:
                status = 'affordable_with_plan'
            else:
                status = 'not_affordable'

        return SafeAmountDecision(
            request_id=req_id,
            user_id=user_id,
            request_date=req_date,
            requested_amount=req_amt,
            home_currency=home_curr,
            current_available_balance=cur_bal,
            minimum_balance_to_keep=min_bal,
            starting_safe_balance=start_bal,
            next_salary_date=next_sal_date or req_date,
            pre_salary_outflows=pre_sal_outflows,
            pre_salary_trough=pre_sal_trough,
            amount_safe_to_pay=amount_safe,
            earliest_date_for_full_payment=earliest_full_date,
            affordability_status=status
        )
