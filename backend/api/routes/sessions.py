"""CloudPilot simulated session-management API."""
from fastapi import APIRouter, HTTPException
from backend.sessions import service

router = APIRouter(prefix="/sessions", tags=["Cloud Sessions"])


@router.get("")
async def get_sessions():
    return service.list_sessions()


@router.post("/{provider}/start")
async def start_provider_session(provider: str):
    try:
        return service.start_session(provider.lower())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{provider}/activity")
async def provider_activity(provider: str):
    try:
        return service.record_activity(provider.lower())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{provider}/end")
async def end_provider_session(provider: str):
    try:
        return service.end_session(provider.lower())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/end-all")
async def end_all():
    return service.end_all_sessions()
