# Notification System Design

## Stage 1

The notification platform should expose simple REST APIs for creating, reading, and updating notifications. I would keep the endpoints predictable so the frontend can use them without extra mapping logic.

### Main APIs

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/notifications` | create a new notification |
| GET | `/notifications` | list notifications for the logged-in user |
| GET | `/notifications/{id}` | get one notification |
| PATCH | `/notifications/{id}/read` | mark one notification as read |
| PATCH | `/notifications/read-all` | mark all notifications as read |
| GET | `/notifications/unread-count` | show unread count in the UI |

### Create Notification Request

```json
{
  "userId": 1042,
  "notificationType": "Placement",
  "title": "Placement Drive",
  "message": "A new placement drive has been posted",
  "priority": 10
}
```

### Notification Response

```json
{
  "id": "noti_101",
  "userId": 1042,
  "notificationType": "Placement",
  "title": "Placement Drive",
  "message": "A new placement drive has been posted",
  "priority": 10,
  "isRead": false,
  "createdAt": "2026-05-08T10:30:00Z"
}
```

For real-time updates, I would use WebSocket or Server-Sent Events. The frontend can still call the REST APIs after refresh, so real-time delivery is an extra layer and not the only source of truth.

## Stage 2

A relational database is a good starting point because the data has clear relationships: users have many notifications, and every notification belongs to one user.

### Suggested Tables

```sql
CREATE TABLE students (
    id BIGINT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL
);

CREATE TABLE notifications (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id),
    notification_type VARCHAR(30) NOT NULL,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    priority INT DEFAULT 0,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

As data grows, the main problems will be slow unread notification queries, large table size, and too many writes during bulk notification events. To handle this, indexes should be added early, and old notifications can be archived later if they are no longer needed in the main app.

## Stage 3

The given query is:

```sql
SELECT * FROM notifications
WHERE studentID = 1042 AND isRead = false
ORDER BY createdAt DESC;
```

The query is logically fine if the column names are correct, but it will become slow when the table has millions of rows because the database may scan many records for one student.

I would add a composite index:

```sql
CREATE INDEX idx_notifications_student_read_created
ON notifications (student_id, is_read, created_at DESC);
```

This helps because the database can directly find unread notifications for one student and already read them in newest-first order.

Adding indexes on every column is not a good idea. Indexes make reads faster, but they also slow down inserts and updates because every index has to be maintained. They also take extra storage.

Query to find students who got placement notifications:

```sql
SELECT DISTINCT student_id
FROM notifications
WHERE notification_type = 'Placement';
```

If the app frequently filters by type, I would also add:

```sql
CREATE INDEX idx_notifications_type_student
ON notifications (notification_type, student_id);
```

## Stage 4

Fetching notifications on every page load is simple, but it wastes database and network resources. A better solution is a mix of caching, pagination, and real-time updates.

### Options

- Pagination: fetch 20 or 50 notifications at a time instead of all records.
- Unread count cache: store only the unread count in Redis or a similar cache.
- Client polling: easy to implement, but can create extra load if many users are online.
- WebSocket or SSE: better for real-time updates, but needs connection handling.
- Database indexes: still required because caching does not solve every query.

My approach would be:

1. Fetch latest notifications with pagination.
2. Cache unread count per student.
3. Use WebSocket or SSE only for new notification events.
4. Fall back to REST API if the real-time connection fails.

This keeps the app reliable without making the first version too complicated.

## Stage 5

The pseudocode sends email, saves to DB, and pushes to app inside one loop. The main issue is that one failed email can slow or break the whole process. If 50,000 students are notified at once, doing everything synchronously is risky.

Problems:

- Sending email one by one is slow.
- DB inserts one by one are expensive.
- A failure midway can leave some students notified and some not.
- There is no retry system.
- The user has to wait for the whole process.

Better design:

```txt
1. Create a notification campaign.
2. Insert notification rows in batches.
3. Push email jobs to a queue.
4. Push in-app notification events separately.
5. Retry failed email jobs.
6. Track campaign progress.
```

Saving to DB and sending email should not fully depend on each other. The DB insert should happen first so the system has a record of what should be sent. Email sending can happen through a background worker with retries.

Useful logging points:

- campaign created
- batch insert completed
- email job failed
- retry started
- campaign completed

## Stage 6

For the priority inbox, I would rank notifications using priority, notification type, and recency.

Example score:

```txt
score = priority + typeWeight + recencyBonus
```

Where:

- Placement = 30
- Result = 20
- Event = 10
- newer notifications get a small bonus

The API can return only the top 10:

```txt
GET /notifications/priority
```

Response:

```json
{
  "notifications": [
    {
      "id": "noti_101",
      "notificationType": "Placement",
      "title": "Placement Drive",
      "priority": 10,
      "score": 43
    }
  ]
}
```

For a large system, I would not sort every notification from scratch on every request. I would keep the right indexes, query recent unread notifications first, calculate the score for a limited set, and return the top 10. If traffic grows more, the top 10 list can be cached per student and refreshed when a new notification arrives.
