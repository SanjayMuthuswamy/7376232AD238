# Vehicle Maintenance Scheduler

This backend endpoint fetches depot and vehicle task data from the protected test APIs and picks the best set of tasks for each depot.

The problem is solved using a simple 0/1 knapsack approach:

- mechanic hours = capacity
- task duration = weight
- task impact = value

Run the local app and call:

```txt
GET http://127.0.0.1:8000/vehicle-scheduling
```

`AUTH_TOKEN` must be present in `.env` before calling this endpoint.
