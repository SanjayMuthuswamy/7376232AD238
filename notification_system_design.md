# Notification System Design

## Stage 1

For the core API, I think we need a few main endpoints to handle notifications properly when a user logs in. Here are the core actions we need to support:
- Fetching a list of notifications (paginated)
- Getting just the unread count (for the little badge in the UI)
- Marking a single notification as read
- Marking everything as read in one go
- Creating a notification internally

### REST API Endpoints

**1. Fetch Notifications**
`GET /api/v1/notifications`

Headers:
```json
{ "Authorization": "Bearer <jwt_token>" }
```

Query Params: `page` (default 1), `limit` (default 20), `unread_only` (default false)

Response:
```json
{
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Assignment Graded",
      "message": "Your math assignment has been graded.",
      "type": "alert",
      "is_read": false,
      "action_url": "/assignments/123",
      "created_at": "2026-05-08T10:00:00Z"
    }
  ],
  "meta": {
    "total": 45,
    "page": 1,
    "limit": 20,
    "total_pages": 3
  }
}
```

**2. Get Unread Count**
`GET /api/v1/notifications/unread-count`
Response:
```json
{ "unread_count": 5 }
```

**3. Mark as Read**
`PATCH /api/v1/notifications/{notification_id}/read`
Response:
```json
{ "success": true, "message": "Notification marked as read." }
```

**4. Mark All as Read**
`PATCH /api/v1/notifications/read-all`

### Real-Time Updates
Since notifications mostly just flow from the server to the client, Server-Sent Events (SSE) is probably the best and lightest option here. We don't really need a full 2-way WebSocket connection unless we're already using something like Socket.io for a chat feature. If we just connect the client to a `GET /api/v1/notifications/stream` endpoint, the server can push JSON down whenever a new event comes through Redis Pub/Sub.

## Stage 2

### Database Choice
I'd go with **PostgreSQL**. Since we still have a strong relationship to the `studentID` but might occasionally want to toss random JSON payloads in there, Postgres gives us the best of both worlds (relational guarantees + JSONB columns). 

### Schema
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    studentID INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50),
    action_url VARCHAR(255),
    isRead BOOLEAN DEFAULT FALSE,
    createdAt TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- We definitely need these indexes so reads don't crawl
CREATE INDEX idx_notifications_studentID ON notifications(studentID);
CREATE INDEX idx_notifications_student_isRead ON notifications(studentID, isRead);
```

### Scaling Challenges
As we hit millions of rows, a few things will break:
1. Searching by `studentID` and `isRead` will slow down if our indexes get too big to fit in memory.
2. Storing 5 years of notifications is a waste of money and disk space.
3. If we send a mass announcement to 100k students at once, we might lock up the DB with writes.

To fix this:
- **Partitioning**: Split the table by month so we're only querying recent stuff.
- **Archiving**: Delete or move notifications older than 90 days.
- **Caching**: Stick the unread count in Redis so we aren't running `COUNT(*)` on page loads.
- **Queues**: Use RabbitMQ or Kafka to insert notifications in background batches.

### Queries

Fetch notifications:
```sql
SELECT id, title, message, type, isRead, action_url, createdAt 
FROM notifications 
WHERE studentID = 1042 
ORDER BY createdAt DESC 
LIMIT 20 OFFSET 0;
```

Unread Count:
```sql
SELECT COUNT(*) FROM notifications WHERE studentID = 1042 AND isRead = FALSE;
```

Mark as read:
```sql
UPDATE notifications SET isRead = TRUE WHERE id = 'uuid-here' AND studentID = 1042;
```

Mark all as read:
```sql
UPDATE notifications SET isRead = TRUE WHERE studentID = 1042 AND isRead = FALSE;
```

## Stage 3

### Why the query is slow
Looking at `SELECT * FROM notifications WHERE studentID = 1042 AND isRead = false ORDER BY createdAt DESC;`

1. **No index**: If there's no index that covers both `studentID` and `isRead`, Postgres has to do a full table scan across all 5 million rows just to find the records.
2. **Memory sorting**: Even if it finds the rows, `ORDER BY createdAt DESC` forces the DB to sort the results in memory before returning them, which is super slow.
3. **`SELECT *`**: Pulling every single column off the disk takes up more memory and network bandwidth than necessary.

### How to fix it

**1. Add a composite index (This is the most important fix)**
We need an index that perfectly matches the `WHERE` and `ORDER BY` clauses.
```sql
CREATE INDEX idx_notifications_student_read_created 
ON notifications (studentID, isRead, createdAt DESC);
```
With this, the DB instantly jumps to the right student, filters out the read ones, and the data is *already sorted* inside the index, so it skips the memory sort entirely.

**2. Optimize the query**
Stop doing `SELECT *` and add a limit so we don't accidentally fetch 10,000 rows.
```sql
SELECT id, title, message, type, createdAt 
FROM notifications
WHERE studentID = 1042 AND isRead = false
ORDER BY createdAt DESC
LIMIT 20;
```

**3. Redis caching**
Honestly, we shouldn't be running this query just to show the unread badge. We should keep an `unread_count:1042` key in Redis, increment it when a new notification comes in, and decrement it when they read it.


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
