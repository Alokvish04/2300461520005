import requests
from typing import List, Dict
import datetime
import logging
import os

# Simple logger setup to mimic structured logging / middleware usage
def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


logger = get_logger("priority_inbox")


def get_type_weight(notification_type: str) -> int:
    """
    Assign weight based on notification type.
    placement > result > event
    """
    type_map = {
        "Placement": 3,
        "Result": 2,
        "Event": 1,
    }
    return type_map.get(notification_type, 0)


def fetch_notifications(api_url: str) -> List[Dict]:
    """
    Fetch notifications from the API.
    Uses logging for request tracing and bearer token auth.
    """
    # Read bearer token from environment variable (DO NOT hard-code it)
    access_token = os.getenv("NOTIFICATION_API_TOKEN")

    headers = {}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    # Log headers in a safe way (mask the token)
    safe_headers = {
        k: ("***" if k.lower() == "authorization" else v)
        for k, v in headers.items()
    }
    logger.info(
        "Fetching notifications from API "
        f"url={api_url} has_token={bool(access_token)} headers={safe_headers}"
    )

    response = requests.get(api_url, headers=headers)

    if response.status_code != 200:
        logger.error(
            "API request failed "
            f"status_code={response.status_code} url={api_url}"
        )
        raise RuntimeError(f"API request failed with status {response.status_code}")

    data = response.json()
    logger.info(f"Successfully fetched notifications count={len(data)}")
    return data


def compute_priority_score(notification: Dict) -> float:
    """
    Compute priority score based on type weight and recency.
    """
    type_weight = get_type_weight(notification.get("notificationType", ""))
    created_at = notification.get("createdAt", "")

    try:
        # Expecting ISO 8601, e.g. "2026-06-11T08:00:00Z" or without Z
        created_at_clean = created_at.rstrip("Z")
        dt = datetime.datetime.fromisoformat(created_at_clean)
        timestamp = dt.timestamp()
    except Exception as e:
        logger.warning(
            "Failed to parse createdAt "
            f"createdAt={created_at} error={e}"
        )
        timestamp = 0.0

    now_ts = datetime.datetime.now().timestamp()
    recency_factor = timestamp / now_ts if now_ts > 0 else 0.0

    priority_score = type_weight * (1.0 + recency_factor)
    return priority_score


def get_top_n_unread_notifications(
    notifications: List[Dict],
    n: int = 10
) -> List[Dict]:
    """
    Filter unread notifications, compute priority score,
    sort by score descending, and return top n.
    """
    logger.info("Filtering unread notifications")
    unread = [
        nb for nb in notifications
        if nb.get("isRead") is False
    ]
    logger.info(f"Filtered unread notifications count={len(unread)}")

    for nb in unread:
        nb["_priority_score"] = compute_priority_score(nb)

    logger.info("Sorting notifications by priority score (desc)")
    sorted_notifications = sorted(
        unread,
        key=lambda nb: nb["_priority_score"],
        reverse=True
    )

    top_n = sorted_notifications[:n]
    logger.info(f"Selected top N notifications n={n} actual_count={len(top_n)}")
    return top_n


def main():
    api_url = "http://4.224.186.213/evaluation-service/notifications"
    logger.info("Starting Priority Inbox computation")

    notifications = fetch_notifications(api_url)
    top_10 = get_top_n_unread_notifications(notifications, n=10)

    logger.info("Top 10 unread priority notifications:")
    for i, nb in enumerate(top_10, start=1):
        logger.info(
            f"#{i} "
            f"id={nb.get('id')} "
            f"title={nb.get('title')} "
            f"type={nb.get('notificationType')} "
            f"score={nb.get('_priority_score')} "
            f"createdAt={nb.get('createdAt')}"
        )

    return top_10


if __name__ == "__main__":
    main()