"""
Forecast Diagnostics Tool for HackerRank Orchestrate: Buy or Wait? (Phase 2)
Executes Phase 2 timeline simulation and prints detailed cash flow reports for users/requests.
"""
import sys
import os
import argparse

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
code_dir = os.path.join(repo_root, "code")
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from data_loader import DataLoader
from indexes import DatasetIndexes
from currency import CurrencyConverter
from forecaster import CashFlowForecaster


def inspect_request_forecast(request_id: str = "request_01"):
    dataset_dir = os.path.join(repo_root, "dataset")
    loader = DataLoader(dataset_dir)

    requests = loader.load_requests("requests.csv")
    sample_dict = loader.load_sample_requests("sample_requests.csv")
    sample_requests = sample_dict['requests']
    all_requests = requests + sample_requests

    profiles = loader.load_financial_profiles("financial_profiles.csv")
    events = loader.load_financial_events("financial_events.csv")
    messages = loader.load_messages("messages.csv")
    exchange_rates = loader.load_exchange_rates("exchange_rates.csv")

    indexes = DatasetIndexes(profiles, events, [], messages, [], exchange_rates)
    currency_converter = CurrencyConverter(exchange_rates)
    forecaster = CashFlowForecaster(currency_converter)

    req = next((r for r in all_requests if r.request_id == request_id), None)
    if not req:
        print(f"Error: Request {request_id} not found.")
        return False

    prof = indexes.get_profile(req.user_id)
    user_events = indexes.get_events_for_user(req.user_id)
    user_msgs = indexes.get_messages_for_user(req.user_id)

    res = forecaster.forecast_90_days(prof, user_events, user_msgs, req.request_date)

    print("==================================================")
    print(f" FORECAST DIAGNOSTICS FOR REQUEST {req.request_id}")
    print("==================================================")
    print(f"User ID: {req.user_id}")
    print(f"Home Currency: {res.home_currency}")
    print(f"Request Date: {req.request_date}")
    print(f"Requested Amount: {req.requested_amount:,.2f} {res.home_currency}")
    print(f"Current Available Balance: {prof.current_available_balance:,.2f} {res.home_currency}")
    print(f"Starting Safe Balance (after pending debits): {res.starting_balance:,.2f} {res.home_currency}")
    print(f"Minimum Balance to Keep: {res.minimum_balance_to_keep:,.2f} {res.home_currency}")
    print(f"Minimum Projected Balance (90 days): {res.minimum_projected_balance:,.2f} {res.home_currency} on {res.minimum_projected_date}")

    safety_margin = res.minimum_projected_balance - res.minimum_balance_to_keep
    print(f"Lowest Projected Safety Margin: {safety_margin:,.2f} {res.home_currency}")

    print("\n--- ASSUMPTIONS & MESSAGE FACTS USED ---")
    if res.assumptions_used:
        for a in res.assumptions_used:
            print(f"  * {a}")
    else:
        print("  None")

    print("\n--- 90-DAY CASH FLOW SUMMARY ---")
    print(f"Total Projected Inflows: +{res.projected_inflows_total:,.2f} {res.home_currency}")
    print(f"Total Projected Outflows: -{res.projected_outflows_total:,.2f} {res.home_currency}")

    print("\n--- SAMPLE DAILY BALANCES ---")
    dates_sorted = sorted(res.daily_balances.keys())
    sample_dates = [dates_sorted[0], dates_sorted[15], dates_sorted[30], dates_sorted[45], dates_sorted[60], dates_sorted[75], dates_sorted[-1]]
    for d in sample_dates:
        print(f"  {d}: {res.daily_balances[d]:,.2f} {res.home_currency}")

    print("==================================================")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--request_id", default="request_01", help="Request ID to inspect")
    args = parser.parse_args()
    inspect_request_forecast(args.request_id)
