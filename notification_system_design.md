# Stage 1 – Notification REST API Design

This document defines the REST APIs and real-time mechanism for a campus notification platform that delivers updates about Placements, Events, and Results to logged-in students.[page:1] The goal is to provide predictable endpoints, clear JSON contracts, and a simple real-time channel for the frontend.[page:1]

## Core Actions

- Create a notification (by an admin or system process).
- Fetch notifications for a user (with pagination and filters).
- Fetch unread notifications for a user.
- Mark a notification as read.
- Mark all notifications as read.
- Delete a notification for a user.
- Subscribe to real-time notification updates.

## REST API Endpoints

Assumption: Users accessing the APIs are already authenticated by the platform, and the backend derives the current user from context or headers.[page:1]

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

All APIs assume that the user is pre-authorised by the platform.[page:1]

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
- `type` (string, required): Category of notification, e.g., `PLACEMENT`, `EVENT`, `RESULT`.
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

For real-time updates, the platform can use **Server-Sent Events (SSE)** to push notifications from the server to the browser over a long-lived HTTP connection.[page:1] Alternatively, a WebSocket endpoint can be used with the same payload structure.[page:1]

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

This section defines the database choice, schema, scaling concerns, and example queries for implementing the notification APIs defined in Stage 1.[page:1]

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

These queries, combined with the schema and API design above, provide a complete end-to-end design for the notification platform required in Stage 1 and Stage 2.[page:1]
```