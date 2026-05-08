from logging_middleware import Log
from vehicle_maintenance_scheduler.api_client import fetch_depots, fetch_vehicles


def choose_tasks(tasks, available_hours):
    # normal 0/1 knapsack: duration is weight, impact is value
    n = len(tasks)
    dp = [[0 for _ in range(available_hours + 1)] for _ in range(n + 1)]

    for i in range(1, n + 1):
        task = tasks[i - 1]
        duration = int(task.get("Duration", 0))
        impact = int(task.get("Impact", 0))

        for hours in range(available_hours + 1):
            skip = dp[i - 1][hours]
            take = 0
            if duration <= hours:
                take = impact + dp[i - 1][hours - duration]
            dp[i][hours] = max(skip, take)

    picked = []
    hours_left = available_hours

    for i in range(n, 0, -1):
        if dp[i][hours_left] != dp[i - 1][hours_left]:
            task = tasks[i - 1]
            picked.append(task)
            hours_left -= int(task.get("Duration", 0))

    picked.reverse()
    return picked, dp[n][available_hours]


def make_schedule():
    depots = fetch_depots()
    vehicles = fetch_vehicles()

    Log("backend", "info", "service", "started maintenance schedule calculation")

    schedules = []
    for depot in depots:
        depot_id = depot.get("ID")
        hours = int(depot.get("MechanicHours", 0))
        selected, total_impact = choose_tasks(vehicles, hours)
        total_duration = sum(int(item.get("Duration", 0)) for item in selected)

        schedules.append({
            "depot_id": depot_id,
            "mechanic_hours": hours,
            "used_hours": total_duration,
            "total_impact": total_impact,
            "selected_tasks": selected,
        })

    Log("backend", "info", "service", "maintenance schedule calculated")
    return {"schedules": schedules}
