"""
Afford IQ · Goal Accelerator Intelligence Engine
Calculates behavior-aware saving plans, daily/weekly/monthly contribution requirements,
dynamic pace adjustments, and educational growth scenarios.
"""

import math
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class Goal:
    goal_id: str
    name: str
    category: str
    target_amount: float
    current_saved: float
    target_date: str
    created_date: str
    monthly_contribution: float
    current_avg_contribution: float
    status: str  # "on_track", "at_risk", "behind", "ahead", "completed"
    icon: str
    color: str


class GoalEngine:
    def __init__(self):
        pass

    def calculate_plan(
        self,
        target_amount: float,
        current_saved: float,
        target_date_str: str,
        monthly_income: float = 35000.0,
        essential_commitments: float = 12499.0,
        buffer_shield: float = 5000.0,
        start_date_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates required daily, weekly, monthly contributions and behavior-aware feasibility.
        """
        try:
            target_d = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        except Exception:
            target_d = (datetime.now() + timedelta(days=365)).date()

        if start_date_str:
            try:
                start_d = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except Exception:
                start_d = datetime.now().date()
        else:
            start_d = datetime.now().date()

        days_diff = max(1, (target_d - start_d).days)
        months_diff = max(1.0, days_diff / 30.4375)
        weeks_diff = max(1.0, days_diff / 7.0)

        remaining_amount = max(0.0, target_amount - current_saved)

        req_daily = remaining_amount / days_diff
        req_weekly = remaining_amount / weeks_diff
        req_monthly = remaining_amount / months_diff

        # Behavior analysis based on cash flow
        # Monthly disposable surplus = income - essential commitments
        disposable_surplus = max(1000.0, monthly_income - essential_commitments)
        
        # Buffer impact ratio
        ratio = req_monthly / disposable_surplus

        if ratio <= 0.50:
            feasibility = "comfortable"
            feasibility_badge = "Easily Achievable"
            feasibility_color = "secondary"
            feasibility_headline = f"Your current spending leaves plenty of room for ₹{round(req_monthly):,.0f}/month."
            feasibility_sub = f"You will retain ~₹{round(disposable_surplus - req_monthly):,.0f}/month for everyday flexible spending and unexpected events."
        elif ratio <= 0.85:
            feasibility = "moderate"
            feasibility_badge = "Achievable with Focus"
            feasibility_color = "primary"
            feasibility_headline = f"₹{round(req_monthly):,.0f}/month is achievable but leaves moderate day-to-day flexibility."
            feasibility_sub = f"Leaves approximately ₹{round(disposable_surplus - req_monthly):,.0f}/month free after essentials and your emergency shield."
        else:
            feasibility = "tight"
            feasibility_badge = "Tight Margin"
            feasibility_color = "tertiary"
            feasibility_headline = f"₹{round(req_monthly):,.0f}/month takes up most of your disposable cash flow."
            feasibility_sub = f"Consider extending your target date by a few months or trimming flexible subscriptions to avoid cash stress."

        # Generate 3 Tailored Approach Plans
        plans = [
            {
                "id": "plan_standard",
                "name": "Plan A · Pure Savings Pace",
                "badge": "Standard",
                "monthly_amount": round(req_monthly),
                "desc": f"Save ₹{round(req_monthly):,.0f}/mo (approx ₹{round(req_daily):,.0f}/day) in your safe savings account.",
                "duration": f"{round(months_diff)} months",
                "is_recommended": (feasibility != "tight")
            },
            {
                "id": "plan_trimmed",
                "name": "Plan B · Optimized Spending Trim",
                "badge": "Balanced",
                "monthly_amount": round(req_monthly * 0.90),
                "desc": f"Save ₹{round(req_monthly * 0.90):,.0f}/mo + reduce discretionary dining/shopping by ₹{round(req_monthly * 0.10):,.0f}/mo.",
                "duration": f"{round(months_diff)} months",
                "is_recommended": (feasibility == "tight")
            },
            {
                "id": "plan_growth",
                "name": "Plan C · Smart Growth Scenario",
                "badge": "Growth Accelerated",
                "monthly_amount": round(self._calculate_sip_monthly(target_amount, current_saved, months_diff, 0.08)),
                "desc": f"Contribute ₹{round(self._calculate_sip_monthly(target_amount, current_saved, months_diff, 0.08)):,.0f}/mo with illustrative 8% annual return compounding.",
                "duration": f"{round(months_diff)} months",
                "is_recommended": False
            }
        ]

        # Growth scenarios
        growth_scenarios = self.generate_growth_scenarios(target_amount, current_saved, months_diff)

        return {
            "target_amount": target_amount,
            "current_saved": current_saved,
            "remaining_amount": remaining_amount,
            "target_date": target_date_str,
            "days_remaining": days_diff,
            "months_remaining": round(months_diff, 1),
            "required_daily": round(req_daily),
            "required_weekly": round(req_weekly),
            "required_monthly": round(req_monthly),
            "disposable_surplus": round(disposable_surplus),
            "feasibility": feasibility,
            "feasibility_badge": feasibility_badge,
            "feasibility_color": feasibility_color,
            "feasibility_headline": feasibility_headline,
            "feasibility_sub": feasibility_sub,
            "plans": plans,
            "growth_scenarios": growth_scenarios
        }

    def recalculate_dynamic_adjustment(
        self,
        target_amount: float,
        current_saved: float,
        target_date_str: str,
        behind_amount: float = 1200.0,
        current_monthly_pace: float = 3750.0
    ) -> Dict[str, Any]:
        """
        Dynamically calculates course corrections when actual pace lags or leads planned pace.
        """
        try:
            target_d = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        except Exception:
            target_d = (datetime.now() + timedelta(days=240)).date()

        now = datetime.now().date()
        remaining_days = max(1, (target_d - now).days)
        remaining_months = max(1.0, remaining_days / 30.4375)

        remaining_amount = max(0.0, target_amount - current_saved)
        
        # Option 1: Catch up to original target date
        new_req_monthly = remaining_amount / remaining_months

        # Option 2: Keep current pace and extend date
        if current_monthly_pace > 0:
            months_needed_at_current_pace = remaining_amount / current_monthly_pace
            days_needed = int(months_needed_at_current_pace * 30.4375)
            extended_date = now + timedelta(days=days_needed)
            days_delayed = max(1, (extended_date - target_d).days)
            extended_date_str = extended_date.strftime("%B %d, %Y")
        else:
            days_delayed = 30
            extended_date_str = (target_d + timedelta(days=30)).strftime("%B %d, %Y")

        # Option 3: Adjust target amount to match current trajectory
        projected_total = current_saved + (current_monthly_pace * remaining_months)

        return {
            "behind_amount": behind_amount,
            "remaining_amount": remaining_amount,
            "remaining_months": round(remaining_months, 1),
            "current_pace": round(current_monthly_pace),
            "original_req_monthly": round(current_monthly_pace),
            "option_increase_monthly": {
                "title": f"Increase monthly contribution to ₹{round(new_req_monthly):,.0f}",
                "amount": f"₹{round(new_req_monthly):,.0f} / month",
                "diff": f"+₹{round(new_req_monthly - current_monthly_pace):,.0f}/mo",
                "result": "Hits original target date with zero delay.",
                "action_type": "increase_pace",
                "new_monthly": round(new_req_monthly)
            },
            "option_extend_date": {
                "title": f"Keep ₹{round(current_monthly_pace):,.0f}/mo & extend by {days_delayed} days",
                "amount": f"Target: {extended_date_str}",
                "diff": f"+{days_delayed} days",
                "result": "Zero budget strain, maintains comfortable monthly breathing room.",
                "action_type": "extend_date",
                "new_date": extended_date_str
            },
            "option_trim_expenses": {
                "title": f"Trim ₹{round(behind_amount / remaining_months):,.0f}/mo from food/shopping",
                "amount": f"Save ₹{round(behind_amount / remaining_months):,.0f} from discretionary",
                "diff": "No extra income needed",
                "result": "Brings goal back on track without raising overall monthly savings requirement.",
                "action_type": "trim_spending"
            }
        }

    def generate_growth_scenarios(
        self,
        target_amount: float,
        current_saved: float,
        months: float
    ) -> List[Dict[str, Any]]:
        """
        Generates 4 educational growth scenarios with clear risk/timeline/liquidity labels.
        """
        remaining_amount = max(0.0, target_amount - current_saved)
        t_years = max(0.1, months / 12.0)

        scenarios_defs = [
            {
                "id": "sc_cash",
                "name": "Liquid Savings Account",
                "rate": 0.04,
                "risk": "Very Low",
                "liquidity": "Instant (Same Day)",
                "icon": "account_balance",
                "color": "secondary",
                "desc": "Capital fully protected. Ideal for emergency funds and short-term goals (< 6 months)."
            },
            {
                "id": "sc_rd",
                "name": "Recurring Deposit / Fixed Income",
                "rate": 0.07,
                "risk": "Low",
                "liquidity": "Tenure Locked (Premature penalty)",
                "icon": "lock_clock",
                "color": "primary",
                "desc": "Guaranteed fixed interest. Great for goals with fixed upcoming dates (6 - 24 months)."
            },
            {
                "id": "sc_balanced",
                "name": "Balanced / Index SIP",
                "rate": 0.10,
                "risk": "Moderate",
                "liquidity": "2 - 3 Business Days",
                "icon": "trending_up",
                "color": "tertiary",
                "desc": "Diversified basket of index equities and debt. Suitable for medium-term horizons (1 - 3 years)."
            },
            {
                "id": "sc_equity",
                "name": "Long-Term Growth Fund",
                "rate": 0.12,
                "risk": "Higher",
                "liquidity": "2 - 3 Business Days",
                "icon": "insights",
                "color": "primary-container",
                "desc": "Higher volatility with long-term compounding potential. Best for horizons > 3 years."
            }
        ]

        results = []
        for s in scenarios_defs:
            r = s["rate"]
            monthly_contrib = self._calculate_sip_monthly(target_amount, current_saved, months, r)
            total_invested = current_saved + (monthly_contrib * months)
            fv = self._calculate_sip_fv(current_saved, monthly_contrib, months, r)
            estimated_gain = max(0.0, fv - total_invested)

            results.append({
                "id": s["id"],
                "name": s["name"],
                "assumed_annual_rate": f"{int(r * 100)}%",
                "monthly_contribution": round(monthly_contrib),
                "total_contributed": round(total_invested),
                "estimated_final_value": round(fv),
                "estimated_gain": round(estimated_gain),
                "risk_level": s["risk"],
                "liquidity": s["liquidity"],
                "icon": s["icon"],
                "color": s["color"],
                "desc": s["desc"],
                "timeline_fit": (
                    "Best fit" if (months < 12 and s["id"] in ["sc_cash", "sc_rd"])
                    or (12 <= months <= 36 and s["id"] in ["sc_rd", "sc_balanced"])
                    or (months > 36 and s["id"] in ["sc_balanced", "sc_equity"])
                    else "Optional"
                )
            })

        return results

    def _calculate_sip_monthly(
        self,
        target_amount: float,
        initial_lump: float,
        months: float,
        annual_rate: float
    ) -> float:
        """
        Calculates required monthly contribution to reach target_amount in N months at annual_rate.
        """
        if months <= 0:
            return max(0.0, target_amount - initial_lump)

        if annual_rate <= 0:
            return max(0.0, target_amount - initial_lump) / months

        i = annual_rate / 12.0
        # Future value of initial lump sum
        fv_lump = initial_lump * ((1.0 + i) ** months)
        needed_from_sip = max(0.0, target_amount - fv_lump)

        # FV_sip = P * [((1 + i)^n - 1) / i] * (1 + i)
        # P = FV_sip / ([((1 + i)^n - 1) / i] * (1 + i))
        factor = (((1.0 + i) ** months - 1.0) / i) * (1.0 + i)
        if factor <= 0:
            return needed_from_sip / months

        return needed_from_sip / factor

    def _calculate_sip_fv(
        self,
        initial_lump: float,
        monthly_contrib: float,
        months: float,
        annual_rate: float
    ) -> float:
        """
        Calculates Future Value of an initial lump sum + monthly contributions.
        """
        if annual_rate <= 0:
            return initial_lump + (monthly_contrib * months)

        i = annual_rate / 12.0
        fv_lump = initial_lump * ((1.0 + i) ** months)
        factor = (((1.0 + i) ** months - 1.0) / i) * (1.0 + i)
        fv_sip = monthly_contrib * factor
        return fv_lump + fv_sip
