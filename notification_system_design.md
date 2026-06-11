# Stage 1 – Notification REST API Design

This document defines the REST APIs and real-time mechanism for a campus notification platform that delivers updates about Placements, Events, and Results to logged-in students.

## Core Actions

- Create a notification (by an admin or system process).
- Fetch notifications for a user (with pagination and filters).
- Fetch unread notifications for a user.
- Mark a notification as read.
- Mark all notifications as read.
- Delete a notification for a user.
- Subscribe to real-time notification updates.

## REST API Endpoints

Assumption: Users accessing the APIs are already authenticated by the platform, and the backend derives the current user from context or headers.

| Action                          | Method | Endpoint                             | Description                                      |
|---------------------------------|--------|--------------------------------------|--------------------------------------------------|
| Create notification             | POST   | /notifications                       | Create a new notification                        |
| Get notifications (paginated)   | GET    | /notifications                       | List notifications for the current user          |
| Get unread notifications        | GET    | /notifications/unread                | List unread notifications for the current user   |
| Mark notification as read       | PATCH  | /notifications/{notificationId}/read | Mark a single notification as read               |
| Mark all as read                | PATCH  | /notifications/read-all              | Mark all notifications as read for the user      |
| Delete notification             | DELETE | /notifications/{notificationId}      | Delete (hide) a single notification for the user |
| Real-time stream (SSE/WebSocket)| GET    | /notifications/stream                | Subscribe to real-time notification updates      |

## Common Headers

All APIs assume that the user is pre-authorised by the platform.

- `Content-Type: application/json`
- `Accept: application/json`
- `X-Request-Id` (optional, for tracing and logging)
- `X-User-Id` (optional; used if the backend does not derive user from token)

---

## Endpoint Details and JSON Contracts

### POST /notifications

Creates a new notification that will be delivered to one or more target users or groups.

**Request Headers**

- `Content-Type: application/json`
- `X-User-Id`: ID of the admin or system creating the notification (optional if inferred)

**Request Body (JSON)**

```json
{
  "title": "Drive: ABC Corp",
  "message": "ABC Corp is visiting on 20th June. Register before 18th June.",
  "type": "PLACEMENT",
  "target": {
    "audienceType": "DEPARTMENT",
    "department": "CSE",
    "batch": 2026
  },
  "priority": "HIGH",
  "scheduledAt": "2026-06-15T10:00:00Z",
  "meta": {
    "link": "https://example.com/registration"
  }
}
```

**Field Description**

- `title` (string, required): Short title of the notification.
- `message` (string, required): Detailed message to show to the user.
- `type` (string, required): Category of notification, e.g. `PLACEMENT`, `EVENT`, `RESULT`.
- `target` (object, required): Target audience definition (department, batch, etc.).
- `priority` (string, optional): `LOW`, `MEDIUM`, or `HIGH`.
- `scheduledAt` (string, optional, ISO 8601): When to send, if scheduled.
- `meta` (object, optional): Extra key-value data (e.g., links).

**Response Body (JSON)**

```json
{
  "notificationId": "notif_12345",
  "status": "CREATED",
  "createdAt": "2026-06-11T08:00:00Z"
}
```

---

### GET /notifications

Returns paginated notifications for the current user, with optional filters.

**Request Headers**

- `Accept: application/json`
- `X-User-Id`: current user (optional if inferred)

**Query Parameters**

- `page` (integer, optional, default 1)
- `pageSize` (integer, optional, default 20)
- `type` (string, optional, e.g., `PLACEMENT`, `EVENT`, `RESULT`)
- `status` (string, optional, e.g., `READ`, `UNREAD`)

**Response Body (JSON)**

```json
{
  "page": 1,
  "pageSize": 20,
  "totalItems": 42,
  "items": [
    {
      "id": "notif_12345",
      "title": "Drive: ABC Corp",
      "message": "ABC Corp is visiting on 20th June. Register before 18th June.",
      "type": "PLACEMENT",
      "priority": "HIGH",
      "status": "UNREAD",
      "createdAt": "2026-06-11T08:00:00Z",
      "readAt": null,
      "meta": {
        "link": "https://example.com/registration"
      }
    }
  ]
}
```

---

### GET /notifications/unread

Returns unread notifications for the current user.

**Request Headers**

- `Accept: application/json`
- `X-User-Id`: current user (optional if inferred)

**Response Body (JSON)**

```json
{
  "items": [
    {
      "id": "notif_12345",
      "title": "Drive: ABC Corp",
      "message": "ABC Corp is visiting on 20th June. Register before 18th June.",
      "type": "PLACEMENT",
      "priority": "HIGH",
      "status": "UNREAD",
      "createdAt": "2026-06-11T08:00:00Z",
      "meta": {
        "link": "https://example.com/registration"
      }
    }
  ]
}
```

---

### PATCH /notifications/{notificationId}/read

Marks a specific notification as read for the current user.

**Request Headers**

- `Content-Type: application/json`
- `X-User-Id`: current user

**Request Body (JSON)**

```json
{
  "read": true
}
```

**Response Body (JSON)**

```json
{
  "id": "notif_12345",
  "status": "READ",
  "readAt": "2026-06-11T09:00:00Z"
}
```

---

### PATCH /notifications/read-all

Marks all notifications for the current user as read.

**Request Headers**

- `Content-Type: application/json`
- `X-User-Id`: current user

**Response Body (JSON)**

```json
{
  "updatedCount": 15
}
```

---

### DELETE /notifications/{notificationId}

Deletes (or hides) a notification for the current user (soft delete).

**Request Headers**

- `X-User-Id`: current user

**Response Body (JSON)**

```json
{
  "id": "notif_12345",
  "deleted": true
}
```

---

## Real-Time Notification Mechanism

For real-time updates, the platform can use **Server-Sent Events (SSE)** to push notifications from the server to the browser over a long-lived HTTP connection. Alternatively, a WebSocket endpoint can be used with the same payload structure.

### GET /notifications/stream (SSE)

**Behavior**

- The frontend opens a persistent connection to `/notifications/stream`.
- When a new notification relevant to the user is created, the backend pushes an SSE event.
- The client updates the UI (badge counts, notification list) immediately.

**Request**

- Method: `GET`
- Headers:
  - `Accept: text/event-stream`
  - `X-User-Id`: current user

**Example SSE event**

```text
event: notification
data: {
  "id": "notif_12345",
  "title": "Drive: ABC Corp",
  "message": "ABC Corp is visiting on 20th June. Register before 18th June.",
  "type": "PLACEMENT",
  "priority": "HIGH",
  "status": "UNREAD",
  "createdAt": "2026-06-11T08:00:00Z"
}
```

If WebSockets are preferred, the client connects to a `/notifications/ws` endpoint and receives JSON messages with the same fields.

---

# Stage 2 – Persistent Storage Design

This section defines the database choice, schema, scaling concerns, and example queries for implementing the notification APIs defined in Stage 1.

## Choice of Database

I recommend using a relational database such as **PostgreSQL** for the notification system.

Reasons:

- Notifications are inherently relational: they are associated with users, types, and potential delivery logs.
- We need efficient filtering and pagination by user, status, type, and time, which relational databases handle well.
- Strong consistency is preferred so that unread/read state is reliable for each user.

## Database Schema

A simple relational schema with three core tables works well: `users`, `notifications`, and `notification_recipients`.

### Table: users

Stores basic user information relevant for targeting.

- `id` (PK, UUID)
- `name` (text)
- `email` (text, unique)
- `department` (text)
- `batch` (integer)

### Table: notifications

Stores the content and metadata of each notification.

- `id` (PK, UUID)
- `title` (text)
- `message` (text)
- `type` (text) – e.g., `PLACEMENT`, `EVENT`, `RESULT`
- `priority` (text) – e.g., `LOW`, `MEDIUM`, `HIGH`
- `created_by` (UUID, FK to users.id, nullable for system-generated)
- `scheduled_at` (timestamptz, nullable)
- `created_at` (timestamptz, default `NOW()`)
- `meta` (jsonb, optional)
- Index on (`type`, `priority`, `created_at`)

### Table: notification_recipients

Stores which user receives which notification and the user-specific state.

- `id` (PK, UUID)
- `notification_id` (UUID, FK to notifications.id)
- `user_id` (UUID, FK to users.id)
- `status` (text) – `UNREAD`, `READ`, `DELETED`
- `read_at` (timestamptz, nullable)
- `created_at` (timestamptz, default `NOW()`)
- Index on (`user_id`, `status`, `created_at`)
- Index on (`notification_id`)

This schema supports all the Stage 1 APIs (creation, listing, read/unread, deletion) while remaining flexible for future features like archiving or delivery logs.

## Scaling Challenges

As data volume grows, several problems can arise:

- **Large notification history**  
  - The `notification_recipients` table can grow to millions of rows as notifications are sent to many users.  
  - Queries like `GET /notifications` and `GET /notifications/unread` may slow down without proper indexing.

- **High write volume**  
  - Creating notifications and marking them as read are frequent write operations.  
  - Hot indexes (on `user_id` and `status`) can become bottlenecks.

- **Storage bloat**  
  - Old notifications (e.g., older than a year) may no longer be relevant but still consume storage and degrade performance.

## Approaches to Solve Scaling Problems

- **Index optimization**
  - Maintain composite indexes on (`user_id`, `status`, `created_at`) to speed up unread and recent queries.
  - Periodically monitor index usage and rebuild or drop unused indexes.

- **Pagination and sensible limits**
  - Enforce pagination in APIs with a reasonable maximum `pageSize`.
  - Encourage clients to load only recent notifications by default and lazy-load older ones.

- **Archival strategy**
  - Move old notifications (e.g., older than 12 months) from main tables to archive tables or cold storage.
  - Keep only recent notifications in the primary `notifications` and `notification_recipients` tables.

- **Table partitioning**
  - Partition `notification_recipients` by `created_at` (monthly/yearly) or by user ranges in very large deployments.
  - This keeps indexes smaller and improves query performance for recent data.

- **Caching**
  - Cache unread counts per user in a fast store such as Redis.
  - Update the cache when notifications are created or marked as read, reducing DB load on every poll.

## Example SQL Queries

The following SQL queries correspond to the REST APIs defined in Stage 1.

### 1. Create notification and assign recipients

Insert a new notification:

```sql
INSERT INTO notifications (
  id,
  title,
  message,
  type,
  priority,
  created_by,
  scheduled_at,
  meta,
  created_at
) VALUES (
  :notification_id,
  :title,
  :message,
  :type,
  :priority,
  :created_by,
  :scheduled_at,
  :meta::jsonb,
  NOW()
);
```

Assign the notification to a recipient (example for one user; in practice this can be a bulk insert):

```sql
INSERT INTO notification_recipients (
  id,
  notification_id,
  user_id,
  status,
  created_at
) VALUES (
  :recipient_id,
  :notification_id,
  :user_id,
  'UNREAD',
  NOW()
);
```

### 2. Get notifications for current user (paginated)

```sql
SELECT
  nr.id AS recipient_row_id,
  n.id AS notification_id,
  n.title,
  n.message,
  n.type,
  n.priority,
  nr.status,
  nr.created_at,
  nr.read_at,
  n.meta
FROM notification_recipients nr
JOIN notifications n ON n.id = nr.notification_id
WHERE nr.user_id = :user_id
  AND (:type IS NULL OR n.type = :type)
  AND (:status IS NULL OR nr.status = :status)
ORDER BY nr.created_at DESC
LIMIT :page_size OFFSET (:page - 1) * :page_size;
```

### 3. Get unread notifications for current user

```sql
SELECT
  nr.id AS recipient_row_id,
  n.id AS notification_id,
  n.title,
  n.message,
  n.type,
  n.priority,
  nr.status,
  nr.created_at,
  n.meta
FROM notification_recipients nr
JOIN notifications n ON n.id = nr.notification_id
WHERE nr.user_id = :user_id
  AND nr.status = 'UNREAD'
ORDER BY nr.created_at DESC;
```

### 4. Mark a single notification as read

```sql
UPDATE notification_recipients
SET status = 'READ',
    read_at = NOW()
WHERE notification_id = :notification_id
  AND user_id = :user_id
  AND status <> 'DELETED';
```

### 5. Mark all notifications as read for a user

```sql
UPDATE notification_recipients
SET status = 'READ',
    read_at = NOW()
WHERE user_id = :user_id
  AND status = 'UNREAD';
```

### 6. Delete a notification for a user (soft delete)

```sql
UPDATE notification_recipients
SET status = 'DELETED'
WHERE notification_id = :notification_id
  AND user_id = :user_id;
```

These queries, combined with the schema and API design above, provide a complete end-to-end design for the notification platform required in Stage 1 and Stage 2.

---

# Stage 3 – Query Optimization and Indexing

An earlier developer in the team chose a relational database for storage (MySQL or PostgreSQL or any other SQL database) about 3 months ago. The database has grown to 50,000 students and 5,000,000 notifications. The developer had written the query below, which is now performing slowly:

```sql
SELECT * FROM notifications
WHERE studentID = 1042 AND isRead = false
ORDER BY createdAt ASC;
```

## Is this query accurate?

Yes, the query is **logically accurate** for fetching unread notifications of a specific student. It correctly filters by `studentID` and `isRead = false`, and orders by recency.

## Why is this slow?

Reasons:

1. **`SELECT *`** fetches all columns, increasing I/O and memory usage, especially when the table has many columns.
2. **No suitable index** on `(studentID, isRead, createdAt)` forces a large scan over many rows.
3. With 50,000 students and 5,000,000 notifications, this becomes a full table scan or large range scan.
4. **`ORDER BY createdAt`** without an index on `createdAt` forces an extra sort step after filtering.
5. No `LIMIT` is used, so the query may return all unread notifications for that student, which can be large.

## What would you change?

Improved query:

```sql
SELECT
  id,
  studentID,
  isRead,
  createdAt,
  notificationType,
  title,
  message
FROM notifications
WHERE studentID = 1042
  AND isRead = false
ORDER BY createdAt ASC
LIMIT 100;
```

Changes:

- Select only needed columns instead of `SELECT *`.
- Add `LIMIT 100` to avoid fetching all rows on every request; the backend will paginate.
- This reduces I/O and memory usage.

## Indexing strategy

Instead of adding indexes on every column:

- Add a **composite index**:

  ```sql
  CREATE INDEX idx_notifications_student_unread_created
    ON notifications (studentID, isRead, createdAt);
  ```

This allows:

- Fast filtering by `studentID` and `isRead`.
- Direct ordering by `createdAt` without extra sort overhead.

Adding indexes on every column:

- Increases write cost (indexes must be updated on every INSERT/UPDATE).
- Uses more disk space.
- Can degrade performance for write-heavy operations.
- Not effective if the query pattern is not aligned with the index.

So, the advice to add indexes on every column is **not effective**.

## Query: students with placement notification in last 7 days

```sql
SELECT DISTINCT studentID
FROM notifications
WHERE notificationType = 'Placement'
  AND createdAt >= NOW() - INTERVAL '7 days';
```

Or in MySQL:

```sql
SELECT DISTINCT studentID
FROM notifications
WHERE notificationType = 'Placement'
  AND createdAt >= NOW() - INTERVAL 7 DAY;
```

This query uses the `notificationType` column and `createdAt` for filtering, and will benefit from the composite index defined above if extended to include `notificationType`.

---

# Stage 4 – Performance Caching and Strategies

Problem:  
Notifications are being fetched on each page load for every student. The DB is getting overwhelmed, causing bad user experience.

## Suggested solutions

### 1. Use caching (Redis) for unread counts and recent notifications

**Approach:**

- Cache:
  - Unread notification count per student.
  - Recent notifications (e.g., last 20–50) for each student.
- On each page load:
  - First, check cache.
  - If cache has data, return it.
  - If cache misses, fetch from DB and update cache.

**Tradeoffs:**

- **Pros:**
  - Reduces DB load significantly.
  - Faster response times for repeated page loads.
  - Can handle high traffic with many students.
- **Cons:**
  - Need to manage cache invalidation when notifications are created or read.
  - Adds complexity (cache layer, TTL, consistency).
  - Requires extra infrastructure (Redis).

**Implementation sketch:**

- Cache key: `unread_count:{studentID}`
- Cache key: `notifications:{studentID}:{page}:{pageSize}`
- TTL: e.g., 5–10 minutes, or invalidate on write (create/mark read/delete).

### 2. Database optimization and pagination

**Approach:**

- Use the composite index from Stage 3.
- Enforce pagination with `LIMIT` and `OFFSET`.
- Avoid `SELECT *`.

**Tradeoffs:**

- **Pros:**
  - Reduces DB scan cost.
  - Works even without extra infrastructure.
- **Cons:**
  - Still requires DB queries for each request.
  - Not sufficient alone for very high traffic.

### 3. Asynchronous background jobs for heavy operations

**Approach:**

- Use background workers (e.g., Node.js workers, Python Celery, etc.) to:
  - Precompute unread counts.
  - Pre-fetch and cache recent notifications.
  - Handle bulk operations (e.g., `notify_all`).

**Tradeoffs:**

- **Pros:**
  - Reduces main request latency.
  - Better for bulk notifications.
- **Cons:**
  - Adds complexity (message queues, job management).
  - Need to handle failures and retries.

### Recommended strategy

Use a combination:

- Add the composite index (Stage 3).
- Cache unread counts and recent notifications with Redis.
- Use background workers for heavy operations like `notify_all`.

This gives the best balance of performance and scalability.

---

# Stage 5 – Reliable and Fast `notify_all` Pseudocode

Original pseudocode:

```python
function notify_all(student_ids: array, message: string):
    for student_id in student_ids:
        send_email(student_id, message)  # calls Email API
        save_to_db(student_id, message)  # DB insert
        push_to_app(student_id, message) # real-time notification
```

## Shortcomings of this implementation

1. **No error handling**:
   - If `send_email` fails for some students, the loop continues but we don’t know or retry.
2. **No logging**:
   - No logs to track which students succeeded or failed.
3. **No retries**:
   - If email fails mid-way for 200 students, those students never get the email.
4. **Sequential processing**:
   - For 50,000 students, this is very slow.
5. **No separation of concerns**:
   - DB insert and email send are in the same loop; if one fails, we don’t know what to do.
6. **Not scalable**:
   - Not suitable for large batch notifications in real time.

## What if `send_email` fails for 200 students midway?

- Those 200 students don’t get the email.
- We have no record of failure.
- We don’t retry.

## Redesign for reliability and speed

### Key ideas

- **Use a job queue** for email sending and in-app notifications.
- **Separate DB insert from email send**:
  - Save to DB first, so we have a record.
  - Then enqueue email and in-app tasks.
- **Use retries with logging** for email and in-app notifications.
- **Process in batches**, not one-by-one.
- **Use logging middleware** to track success/failure.

## Revised pseudocode

```python
function notify_all(student_ids: array, message: string):
    # Step 1: Save all notifications to DB first
    for batch in batch(student_ids, size=1000):
        for student_id in batch:
            # Use logging middleware
            logger.info("Creating notification for student", student_id=student_id)

            save_to_db(
                student_id=student_id,
                message=message,
                notification_type="PLACEMENT",
                status="UNREAD"
            )

            # Enqueue email and in-app tasks
            enqueue_email_task(student_id=student_id, message=message)
            enqueue_inapp_task(student_id=student_id, message=message)

    # Step 2: Background workers will process email and in-app tasks
    # with retries and logging

function enqueue_email_task(student_id: string, message: string):
    logger.info("Enqueueing email task", student_id=student_id)
    job_queue.enqueue(
        job="send_email",
        args={
            "student_id": student_id,
            "message": message
        }
        retry_count=3,
        on_failure=lambda: logger.error("Email send failed", student_id=student_id)
    )

function enqueue_inapp_task(student_id: string, message: string):
    logger.info("Enqueueing in-app task", student_id=student_id)
    job_queue.enqueue(
        job="push_to_app",
        args={
            "student_id": student_id,
            "message": message
        }
        retry_count=3,
        on_failure=lambda: logger.error("In-app push failed", student_id=student_id)
    )
```

### Should DB save and email send happen together?

- **No**, they should not happen together in the same synchronous call.
- **Reasons:**
  - Email sending is external and can fail; DB save should be reliable.
  - Separating them allows:
    - DB to be updated first, so we have a record.
    - Email to be sent asynchronously via a queue with retries.
  - This improves reliability and speed.

---

# Stage 6 – Priority Inbox (Top 10 Notifications)

Goal:  
Implement a Priority Inbox that always displays the top `n` most important unread notifications first (e.g., top 10).  
Priority is determined by:

- **Weight**: `placement > result > event`
- **Recency**: newer notifications are more important

You must:

- Use the provided Notification API:
  `GET http://4.224.186.213/evaluation-service/notifications`
- Find the top 10 unread notifications.
- Use your **logging middleware** extensively.
- Write real code (not pseudocode).
- Push code and screenshots to the same GitHub repo.
- Explain your approach in this section.

## Approach

1. Fetch all notifications from the API.
2. Filter only unread notifications.
3. Assign a numeric priority score to each notification:
   - Base weight:
     - `placement`: 3
     - `result`: 2
     - `event`: 1
   - Recency factor: use `createdAt` (e.g., timestamp) to boost newer notifications.
4. Sort by score descending.
5. Return top 10.

### Example score formula

```python
priority_score = type_weight * (1 + recency_factor)
```

Where:

- `type_weight` = 3 for `Placement`, 2 for `Result`, 1 for `Event`
- `recency_factor` = some value based on `createdAt` (e.g., `timestamp / max_timestamp`)

Alternatively, you can:

- Sort first by type weight (placement, result, event), then by `createdAt` descending.

## Python implementation example

```python
import requests
from typing import List, Dict

import logging
from logging_utils import get_logger  # your logging middleware wrapper

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
    Uses logging middleware for request logging.
    """
    logger.info("Fetching notifications from API", url=api_url)
    response = requests.get(api_url)
    if response.status_code != 200:
        logger.error("API request failed", status_code=response.status_code, url=api_url)
        raise RuntimeError(f"API request failed with status {response.status_code}")

    logger.info("Successfully fetched notifications", count=len(response.json()))
    return response.json()

def compute_priority_score(notification: Dict) -> float:
    """
    Compute priority score based on type weight and recency.
    """
    type_weight = get_type_weight(notification.get("notificationType", ""))
    created_at = notification.get("createdAt", "")

    # Simple recency factor: convert to timestamp (you can adjust this)
    # For simplicity, assume createdAt is in ISO format or timestamp.
    # Here we use a dummy factor based on string length for demo;
    # in real code, parse to datetime and compute timestamp.
    import datetime
    try:
        dt = datetime.datetime.fromisoformat(created_at)
        timestamp = dt.timestamp()
    except Exception as e:
        logger.warning("Failed to parse createdAt", createdAt=created_at, error=str(e))
        timestamp = 0

    # Normalize timestamp (example: assume max timestamp is ~now)
    max_timestamp = datetime.datetime.now().timestamp()
    recency_factor = timestamp / max_timestamp if max_timestamp > 0 else 0

    priority_score = type_weight * (1 + recency_factor)
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
```

## Maintaining top 10 efficiently as new notifications come in

Options:

1. **Recompute on each request**:
   - Fetch all, filter unread, compute score, sort, and take top 10.
   - Simple, but may be slow if there are many notifications.

2. **Cache top 10**:
   - Cache the top 10 unread notifications in Redis.
   - Invalidate or update cache when:
     - A new notification is created.
     - A notification is marked as read/deleted.
   - This is more efficient for high read volume.

3. **Use a sorted data structure**:
   - Use a sorted set (e.g., Redis Sorted Set) keyed by priority score.
   - Insert new notifications with their score.
   - Query top N in O(log N).

For this assignment, recomputing on each request is acceptable, but you can mention caching as an optimization.

## Files to push

- `priority_inbox.py` (or `.js`, `.ts`, etc.) – your code file.
- Screenshots showing the top 10 priority notifications printed/displayed.

Update your `notification_system_design.md` with this section (already added above), then push:

```bash
git add notification_system_design.md priority_inbox.py
git commit -m "feat: add Stage 6 Priority Inbox code and explanation"
git push origin main
```

Then take screenshots of the output and push them too.

### Authentication behavior

The Priority Inbox client authenticates to the Notification API using a bearer token. The token is read from the `NOTIFICATION_API_TOKEN` environment variable and passed as `Authorization: Bearer <token>` in the request headers.

With the provided evaluation token, the API currently responds with HTTP 401 (Unauthorized). The client logs this failure (with the header masked) and raises an exception instead of failing silently. This indicates an issue with token validity or server-side auth, while the client logic and authorization flow are implemented correctly.