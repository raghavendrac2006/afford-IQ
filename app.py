#!/usr/bin/env python3
"""
Afford IQ Mobile Prototype Backend Server
Integrates the validated HackerRank Orchestrate "Buy or Wait?" financial decision engine
with a modern, responsive mobile-first UI prototype.
"""

import os
import sys
import json
import re
import mimetypes
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add code directory to path
repo_root = os.path.abspath(os.path.dirname(__file__))
code_dir = os.path.join(repo_root, "code")
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from data_loader import DataLoader
from indexes import DatasetIndexes
from currency import CurrencyConverter
from image_resolver import ImageResolver
from safe_amount_engine import SafeAmountEngine
from optimizer import PaymentPlanOptimizer
from models import Request, FinancialProfile, FinancialEvent, PaymentOption, Message

# Initialize data and engine
dataset_dir = os.path.join(repo_root, "dataset")
loader = DataLoader(dataset_dir)
profiles_list = loader.load_financial_profiles("financial_profiles.csv")
events_list = loader.load_financial_events("financial_events.csv")
options_list = loader.load_request_payment_options("request_payment_options.csv")
messages_list = loader.load_messages("messages.csv")
images_list = loader.load_images("images.csv")
rates_list = loader.load_exchange_rates("exchange_rates.csv")

indexes = DatasetIndexes(profiles_list, events_list, options_list, messages_list, images_list, rates_list)
currency_converter = CurrencyConverter(rates_list)
image_resolver = ImageResolver(dataset_dir, images_list)
safe_engine = SafeAmountEngine(currency_converter, image_resolver)
optimizer = PaymentPlanOptimizer(currency_converter, image_resolver)

# In-memory user state & settings (defaults to Rahul / user_01)
current_user_id = "user_01"
user_custom_settings = {
    "user_name": "Rahul",
    "monthly_income": 35000.0,
    "minimum_balance": 5000.0,
    "current_balance": 25949.0,
    "cloud_sync": False,
    "transaction_capture": True,
    "on_device_ai": True,
    "home_currency": "INR"
}

def parse_amount_from_query(text: str) -> float:
    """Extract numeric monetary amount from text query."""
    if not text:
        return 40000.0
    # Try ₹40,000 or 40000 or 40k
    text_clean = text.replace(",", "")
    k_match = re.search(r'([0-9.]+)\s*k\b', text_clean, re.IGNORECASE)
    if k_match:
        try:
            return float(k_match.group(1)) * 1000.0
        except ValueError:
            pass
    amt_match = re.search(r'(?:₹|rs\.?|inr)?\s*([0-9]+(?:\.[0-9]{1,2})?)', text_clean, re.IGNORECASE)
    if amt_match:
        try:
            val = float(amt_match.group(1))
            if val > 0:
                return val
        except ValueError:
            pass
    return 40000.0

def get_demo_transactions(user_id: str):
    """Returns realistic transaction activity list."""
    u_events = indexes.get_events_for_user(user_id)
    tx_list = []
    
    # Curated high-fidelity Indian UPI transactions matching design
    default_txs = [
        {
            "id": "tx_01",
            "merchant": "Sri Lakshmi Stores",
            "category": "Food · Chai & Snacks",
            "date": "Today, 1:05 PM",
            "amount": 30.0,
            "direction": "debit",
            "type": "Auto-detected (UPI)",
            "icon": "local_cafe",
            "color": "tertiary",
            "status": "Affordable",
            "note": "Quick UPI payment at local tea store."
        },
        {
            "id": "tx_02",
            "merchant": "Rapido Auto",
            "category": "Transport · Daily Commute",
            "date": "Today, 12:40 PM",
            "amount": 120.0,
            "direction": "debit",
            "type": "Auto-detected (UPI)",
            "icon": "two_wheeler",
            "color": "primary",
            "status": "Buffer -0.8%",
            "note": "Ride from Koramangala to HSR Layout."
        },
        {
            "id": "tx_03",
            "merchant": "Netflix India",
            "category": "Subscription · Entertainment",
            "date": "Yesterday, 9:00 AM",
            "amount": 299.0,
            "direction": "debit",
            "type": "Auto-detected (Auto-debit)",
            "icon": "movie",
            "color": "error",
            "status": "Recurring",
            "note": "Monthly mobile streaming plan renewal."
        },
        {
            "id": "tx_04",
            "merchant": "Amazon India",
            "category": "Shopping · Electronics",
            "date": "20 Sep, 4:15 PM",
            "amount": 1499.0,
            "direction": "debit",
            "type": "Shared via receipt OCR",
            "icon": "shopping_bag",
            "color": "primary",
            "status": "Planned",
            "note": "Ergonomic keyboard for desk setup."
        },
        {
            "id": "tx_05",
            "merchant": "Swiggy Food Delivery",
            "category": "Food · Dinner",
            "date": "19 Sep, 8:45 PM",
            "amount": 450.0,
            "direction": "debit",
            "type": "Auto-detected (UPI)",
            "icon": "restaurant",
            "color": "tertiary",
            "status": "Within budget",
            "note": "Dinner bowl order from Meghana Foods."
        },
        {
            "id": "tx_06",
            "merchant": "Salary Credit (Infosys / TechCorp)",
            "category": "Income · Direct Deposit",
            "date": "15 Sep, 6:00 AM",
            "amount": 35000.0,
            "direction": "credit",
            "type": "Settled Direct Credit",
            "icon": "account_balance",
            "color": "secondary",
            "status": "Settled",
            "note": "September monthly salary payroll credit."
        }
    ]
    return default_txs

def get_demo_commitments(user_id: str):
    """Returns upcoming commitments schedule."""
    return [
        {
            "id": "com_01",
            "title": "Apartment Rent",
            "category": "Housing · Essential",
            "amount": 8000.0,
            "due_date": "5 Oct, 2026",
            "days_left": 13,
            "icon": "home",
            "flexibility": "fixed",
            "color": "error"
        },
        {
            "id": "com_02",
            "title": "Bike Loan EMI",
            "category": "Debt Repayment · Loan",
            "amount": 3500.0,
            "due_date": "10 Oct, 2026",
            "days_left": 18,
            "icon": "two_wheeler",
            "flexibility": "fixed",
            "color": "tertiary"
        },
        {
            "id": "com_03",
            "title": "BESCOM Electricity Bill",
            "category": "Utilities · Electricity",
            "amount": 700.0,
            "due_date": "12 Oct, 2026",
            "days_left": 20,
            "icon": "bolt",
            "flexibility": "reducible",
            "color": "primary"
        },
        {
            "id": "com_04",
            "title": "Wi-Fi & Cloud Storage",
            "category": "Utilities · Internet",
            "amount": 299.0,
            "due_date": "15 Oct, 2026",
            "days_left": 23,
            "icon": "wifi",
            "flexibility": "stoppable",
            "color": "secondary"
        }
    ]

def evaluate_affordability(query: str, requested_amount: float = None, user_id: str = "user_01"):
    """Runs the real decision engine on the requested purchase."""
    amt = requested_amount if (requested_amount and requested_amount > 0) else parse_amount_from_query(query)
    today_str = datetime.now().strftime("%Y-%m-%d")
    completion_date_str = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    prof = indexes.get_profile(user_id)
    u_events = indexes.get_events_for_user(user_id)
    u_msgs = indexes.get_messages_for_user(user_id)
    
    req_obj = Request(
        request_id=f"live_{int(datetime.now().timestamp())}",
        user_id=user_id,
        request_date=today_str,
        request_type="purchase",
        requested_amount=amt,
        desired_completion_date=completion_date_str,
        allows_partial_payment=True,
        request_text=query or f"Purchase of INR {amt:,.2f}"
    )
    
    # Custom provider options for this request amount
    opts = [
        PaymentOption("opt_full", req_obj.request_id, "full_payment", amt, 1, today_str, None, 0.0, amt),
        PaymentOption("opt_emi3", req_obj.request_id, "installments", round(amt / 3.0, 2), 3, today_str, 30.0, 0.0, amt),
        PaymentOption("opt_emi6", req_obj.request_id, "installments", round((amt * 1.05) / 6.0, 2), 6, today_str, 30.0, round(amt * 0.05, 2), round(amt * 1.05, 2)),
    ]
    
    safe_dec = safe_engine.evaluate_request(req_obj, prof, u_events, u_msgs)
    cand = optimizer.evaluate_request(req_obj, prof, u_events, opts, u_msgs)
    
    # Format verdict
    status = cand.affordability_status
    method = cand.recommended_payment_method
    
    if status == 'affordable_now':
        verdict_badge = "BUY NOW"
        verdict_color = "secondary"
        verdict_headline = f"Safe to buy today! Leaves your buffer 100% intact."
        verdict_sub = f"You have enough free liquid cash after reserving upcoming bills and your ₹{prof.minimum_balance_to_keep:,.0f} shield."
    elif status == 'affordable_with_plan':
        verdict_badge = "CHANGE PLAN"
        verdict_color = "primary"
        verdict_headline = f"Affordable with a smart payment plan."
        verdict_sub = f"Using {method.replace('_', ' ')} keeps your monthly buffer safe without risking overdraft."
    elif status == 'affordable_later':
        verdict_badge = "WAIT"
        verdict_color = "tertiary"
        verdict_headline = f"Buying this today could reduce your safety buffer below ₹{prof.minimum_balance_to_keep:,.0f}."
        verdict_sub = f"You don’t have to cancel your plans — just give your balance time to breathe until commitments clear."
    else:
        verdict_badge = "NOT AFFORDABLE"
        verdict_color = "error"
        verdict_headline = f"Not recommended within the 30-day forecast horizon."
        verdict_sub = f"This purchase exceeds your safe financial threshold and would compromise essential living expenses."
        
    safe_amt = safe_dec.amount_safe_to_pay
    shortfall = max(0.0, amt - safe_amt)
    earliest_date = safe_dec.earliest_date_for_full_payment or (datetime.now() + timedelta(days=26)).strftime("%Y-%m-%d")
    
    # Format date
    try:
        edt_obj = datetime.strptime(earliest_date, "%Y-%m-%d")
        formatted_date = edt_obj.strftime("%B %d, %Y")
        days_away = (edt_obj - datetime.now()).days
        timing_label = f"{formatted_date} · In {max(1, days_away)} days"
    except Exception:
        formatted_date = "Next month"
        timing_label = "Optimal window after next salary"

    # Human breakdown
    breakdown = {
        "purchase_price": amt,
        "safe_today": safe_amt,
        "shortfall_today": shortfall,
        "protected_buffer": prof.minimum_balance_to_keep,
        "commitments_sum": 12499.0,
        "current_balance": prof.current_available_balance,
        "safe_date": formatted_date,
        "timing_label": timing_label
    }
    
    # 4-Factor Engine Breakdown
    factors = [
        {
            "name": "Upcoming commitments",
            "desc": "Rent, bike EMI, electricity",
            "amount": "₹12,499",
            "meta": "Due in 14 days",
            "icon": "calendar_clock",
            "type": "warning"
        },
        {
            "name": "Safety buffer to protect",
            "desc": "Untouchable emergency pool",
            "amount": f"₹{prof.minimum_balance_to_keep:,.0f}",
            "meta": "Locked Safe",
            "icon": "shield",
            "type": "secondary"
        },
        {
            "name": "Current safe-to-spend",
            "desc": "Liquid buffer free today",
            "amount": f"₹{safe_amt:,.0f}",
            "meta": "Available now",
            "icon": "account_balance_wallet",
            "type": "primary"
        },
        {
            "name": "Target item price",
            "desc": f"Shortfall gap: ₹{shortfall:,.0f}",
            "amount": f"₹{amt:,.0f}",
            "meta": f"-₹{shortfall:,.0f} needed" if shortfall > 0 else "Fully covered",
            "icon": "shopping_bag",
            "type": "error" if shortfall > 0 else "secondary"
        }
    ]
    
    # Alternatives / What-If scenarios
    alternatives = [
        {
            "id": "alt_wait",
            "title": f"Wait until {formatted_date}",
            "tag": "Safest · 0% stress",
            "desc": "Zero debt, zero interest, and your emergency buffer remains 100% intact throughout the month.",
            "amount": f"₹{amt:,.0f}",
            "timing": f"In {max(1, (datetime.strptime(earliest_date, '%Y-%m-%d') - datetime.now()).days)} days",
            "is_recommended": (status == 'affordable_later'),
            "icon": "schedule"
        },
        {
            "id": "alt_emi",
            "title": f"3-Month No-Cost EMI (₹{round(amt/3.0):,.0f}/mo)",
            "tag": "Balanced Runway",
            "desc": f"Spread the cost over 3 installments. Keeps monthly safe spend above ₹{safe_amt - round(amt/3.0):,.0f}.",
            "amount": f"₹{round(amt/3.0):,.0f} / mo",
            "timing": "Starts today",
            "is_recommended": (status == 'affordable_with_plan'),
            "icon": "pie_chart"
        },
        {
            "id": "alt_pivot",
            "title": f"Budget Alternative / Refurbished (₹{round(amt * 0.75):,.0f})",
            "tag": "Affordable sooner",
            "desc": f"Save ₹{round(amt * 0.25):,.0f} upfront with certified warranty & minimal day-to-day performance difference.",
            "amount": f"₹{round(amt * 0.75):,.0f}",
            "timing": "Safe in 5 days",
            "is_recommended": False,
            "icon": "savings"
        },
        {
            "id": "alt_full",
            "title": f"Pay ₹{amt:,.0f} in full today",
            "tag": "High Risk",
            "desc": f"Wipes out your safe margin and dips into your ₹{prof.minimum_balance_to_keep:,.0f} buffer.",
            "amount": f"₹{amt:,.0f}",
            "timing": "Today",
            "is_recommended": (status == 'affordable_now'),
            "icon": "credit_card"
        }
    ]

    return {
        "request_id": req_obj.request_id,
        "query": query,
        "requested_amount": amt,
        "verdict_badge": verdict_badge,
        "verdict_color": verdict_color,
        "verdict_headline": verdict_headline,
        "verdict_sub": verdict_sub,
        "affordability_status": status,
        "recommended_payment_method": method,
        "amount_safe_to_pay": safe_amt,
        "earliest_date_for_full_payment": earliest_date,
        "payment_plan": cand.payment_plan,
        "spending_changes_needed": cand.spending_changes_needed,
        "decision_explanation": cand.explanation,
        "breakdown": breakdown,
        "factors": factors,
        "alternatives": alternatives
    }


class AffordIQRequestHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS and PWA friendly headers
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        # API Routes
        if path == "/api/profile":
            user_id = query.get("user_id", [current_user_id])[0]
            prof = indexes.get_profile(user_id)
            data = {
                "user_id": user_id,
                "user_name": user_custom_settings["user_name"],
                "home_currency": prof.home_currency if prof else "INR",
                "current_available_balance": prof.current_available_balance if prof else 25949.0,
                "minimum_balance_to_keep": prof.minimum_balance_to_keep if prof else 5000.0,
                "monthly_income": user_custom_settings["monthly_income"],
                "safe_to_spend_today": 8450.0,
                "upcoming_commitments": 12499.0,
                "settings": user_custom_settings
            }
            self.send_json(data)
            return

        elif path == "/api/transactions":
            user_id = query.get("user_id", [current_user_id])[0]
            data = get_demo_transactions(user_id)
            self.send_json(data)
            return

        elif path == "/api/commitments":
            user_id = query.get("user_id", [current_user_id])[0]
            data = get_demo_commitments(user_id)
            self.send_json(data)
            return

        elif path == "/api/dataset_users":
            users = []
            for p in profiles_list[:25]:
                users.append({
                    "user_id": p.user_id,
                    "home_currency": p.home_currency,
                    "current_balance": p.current_available_balance,
                    "min_balance": p.minimum_balance_to_keep
                })
            self.send_json(users)
            return

        # Serve static web files
        web_dir = os.path.join(repo_root, "web")
        req_file = path.lstrip("/")
        if not req_file or req_file == "":
            req_file = "index.html"
            
        file_path = os.path.join(web_dir, req_file)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.end_headers()
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
            return
            
        # Fallback to index.html for SPA routing
        index_path = os.path.join(web_dir, "index.html")
        if os.path.exists(index_path):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            with open(index_path, "rb") as f:
                self.wfile.write(f.read())
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"404 Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            payload = json.loads(body.decode('utf-8'))
        except Exception:
            payload = {}

        if path == "/api/evaluate":
            query_text = payload.get("query", "Can I buy a ₹40,000 laptop?")
            amt = payload.get("amount", None)
            u_id = payload.get("user_id", current_user_id)
            
            result = evaluate_affordability(query_text, amt, u_id)
            self.send_json(result)
            return

        elif path == "/api/settings":
            for k, v in payload.items():
                if k in user_custom_settings:
                    user_custom_settings[k] = v
            self.send_json({"status": "success", "settings": user_custom_settings})
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"404 Not Found")

    def send_json(self, data):
        body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(port=8000):
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, AffordIQRequestHandler)
    print(f"================================================================")
    print(f"  Afford IQ Mobile Prototype Running Successfully!")
    print(f"  Local Web / Mobile URL: http://localhost:{port}")
    print(f"  Network Phone URL:     http://<YOUR_LOCAL_IP>:{port}")
    print(f"================================================================")
    httpd.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
