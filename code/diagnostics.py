"""
Diagnostics Tool for HackerRank Orchestrate: Buy or Wait? (Phase 1)
Executes data loading, dataset integrity checks, and prints comprehensive Phase 1 summary.
"""
import sys
import os
from collections import Counter

# Add repo root and code folder to python path
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
code_dir = os.path.join(repo_root, "code")
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from data_loader import DataLoader
from indexes import DatasetIndexes
from validation.data_integrity import DataIntegrityValidator
from event_classifier import EventClassifier
from image_resolver import ImageResolver
from message_resolver import MessageResolver
from payment_options import PaymentOptionResolver


def run_diagnostics():
    dataset_dir = os.path.join(repo_root, "dataset")

    print("==================================================")
    print(" HACKERRANK ORCHESTRATE - PHASE 1 DIAGNOSTICS")
    print("==================================================")
    print(f"Dataset Directory: {dataset_dir}")

    # 1. Load Datasets
    loader = DataLoader(dataset_dir)
    requests = loader.load_requests("requests.csv")
    sample_dict = loader.load_sample_requests("sample_requests.csv")
    sample_requests = sample_dict['requests']
    profiles = loader.load_financial_profiles("financial_profiles.csv")
    events = loader.load_financial_events("financial_events.csv")
    payment_options = loader.load_request_payment_options("request_payment_options.csv")
    messages = loader.load_messages("messages.csv")
    images = loader.load_images("images.csv")
    exchange_rates = loader.load_exchange_rates("exchange_rates.csv")

    # 2. Build Indexes
    indexes = DatasetIndexes(profiles, events, payment_options, messages, images, exchange_rates)

    # 3. Data Integrity Validation
    validator = DataIntegrityValidator(
        dataset_dir, requests, profiles, events,
        payment_options, messages, images, exchange_rates,
        sample_requests=sample_requests
    )
    errors, warnings = validator.validate_all()

    # 4. Event Classification Counts
    classifier = EventClassifier()
    status_class_counts = Counter()
    dir_class_counts = Counter()
    for e in events:
        cl = classifier.classify_event(e)
        status_class_counts[cl.category] += 1
        dir_class_counts[cl.direction_category] += 1

    # 5. Image & Missing Amount Statistics
    missing_amount_events = [e for e in events if e.amount is None]
    img_resolver = ImageResolver(dataset_dir, images)
    all_imgs_exist, missing_img_files = img_resolver.verify_all_images_exist()
    image_linked_events = [e for e in missing_amount_events if img_resolver.get_image_for_event(e.event_id)]

    # 6. Payment Options Coverage
    req_ids_with_options = set(opt.request_id for opt in payment_options)

    # Print Summary Report
    print("\n--- DATASET COUNTS ---")
    print(f"Evaluation Requests (requests.csv): {len(requests)}")
    print(f"Sample Requests (sample_requests.csv): {len(sample_requests)}")
    print(f"User Profiles (financial_profiles.csv): {len(profiles)}")
    print(f"Financial Events (financial_events.csv): {len(events)}")
    print(f"Payment Options (request_payment_options.csv): {len(payment_options)}")
    print(f"Messages (messages.csv): {len(messages)}")
    print(f"Images (images.csv): {len(images)}")
    print(f"Exchange Rates (exchange_rates.csv): {len(exchange_rates)}")

    print("\n--- EVENT DISTRIBUTIONS ---")
    print(f"Event Types: {dict(Counter(e.event_type for e in events))}")
    print(f"Event Raw Statuses: {dict(Counter(e.status for e in events))}")
    print(f"Event Flexibilities: {dict(Counter(e.flexibility for e in events))}")
    print(f"Supported Currencies: {sorted(list(set(p.home_currency for p in profiles)))}")

    print("\n--- CLASSIFIER CATEGORIES ---")
    print("Status Classifications:")
    for cat, count in status_class_counts.items():
        print(f"  - {cat}: {count}")

    print("Direction Classifications:")
    for dcat, count in dir_class_counts.items():
        print(f"  - {dcat}: {count}")

    print("\n--- MISSING AMOUNTS & IMAGES ---")
    print(f"Financial Events with Missing Amount (NaN): {len(missing_amount_events)}")
    print(f"Missing Amount Events Linked to Images: {len(image_linked_events)}")
    print(f"All {len(images)} PNG Image Files Exist on Disk: {all_imgs_exist}")
    if not all_imgs_exist:
        print(f"  Missing image files: {missing_img_files}")

    print("\n--- PAYMENT OPTIONS COVERAGE ---")
    print(f"Total Requests with Payment Options: {len(req_ids_with_options)} / {len(requests) + len(sample_requests)}")

    print("\n--- DATA INTEGRITY VALIDATION RESULT ---")
    print(f"Total Errors Found: {len(errors)}")
    print(f"Total Warnings Found: {len(warnings)}")
    if errors:
        print("ERRORS DETECTED:")
        for err in errors[:10]:
            print(f"  [ERROR] {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors.")
    else:
        print("PASSED: Clean dataset integrity. Zero data integrity errors!")

    print("==================================================")
    return len(errors) == 0


if __name__ == "__main__":
    success = run_diagnostics()
    sys.exit(0 if success else 1)
