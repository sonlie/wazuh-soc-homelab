import re
import os
import time
import json
import socket
import requests

from collections import defaultdict
from datetime import datetime, timedelta

LOG_FILE = "/var/log/auth.log"

HOSTNAME = socket.gethostname()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

FAILED_THRESHOLD = 2
TIME_WINDOW_MINUTES = 2

failed_attempts = defaultdict(list)
already_alerted = set()

pattern = re.compile(
    r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}).*from (\d+\.\d+\.\d+\.\d+)'
)

def write_alert(alert):

    with open("alerts.json", "a") as f:
        json.dump(alert, f)
        f.write("\n")


def send_discord(alert):

    if not WEBHOOK_URL:
        return

    payload = {
        "embeds": [
            {
                "title": "SSH Brute Force Detected",
                "description": (
                    f"Host: {alert['hostname']}\n"
                    f"Source IP: {alert['source_ip']}"
                ),
                "fields": [
                    {
                        "name": "Severity",
                        "value": alert["severity"]
                    },
                    {
                        "name": "Failed Attempts",
                        "value": str(alert["failed_attempts"])
                    },
                    {
                        "name": "Success Time",
                        "value": alert["success_time"]
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            timeout=10
        )

        if response.status_code >= 400:
            print(
                f"Discord webhook failed: "
                f"{response.status_code}"
            )

    except Exception as e:
        print(f"Discord error: {e}")


def create_alert(ip, fail_count, success_time):

    return {
        "event_type": "ssh_bruteforce_success",
        "severity": "medium",
        "hostname": HOSTNAME,
        "source_ip": ip,
        "failed_attempts": fail_count,
        "success_time": str(success_time)
    }


def process(line):

    match = pattern.search(line)

    if not match:
        return

    event_time = datetime.fromisoformat(
        match.group(1)
    )

    ip = match.group(2)

    if "Failed password" in line:

        failed_attempts[ip].append(
            event_time
        )

        return

    if "Accepted password" not in line:
        return

    recent_fails = [

        x

        for x in failed_attempts[ip]

        if event_time - x
        <= timedelta(
            minutes=TIME_WINDOW_MINUTES
        )

    ]

    failed_attempts[ip] = recent_fails

    if len(recent_fails) < FAILED_THRESHOLD:
        return

    alert_key = (
        ip,
        event_time.strftime(
            "%Y-%m-%d-%H-%M"
        )
    )

    if alert_key in already_alerted:
        return

    already_alerted.add(
        alert_key
    )

    alert = create_alert(
        ip,
        len(recent_fails),
        event_time
    )

    print(
        f"[ALERT] "
        f"{ip} "
        f"{len(recent_fails)} fails"
    )

    write_alert(alert)

    send_discord(alert)


def follow_log():

    with open(LOG_FILE, "r") as f:

        f.seek(0, 2)

        while True:

            line = f.readline()

            if not line:

                time.sleep(0.2)

                continue

            process(line)


if __name__ == "__main__":

    print(
        f"Starting SSH Detection Engine "
        f"on {HOSTNAME}"
    )

    follow_log()
