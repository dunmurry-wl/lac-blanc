#!/usr/bin/env python3
"""Check Refuge du Lac Blanc's reservation badge and notify via ntfy once.

Run locally with: python check_reservations.py
Test notifications: python check_reservations.py --test-notification
"""

import argparse
import os
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SITE_URL = "https://refugelacblanc.com/en/"
BOOKING_URL = f"{SITE_URL}#calendar--bookings"


def get_reservation_state(html: str) -> str:
    """Return 'closed' or 'changed'; raise if the HTML is unexpected.

    'changed' intentionally does not claim that bookings are definitely open.
    """
    soup = BeautifulSoup(html, "html.parser")
    badges = soup.select("a.reservation-badge")
    if not badges:
        raise ValueError("Reservation badge not found; website markup may have changed")

    closed_flags = []
    for badge in badges:
        label = badge.select_one("span.reservation-badge__text")
        if label is None or not label.get_text(" ", strip=True):
            raise ValueError("Reservation badge text missing; cannot determine status")

        text = " ".join(label.stripped_strings).casefold()
        closed_flags.append(
            "is--closed-reservations" in badge.get("class", [])
            or "reservations closed" in text
        )

    if all(closed_flags):
        return "closed"
    if any(closed_flags):
        raise ValueError("Reservation badges disagree; not sending a potentially false alert")
    return "changed"


def send_notification(test: bool = False) -> None:
    topic_url = os.environ.get("NTFY_TOPIC_URL")
    if not topic_url or not topic_url.startswith("https://"):
        raise ValueError("NTFY_TOPIC_URL must be set to an HTTPS ntfy topic URL")

    title = "Lac Blanc monitor test" if test else "Lac Blanc reservations: status changed"
    message = (
        "Test notification: the monitor can send alerts."
        if test
        else (
            "The reservation badge no longer says 'Reservations closed'. "
            "Bookings may have opened. Check the site now:\n" + BOOKING_URL
        )
    )
    response = requests.post(
        topic_url,
        data=message.encode("utf-8"),
        headers={
            "Title": title,
            "Priority": "high",
            "Click": BOOKING_URL,
            "Tags": "calendar",
        },
        timeout=20,
    )
    response.raise_for_status()
    print("ntfy notification accepted by the server")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test-notification", action="store_true")
    args = parser.parse_args()

    if args.test_notification:
        send_notification(test=True)
        return

    response = requests.get(
        SITE_URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ReservationStatusMonitor/1.0)"},
        timeout=20,
    )
    response.raise_for_status()
    state = get_reservation_state(response.text)
    print(f"Reservation badge status: {state}")

    if state == "changed":
        # If publishing fails, the action fails and does NOT disable itself.
        send_notification()
        output_path = os.environ.get("GITHUB_OUTPUT")
        if output_path:
            with Path(output_path).open("a", encoding="utf-8") as output:
                output.write("notification_sent=true\n")


if __name__ == "__main__":
    main()
