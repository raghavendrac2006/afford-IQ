"""
Payment Plan & Spending Change Optimizer for HackerRank Orchestrate: Buy or Wait?
Provides deterministic candidate generation, 90-day safety simulation,
spending change search, plan ranking, and final decision generation.
"""
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Any, Set
from datetime import datetime, timedelta

try:
    from models import FinancialProfile, FinancialEvent, Message, Request, PaymentOption
    from financial_state import FinancialStateResolver
    from currency import CurrencyConverter
    from image_resolver import ImageResolver
    from forecaster import CashFlowForecaster, ForecastResult
    from safe_amount_engine import SafeAmountEngine, SafeAmountDecision
    from payment_options import PaymentOptionResolver
except ImportError:
    from code.models import FinancialProfile, FinancialEvent, Message, Request, PaymentOption
    from code.financial_state import FinancialStateResolver
    from code.currency import CurrencyConverter
    from code.image_resolver import ImageResolver
    from code.forecaster import CashFlowForecaster, ForecastResult
    from code.safe_amount_engine import SafeAmountEngine, SafeAmountDecision
    from code.payment_options import PaymentOptionResolver


def format_amount(amt: float) -> str:
    """Format monetary amount cleanly: integer string if whole number, else 2 decimal places."""
    if abs(amt - round(amt)) < 1e-4:
        return str(int(round(amt)))
    return f"{amt:.2f}"


@dataclass
class PlanCandidate:
    recommended_payment_method: str
    affordability_status: str
    payment_plan: str
    spending_changes_needed: str
    total_amount_paid: float
    start_date: str
    completion_date: str
    num_payments: int
    payment_option_id: str
    is_valid: bool
    spending_change_count: int
    completes_by_deadline: bool
    explanation: str


class PaymentPlanOptimizer:
    def __init__(
        self,
        currency_converter: CurrencyConverter,
        image_resolver: Optional[ImageResolver] = None
    ):
        self.cc = currency_converter
        self.image_resolver = image_resolver
        self.safe_engine = SafeAmountEngine(currency_converter, image_resolver)
        self.forecaster = CashFlowForecaster(currency_converter, image_resolver)

    def find_spending_changes(
        self,
        profile: FinancialProfile,
        user_events: List[FinancialEvent],
        request_date_str: str,
        needed_amount: float
    ) -> Tuple[List[Dict[str, Any]], str, float]:
        """
        Finds minimal permitted spending changes (stop / reduce_to) to release needed cash capacity.
        Returns (applied_changes, spending_changes_str, released_amount).
        """
        stop_cats = set(profile.expense_categories_user_is_willing_to_stop or [])
        reduce_cats = set(profile.expense_categories_user_is_willing_to_reduce or [])
        protect_cats = set(profile.expense_categories_to_protect or [])

        candidate_events = []
        for e in user_events:
            if e.user_id != profile.user_id:
                continue
            if e.direction != 'debit':
                continue
            if e.category in protect_cats:
                continue

            amt = e.amount
            if amt is None and self.image_resolver:
                res = self.image_resolver.resolve_event_amount(e)
                if res.get("resolved") and res.get("amount") is not None:
                    amt = res["amount"]

            if amt is None or amt <= 0:
                continue

            flex = (e.flexibility or '').lower()
            can_stop = (e.category in stop_cats) and ('stop' in flex or flex in ('optional', 'flexible', 'adjustable', 'stoppable'))
            can_reduce = (e.category in reduce_cats) and ('reduc' in flex or flex in ('flexible', 'adjustable')) and (e.minimum_allowed_amount is not None) and (e.minimum_allowed_amount < amt)

            if can_stop or can_reduce:
                candidate_events.append(e)

        if not candidate_events:
            return [], "none", 0.0

        # Group by category and pick most recent event
        cats_most_recent = {}
        for e in candidate_events:
            cat = e.category
            if cat not in cats_most_recent or e.event_date > cats_most_recent[cat].event_date:
                cats_most_recent[cat] = e

        recent_candidates = list(cats_most_recent.values())
        sub_cats = {'streaming', 'cloud_storage', 'music_subscription', 'delivery_membership', 'software', 'hobbies', 'entertainment'}

        def rank_key(e):
            cat = e.category
            is_stop = (cat in stop_cats)
            is_sub = (cat in sub_cats)
            return (0 if is_stop else 1, 0 if is_sub else 1, e.event_date, e.event_id)

        recent_candidates.sort(key=rank_key)

        applied = []
        change_strs = []
        released_total = 0.0

        for e in recent_candidates:
            amt = e.amount or 0.0
            flex = (e.flexibility or '').lower()
            if e.category in stop_cats and ('stop' in flex or flex in ('optional', 'flexible', 'adjustable', 'stoppable')):
                applied.append({'event_id': e.event_id, 'action': 'stop'})
                change_strs.append(f"stop:{e.event_id}")
                released_total += amt
            elif e.category in reduce_cats and e.minimum_allowed_amount is not None:
                min_amt = e.minimum_allowed_amount
                savings = amt - min_amt
                applied.append({'event_id': e.event_id, 'action': 'reduce', 'new_amount': min_amt})
                change_strs.append(f"reduce_to:{e.event_id}:{format_amount(min_amt)}")
                released_total += savings

            if released_total >= needed_amount - 1e-4:
                break

        if applied:
            return applied, "|".join(change_strs), released_total

        return [], "none", 0.0

    def evaluate_request(
        self,
        request: Request,
        profile: FinancialProfile,
        user_events: List[FinancialEvent],
        payment_options: List[PaymentOption],
        user_messages: List[Message]
    ) -> PlanCandidate:
        req_id = request.request_id
        req_date = request.request_date
        req_amt = request.requested_amount
        desired_deadline = request.desired_completion_date
        user_methods = set(profile.payment_methods_user_will_consider or [])

        # 1. Base Safe Amount Decision from Phase 3 Engine
        safe_dec = self.safe_engine.evaluate_request(request, profile, user_events, user_messages)
        safe_amt = safe_dec.amount_safe_to_pay
        earliest_full_dt = safe_dec.earliest_date_for_full_payment

        # Level 1: Full Payment Today without spending changes
        if ('full_payment' in user_methods or not user_methods) and safe_amt >= req_amt - 1e-4:
            return PlanCandidate(
                recommended_payment_method='full_payment',
                affordability_status='affordable_now',
                payment_plan=f"{req_date}:{format_amount(req_amt)}",
                spending_changes_needed='none',
                total_amount_paid=req_amt,
                start_date=req_date,
                completion_date=req_date,
                num_payments=1,
                payment_option_id='z_none',
                is_valid=True,
                spending_change_count=0,
                completes_by_deadline=(req_date <= desired_deadline),
                explanation=f"Full payment of {format_amount(req_amt)} on {req_date} is safe."
            )

        # Level 2: Partial Payment or Installment options without spending changes
        level2_candidates = []

        if request.allows_partial_payment and ('partial_payment' in user_methods or not user_methods):
            if 0 < safe_amt < req_amt and earliest_full_dt and earliest_full_dt <= desired_deadline:
                rem_amt = req_amt - safe_amt
                level2_candidates.append(PlanCandidate(
                    recommended_payment_method='partial_payment',
                    affordability_status='affordable_with_plan',
                    payment_plan=f"{req_date}:{format_amount(safe_amt)}|{earliest_full_dt}:{format_amount(rem_amt)}",
                    spending_changes_needed='none',
                    total_amount_paid=req_amt,
                    start_date=req_date,
                    completion_date=earliest_full_dt,
                    num_payments=2,
                    payment_option_id='z_none',
                    is_valid=True,
                    spending_change_count=0,
                    completes_by_deadline=True,
                    explanation=f"Pay {format_amount(safe_amt)} today and remaining {format_amount(rem_amt)} on {earliest_full_dt}."
                ))

        if payment_options:
            for opt in payment_options:
                n_pmts = opt.number_of_payments
                pmt_amt = opt.payment_amount
                freq_days = int(opt.payment_frequency_days or 30)
                first_dt = datetime.strptime(opt.first_payment_date, "%Y-%m-%d")

                pmt_schedule = []
                plan_str_parts = []
                for i in range(n_pmts):
                    p_dt = first_dt + timedelta(days=i * freq_days)
                    p_dt_str = p_dt.strftime("%Y-%m-%d")
                    pmt_schedule.append((p_dt_str, pmt_amt))
                    plan_str_parts.append(f"{p_dt_str}:{format_amount(pmt_amt)}")

                last_dt_str = pmt_schedule[-1][0]
                plan_str = "|".join(plan_str_parts)
                opt_method = 'full_payment' if (n_pmts == 1 and opt.payment_method == 'full_payment') else 'installments'

                if user_methods:
                    if opt_method == 'full_payment' and 'full_payment' not in user_methods:
                        continue
                    if opt_method == 'installments' and not any(m in ['installments', 'bnpl', 'credit_card'] for m in user_methods):
                        continue

                if n_pmts > 1 and profile.max_installment_months is not None:
                    duration_days = (datetime.strptime(last_dt_str, "%Y-%m-%d") - first_dt).days
                    if duration_days > int(profile.max_installment_months * 30.5):
                        continue

                if last_dt_str > desired_deadline:
                    continue

                is_pmt_safe = (pmt_amt <= safe_amt + 1e-4)
                if not is_pmt_safe and opt.first_payment_date != req_date:
                    next_sal = self.safe_engine.find_next_salary_date(user_events, req_date, profile)
                    limit_dt = opt.first_payment_date
                    if next_sal and opt.first_payment_date <= next_sal:
                        pre_out = self.safe_engine.compute_pre_salary_outflows(profile, user_events, req_date, limit_dt)
                        start_bal = self.safe_engine.state_resolver.resolve_state(profile, user_events, req_date).starting_safe_balance
                        if (start_bal - pre_out - profile.minimum_balance_to_keep) >= pmt_amt - 1e-4:
                            is_pmt_safe = True

                if is_pmt_safe:
                    level2_candidates.append(PlanCandidate(
                        recommended_payment_method=opt_method,
                        affordability_status='affordable_now' if (opt_method == 'full_payment' and opt.first_payment_date == req_date) else 'affordable_with_plan',
                        payment_plan=plan_str,
                        spending_changes_needed='none',
                        total_amount_paid=opt.total_payable_amount,
                        start_date=opt.first_payment_date,
                        completion_date=last_dt_str,
                        num_payments=n_pmts,
                        payment_option_id=opt.payment_option_id,
                        is_valid=True,
                        spending_change_count=0,
                        completes_by_deadline=True,
                        explanation=f"Use {n_pmts} payment(s) of {format_amount(pmt_amt)} starting {opt.first_payment_date}."
                    ))

        if level2_candidates:
            level2_candidates.sort(key=lambda c: (c.total_amount_paid, c.num_payments, c.start_date, c.payment_option_id))
            return level2_candidates[0]

        # Level 3: Full Payment Today WITH spending changes
        if ('full_payment' in user_methods or not user_methods):
            needed = req_amt - safe_amt
            applied, changes_str, released = self.find_spending_changes(profile, user_events, req_date, needed)
            if safe_amt + released >= req_amt - 1e-4 and applied:
                return PlanCandidate(
                    recommended_payment_method='full_payment',
                    affordability_status='affordable_with_plan',
                    payment_plan=f"{req_date}:{format_amount(req_amt)}",
                    spending_changes_needed=changes_str,
                    total_amount_paid=req_amt,
                    start_date=req_date,
                    completion_date=req_date,
                    num_payments=1,
                    payment_option_id='z_none',
                    is_valid=True,
                    spending_change_count=len(applied),
                    completes_by_deadline=(req_date <= desired_deadline),
                    explanation=f"Apply spending changes ({changes_str}) then pay {format_amount(req_amt)} in full on {req_date}."
                )

        # Level 4: Wait (Full Payment Later)
        if earliest_full_dt and earliest_full_dt <= desired_deadline:
            return PlanCandidate(
                recommended_payment_method='wait',
                affordability_status='affordable_later',
                payment_plan=f"{earliest_full_dt}:{format_amount(req_amt)}",
                spending_changes_needed='none',
                total_amount_paid=req_amt,
                start_date=earliest_full_dt,
                completion_date=earliest_full_dt,
                num_payments=1,
                payment_option_id='z_none',
                is_valid=True,
                spending_change_count=0,
                completes_by_deadline=True,
                explanation=f"Pay {format_amount(req_amt)} in full on {earliest_full_dt}."
            )

        # Level 5: not_recommended
        return PlanCandidate(
            recommended_payment_method='not_recommended',
            affordability_status='not_affordable',
            payment_plan='none',
            spending_changes_needed='none',
            total_amount_paid=0.0,
            start_date=req_date,
            completion_date='9999-12-31',
            num_payments=0,
            payment_option_id='z_none',
            is_valid=False,
            spending_change_count=0,
            completes_by_deadline=False,
            explanation=f"Do not proceed with request. None of the available options keeps minimum balance protected."
        )
