"""
Message Fact Extractor for HackerRank Orchestrate: Buy or Wait?
Extracts deterministic financial facts from user messages sent on or before request_date.
Enforces untrusted evidence safeguards (ignores embedded prompt commands/directives).
"""
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Any

try:
    from models import Message
except ImportError:
    from code.models import Message


@dataclass
class MessageFinancialFact:
    message_id: str
    user_id: str
    sent_at: str
    fact_type: str  # 'salary_update', 'employment_ended', 'rent_increase', 'pending_income_unconfirmed', 'one_time_credit'
    new_amount: Optional[float]
    currency: Optional[str]
    effective_date: Optional[str]
    multiplier: Optional[float]
    raw_text: str


class MessageFactExtractor:
    def extract_facts(self, messages: List[Message], request_date_str: str) -> List[MessageFinancialFact]:
        facts: List[MessageFinancialFact] = []

        for m in messages:
            # Consider only messages sent on or before request_date
            sent_date_str = m.sent_at[:10]
            if sent_date_str > request_date_str:
                continue

            text = m.message_text

            # 1. Salary Increase / Salary Update Pattern
            # English: "monthly salary is EUR 2827", "monthly pay is EUR 1037.52", "salary of USD 1680 is confirmed", "first salary of ZAR 38280"
            # Indonesian: "Gaji bulanan Anda naik menjadi IDR 42750000", "Sisa gaji bulanan... adalah IDR 48260000", "Gaji pertama Anda sebesar IDR 16910000"
            sal_match = re.search(r'(?:gaji|salary|pay)(?:[^\d\n]{1,40})?(INR|EUR|IDR|ZAR|USD)\s*([\d\.,]+)', text, re.IGNORECASE)
            if not sal_match:
                sal_match = re.search(r'(INR|EUR|IDR|ZAR|USD)\s*([\d\.,]+)(?:[^\n]{1,40})?(?:gaji|salary|pay)', text, re.IGNORECASE)

            # Check employment ended pattern first
            ended_match = re.search(r'(employment has ended|contract has ended|kontrak.*berakhir|pendapatan.*berakhir)', text, re.IGNORECASE)

            if ended_match:
                # If message states remaining salary, capture it
                if sal_match:
                    curr = sal_match.group(1).upper()
                    amt_str = sal_match.group(2).replace(',', '').rstrip('.')
                    try:
                        amt = float(amt_str)
                        facts.append(MessageFinancialFact(
                            message_id=m.message_id,
                            user_id=m.user_id,
                            sent_at=m.sent_at,
                            fact_type='salary_update',
                            new_amount=amt,
                            currency=curr,
                            effective_date=sent_date_str,
                            multiplier=None,
                            raw_text=text
                        ))
                    except ValueError:
                        pass
                else:
                    facts.append(MessageFinancialFact(
                        message_id=m.message_id,
                        user_id=m.user_id,
                        sent_at=m.sent_at,
                        fact_type='employment_ended',
                        new_amount=0.0,
                        currency=None,
                        effective_date=sent_date_str,
                        multiplier=None,
                        raw_text=text
                    ))
            elif sal_match:
                curr = sal_match.group(1).upper()
                amt_str = sal_match.group(2).replace(',', '').rstrip('.')
                try:
                    amt = float(amt_str)
                    # Check for effective date in text e.g. "berlaku mulai 2025-08-15" or "confirmed for 2024-06-15"
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
                    eff_date = date_match.group(1) if date_match else sent_date_str

                    facts.append(MessageFinancialFact(
                        message_id=m.message_id,
                        user_id=m.user_id,
                        sent_at=m.sent_at,
                        fact_type='salary_update',
                        new_amount=amt,
                        currency=curr,
                        effective_date=eff_date,
                        multiplier=None,
                        raw_text=text
                    ))
                except ValueError:
                    pass

            # 2. Rent Increase Pattern e.g. "increases monthly rent by 12%"
            rent_match = re.search(r'increases monthly rent by (\d+)%', text, re.IGNORECASE)
            if rent_match:
                pct = float(rent_match.group(1))
                facts.append(MessageFinancialFact(
                    message_id=m.message_id,
                    user_id=m.user_id,
                    sent_at=m.sent_at,
                    fact_type='rent_increase',
                    new_amount=None,
                    currency=None,
                    effective_date=sent_date_str,
                    multiplier=1.0 + (pct / 100.0),
                    raw_text=text
                ))

            # 3. Unconfirmed Pending Income Pattern (bonus pending, prize pending)
            unconfirmed_match = re.search(r'(bonus.*pending|prize.*processing|payout.*pending|faktur.*menunggu)', text, re.IGNORECASE)
            if unconfirmed_match and not sal_match:
                facts.append(MessageFinancialFact(
                    message_id=m.message_id,
                    user_id=m.user_id,
                    sent_at=m.sent_at,
                    fact_type='pending_income_unconfirmed',
                    new_amount=None,
                    currency=None,
                    effective_date=sent_date_str,
                    multiplier=None,
                    raw_text=text
                ))

            # 4. Confirmed One-Time Credit Pattern (e.g. bonus of $5,000 USD on 2025-04-15)
            bonus_match = re.search(r'(?:bonus|credit|payout|prize|commission)(?:[^\d\n]{1,40})?(USD|EUR|INR|IDR|ZAR|\$)\s*([\d\.,]+)(?:[^\n]{1,60})?(\d{4}-\d{2}-\d{2})', text, re.IGNORECASE)
            if bonus_match and not unconfirmed_match:
                c_str = bonus_match.group(1)
                c_str = 'USD' if c_str == '$' else c_str.upper()
                a_str = bonus_match.group(2).replace(',', '')
                d_str = bonus_match.group(3)
                try:
                    b_amt = float(a_str)
                    facts.append(MessageFinancialFact(
                        message_id=m.message_id,
                        user_id=m.user_id,
                        sent_at=m.sent_at,
                        fact_type='one_time_credit',
                        new_amount=b_amt,
                        currency=c_str,
                        effective_date=d_str,
                        multiplier=None,
                        raw_text=text
                    ))
                except ValueError:
                    pass

        return facts
