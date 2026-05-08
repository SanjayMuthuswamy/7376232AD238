# Notification System Design

## Stage 1

REST API design with 6 endpoints for managing notifications.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/notifications` | Create notification |
| GET | `/notifications` | List notifications |
| GET | `/notifications/{id}` | Get one notification |
| PATCH | `/notifications/{id}/read` | Mark as read |
| PATCH | `/notifications/read-all` | Mark all as read |
| GET | `/notifications/unread-count` | Get unread count |

Real-time updates use WebSocket or Server-Sent Events.

## Stage 2
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

```txtdid 
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
