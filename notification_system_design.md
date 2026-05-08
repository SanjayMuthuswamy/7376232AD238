# Notification System Design

## Stage 1

### Core Actions
1. **Fetch Notifications**: Retrieve a paginated list of notifications for the logged-in user.
2. **Get Unread Count**: Get the total number of unread notifications for the user badge.
3. **Mark as Read**: Mark a specific notification as read.
4. **Mark All as Read**: Mark all unread notifications for the user as read.
5. **Create Notification**: (Internal/System action) Create a new notification for a user.

### REST API Endpoints

#### 1. Fetch Notifications
- **Endpoint**: `GET /api/v1/notifications`
- **Headers**:
  ```json
  {
    "Authorization": "Bearer <jwt_token>"
  }
  ```
- **Query Parameters**:
  - `page` (integer, default: 1)
  - `limit` (integer, default: 20)
  - `unread_only` (boolean, default: false)
- **Response (200 OK)**:
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

#### 2. Get Unread Count
- **Endpoint**: `GET /api/v1/notifications/unread-count`
- **Headers**:
  ```json
  {
    "Authorization": "Bearer <jwt_token>"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "unread_count": 5
  }
  ```

#### 3. Mark a Notification as Read
- **Endpoint**: `PATCH /api/v1/notifications/{notification_id}/read`
- **Headers**:
  ```json
  {
    "Authorization": "Bearer <jwt_token>",
    "Content-Type": "application/json"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Notification marked as read."
  }
  ```

#### 4. Mark All as Read
- **Endpoint**: `PATCH /api/v1/notifications/read-all`
- **Headers**:
  ```json
  {
    "Authorization": "Bearer <jwt_token>",
    "Content-Type": "application/json"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "All notifications marked as read."
  }
  ```

### Real-Time Notifications Mechanism
To push notifications to the front-end in real-time, **Server-Sent Events (SSE)** or **WebSockets** can be used. 
Since notifications are a one-way stream from the server to the client, **Server-Sent Events (SSE)** is an excellent lightweight choice. Alternatively, if the platform already uses **WebSockets**, the same connection can be reused.
- The client connects to `GET /api/v1/notifications/stream`.
- When the backend generates a new notification, it publishes the event to a message broker (like Redis Pub/Sub).
- The API server listens to the broker and pushes the JSON payload of the new notification to the specific connected client.


## Stage 2

### Persistent Storage Choice
**PostgreSQL** (Relational).
For a notification system where we occasionally need to store unstructured payload data but still maintain a strong relationship with the user, **PostgreSQL** is a solid choice because it supports robust indexing and JSONB data types. It handles large datasets efficiently when properly indexed.

### Database Schema (PostgreSQL)
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

-- Indexes
CREATE INDEX idx_notifications_studentID ON notifications(studentID);
CREATE INDEX idx_notifications_student_isRead ON notifications(studentID, isRead);
```

### Potential Problems with Increasing Data Volume
1. **Slow Reads**: As the table reaches millions of rows, filtering by `studentID` and `isRead` can become slow.
2. **Storage Costs & Bloat**: Retaining years of notifications takes up massive disk space and RAM for indexes.
3. **High Write Throughput Bottlenecks**: Creating notifications for thousands of users simultaneously can lock the database.

### Solutions to Volume Problems
1. **Data Partitioning**: Partition the `notifications` table by date (e.g., monthly partitions) so queries for recent notifications only scan a smaller subset of data.
2. **Archiving/TTL**: Move notifications older than 30 or 90 days to a cold storage database or delete them.
3. **Caching**: Cache the `unread_count` in an in-memory store like **Redis**. Instead of querying the DB every time the user loads a page, increment/decrement the Redis counter.
4. **Batch Processing**: When generating bulk notifications, push them to a queue (Kafka/RabbitMQ) and let workers insert them into the DB in batches.

### Queries Based on Stage 1 APIs

**1. Fetch Notifications:**
```sql
SELECT id, title, message, type, isRead, action_url, createdAt 
FROM notifications 
WHERE studentID = 1042 
ORDER BY createdAt DESC 
LIMIT 20 OFFSET 0;
```

**2. Get Unread Count:**
```sql
SELECT COUNT(*) FROM notifications WHERE studentID = 1042 AND isRead = FALSE;
```

**3. Mark a Notification as Read:**
```sql
UPDATE notifications SET isRead = TRUE WHERE id = 'uuid-here' AND studentID = 1042;
```

**4. Mark All as Read:**
```sql
UPDATE notifications SET isRead = TRUE WHERE studentID = 1042 AND isRead = FALSE;
```

## Stage 3

### Potential Reasons for Slow Query Performance
The query provided is:
```sql
SELECT * FROM notifications
WHERE studentID = 1042 AND isRead = false
ORDER BY createdAt DESC;
```

1. **Missing Indexes**: If there is no index covering `studentID` and `isRead`, the database must perform a **Full Table Scan** across all 5,000,000 rows to find the matching records.
2. **Sorting Overhead (`ORDER BY createdAt DESC`)**: Even with a basic index on `studentID`, the database still has to fetch the results and then sort them in memory (filesort), which is expensive for a large volume of rows.
3. **Fetching Unnecessary Columns (`SELECT *`)**: Selecting all columns increases the amount of data read from disk, taking up more memory and network bandwidth.

### Optimizations

#### 1. Create a Composite Index (Most Impactful)
Create a composite index on the exact columns used in the `WHERE` and `ORDER BY` clauses.
```sql
CREATE INDEX idx_notifications_student_read_created 
ON notifications (studentID, isRead, createdAt DESC);
```
*Why this works*: The database can instantly locate the section of the index for `studentID = 1042` and `isRead = false`. Because the index also includes `createdAt DESC`, the results are already sorted within the index, completely eliminating the expensive memory sort operation.

#### 2. Optimize the Query
Avoid `SELECT *`. Only select the specific columns needed by the front-end to render the notifications. Add pagination (`LIMIT`) to avoid fetching an unbounded number of rows.
```sql
SELECT id, title, message, type, createdAt 
FROM notifications
WHERE studentID = 1042 AND isRead = false
ORDER BY createdAt DESC
LIMIT 20;
```

#### 3. Caching
Store the unread count in **Redis** (e.g. key `unread_count:1042`), increment/decrement as events occur, instead of calculating `COUNT(*)` continuously.


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
