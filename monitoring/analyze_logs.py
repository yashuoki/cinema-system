import os
import re
from collections import Counter

LOG_DIRS = {
    "ticket": "../ticket-service/logs",
    "payment": "../payment-service/logs",
}

metrics = Counter()

patterns = {
    "reserved": re.compile(r"RESERVED"),
    "sold": re.compile(r"SOLD|confirmed"),
    "cancelled": re.compile(r"CANCELLED"),
    "payment_success": re.compile(r"SUCCESS"),
    "payment_failed": re.compile(r"FAILED"),
}

def analyze_logs():
    for service, path in LOG_DIRS.items():
        if not os.path.exists(path):
            continue

        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            with open(file_path, "r") as f:
                for line in f:
                    for key, pattern in patterns.items():
                        if pattern.search(line):
                            metrics[key] += 1

if name == "main":
    analyze_logs()

    print("=== Monitoring metrics ===")
    print(f"Reserved tickets: {metrics['reserved']}")
    print(f"Sold tickets: {metrics['sold']}")
    print(f"Cancelled tickets: {metrics['cancelled']}")
    print(f"Successful payments: {metrics['payment_success']}")
    print(f"Failed payments: {metrics['payment_failed']}")