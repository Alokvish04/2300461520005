import requests
from typing import List, Dict
import datetime

import logging
from logging_utils import get_logger  # your logging middleware wrapper

logger = get_logger("priority_inbox")

def get_type_weight(notification_type: str) -> int:
    type_map = {
        "Placement": 3,
        "Result": 2,
        "Event": 1,
    }
    return type_map.get(notification_type, 0)

def fetch_notifications(api_url: str) -> List[Dict]:
    logger.info("Fetching notifications from API", url=api_url)
    response = requests.get(api_url)
    if response.status_code != 200:
        logger.error("API request failed", status_code=response.status_code, url=api_url)
        raise RuntimeError(f"API request failed with status {response.status_code}")

    logger.info("Successfully fetched notifications", count=len(response.json()))
    return response.json()

def compute_priority_score(notification: Dict) -> float:
    type_weight = get_type_weight(notification.get("notificationType", ""))
    created_at = notification.get("createdAt", "")

    try:
        dt = datetime.datetime.fromisoformat(created_at)
        timestamp = dt.timestamp()
    except Exception as e:
        logger.warning("Failed to parse createdAt", createdAt=created_at, error=str(e))
        timestamp = 0

    max_timestamp = datetime.datetime.now().timestamp()
    recency_factor = timestamp / max_timestamp if max_timestamp > 0 else 0

    priority_score = type_weight * (1 + recency_factor)
    return priority_score

def get_top_n_unread_notifications(
    notifications: List[Dict],
    n: int = 10
) -> List[Dict]:
    logger.info("Filtering unread notifications")
    unread = [
        nb for nb in notifications
        if nb.get("isRead") is False
    ]
    logger.info("Filtered unread notifications", count=len(unread))

    for nb in unread:
        nb["_priority_score"] = compute_priority_score(nb)

    logger.info("Sorting notifications by priority score")
    sorted_notifications = sorted(
        unread,
        key=lambda nb: nb["_priority_score"],
        reverse=True
    )

    top_n = sorted_notifications[:n]
    logger.info("Selected top N notifications", n=n, count=len(top_n))
    return top_n

def main():
    api_url = "http://4.224.186.213/evaluation-service/notifications"
    logger.info("Starting Priority Inbox")

    notifications = fetch_notifications(api_url)
    top_10 = get_top_n_unread_notifications(notifications, n=10)

    logger.info("Top 10 unread priority notifications:")
    for i, nb in enumerate(top_10, start=1):
        logger.info(
            f"#{i}",
            id=nb.get("id"),
            title=nb.get("title"),
            type=nb.get("notificationType"),
            priority_score=nb["_priority_score"],
            createdAt=nb.get("createdAt")
        )

    return top_10

if __name__ == "__main__":
    main()
