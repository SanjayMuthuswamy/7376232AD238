from fastapi import APIRouter, HTTPException
from requests import RequestException

from logging_middleware import Log
from vehicle_maintenance_scheduler.scheduler_service import make_schedule

router = APIRouter()



@router.get("/")
def schedule_vehicles():
    try:
        return make_schedule()
    except ValueError as err:
        Log("backend", "error", "handler", "auth token missing while scheduling")
        raise HTTPException(status_code=400, detail=str(err))
    except RequestException:
        Log("backend", "error", "handler", "test server request failed")
        raise HTTPException(status_code=502, detail="Could not fetch data from test server")
