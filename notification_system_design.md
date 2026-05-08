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

### 1. Is this query accurate and why is it slow?
Yes, the query is perfectly accurate for fetching unread notifications for a specific student. However, it's very slow because of three main issues:
- **No Index**: Without an index on `studentID` and `isRead`, Postgres has to do a **Full Table Scan** (reading all 5,000,000 rows) to find matching records.
- **In-Memory Sort**: The `ORDER BY createdAt DESC` forces the database to sort the results in memory (filesort) after finding them, which is slow and memory-intensive.
- **`SELECT *` Overhead**: Pulling every column off the disk takes up more bandwidth and RAM than just selecting the specific columns needed.

### 2. What would you change & computation cost?
I would add a **composite index** specifically tailored to the `WHERE` and `ORDER BY` clauses:
```sql
CREATE INDEX idx_notifications_student_read_created 
ON notifications (studentID, isRead, createdAt DESC);
```
I would also stop doing `SELECT *` and add pagination (`LIMIT 20`). 
**Computation Cost**: With the index, the database can do an **Index Scan** or **Index-Only Scan**. The cost drops from $O(N)$ (scanning 5 million rows) to $O(\log N)$ (traversing the B-Tree index). Since the index is already sorted by `createdAt DESC`, the sorting cost becomes $O(1)$. 

### 3. Adding indexes on every column?
**Terrible advice.** While indexes speed up read operations (`SELECT`), they drastically slow down write operations (`INSERT`, `UPDATE`, `DELETE`) because every single index must be updated synchronously whenever a row changes. Since notifications are very write-heavy, indexing every column would cripple the database's write performance and waste gigabytes of disk space and RAM.

### 4. Query for Placement Notifications in the last 7 days
```sql
SELECT DISTINCT studentID 
FROM notifications 
WHERE notificationType = 'Placement' 
AND createdAt >= NOW() - INTERVAL '7 days';
```


## Stage 4

If we're querying the DB on *every single page load*, we are going to crush our database under the weight of read requests. Here are a few ways to fix this, along with their pros and cons.

### 1. Redis Caching (For the Unread Badge)
The most common query is just getting the unread count to render the red bubble in the navbar.
- **Solution**: Instead of `SELECT COUNT(*)`, keep a simple key-value in Redis (e.g., `unread_count:1042`). Increment it when a notification is created, decrement it when read.
- **Tradeoffs**: It's blazing fast and takes massive load off the main DB. The downside is potential cache-drift (Redis gets out of sync with Postgres), so you need a background job to occasionally heal the cache.

### 2. Client-Side State & LocalStorage
- **Solution**: Once the frontend fetches the notifications on the initial login, store them in a state manager (like Redux/Zustand) or `localStorage`. On subsequent page navigation, just read from memory instead of hitting the network.
- **Tradeoffs**: Super fast navigation and zero server cost. The tradeoff is that the client might look at stale data if they leave the tab open for hours without refreshing (unless paired with SSE).

### 3. Server-Sent Events (SSE) or WebSockets
- **Solution**: Stop making the client ask the server "do I have notifications?" on every page load. Instead, keep a single SSE connection open. The server pushes down new notifications only when they actually happen.
- **Tradeoffs**: Greatly reduces HTTP request overhead. However, maintaining thousands of open socket connections requires more RAM on the server and a load balancer configured for long-lived connections.

### My Recommendation
I would combine **Redis Caching** for the unread count and **SSE** for real-time updates. When the user logs in, we fetch the first paginated page of notifications once. From then on, we rely on SSE to push new items to the UI. We never fetch on page navigation.

## Stage 5

### What's wrong with this pseudocode?
1. **Synchronous Blocking**: Running an HTTP request (`send_email`) and a DB insert inside a `for` loop for 50,000 iterations will take forever. The HR user's browser will likely timeout waiting for the API to respond.
2. **N+1 Database Problem**: Doing 50,000 individual `INSERT` queries is incredibly inefficient and will severely bog down the database.
3. **No Error Handling or Retries**: If `send_email` throws a network timeout, the entire loop crashes. 

### What happens when it fails midway?
If the loop crashes at student #25,000, we have a nightmare scenario: half the students got the email, half didn't, and we have no safe way to resume. If we re-run the script, the first 25,000 students will get spammed with a duplicate email.

### Should DB saving and email sending happen together?
**Absolutely not.** They should be completely decoupled. 
Database inserts are fast and reliable. Email APIs (like SendGrid or SES) are slow and prone to rate-limits or network blips. If the email API goes down, it shouldn't prevent us from saving the notification to the database. We should bulk-insert the data into the DB first, then offload the email sending to a background worker queue.

### Redesigning for Speed & Reliability
We need to use **Bulk Inserts** for the database and **Message Queues** (like Celery, RabbitMQ, or AWS SQS) for the emails.

**Revised Pseudocode:**
```python
function notify_all(student_ids: array, message: string):
    bulk_save_to_db(student_ids, message)
    
    for student_id in student_ids:
        message_queue.push(task="send_email_and_push", student_id=student_id, message=message)
        
    return "Notifications are being sent in the background!"

function process_queue_task(task):
    try:
        send_email(task.student_id, task.message)
        push_to_app(task.student_id, task.message)
    except EmailAPIError:
        message_queue.retry_task(task, delay="5_minutes")
```

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
