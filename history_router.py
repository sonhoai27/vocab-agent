import json
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from agno.db.base import SessionType
from agno.os.utils import get_session_name

from agno_agent import db

router = APIRouter(prefix="/history", tags=["history"])


class HistoryMessage(BaseModel):
    role: str
    content: str
    created_at: Optional[Union[int, str]]


class HistoryRun(BaseModel):
    run_id: str
    parent_run_id: Optional[str] = None
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    run_input: Optional[str] = None
    content: Optional[Any] = None
    created_at: Optional[Union[int, str]] = None
    metrics: Optional[Dict[str, Any]] = None
    messages: List[HistoryMessage] = []


class HistorySessionEntry(BaseModel):
    session_id: str
    session_name: str
    user_id: Optional[str]
    session_type: str
    created_at: Optional[Union[int, str]]
    updated_at: Optional[Union[int, str]]
    run_count: int
    last_run_at: Optional[Union[int, str]]


class HistoryDetail(BaseModel):
    session_id: str
    session_name: str
    session_type: str
    user_id: Optional[str]
    created_at: Optional[Union[int, str]]
    updated_at: Optional[Union[int, str]]
    session_state: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    session_summary: Optional[Dict[str, Any]]
    runs: List[HistoryRun]


class HistoryListResponse(BaseModel):
    data: List[HistorySessionEntry]
    total: int
    page: int
    limit: int


def _resolve_session_type(session_type: Optional[str]) -> SessionType:
    if not session_type:
        return SessionType.AGENT
    try:
        return SessionType(session_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Unknown session_type, use agent/team/workflow")


def _normalize_message_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    try:
        return json.dumps(content, ensure_ascii=False)
    except Exception:
        return str(content)


def _format_messages(raw_messages: Optional[List[Dict[str, Any]]]) -> List[HistoryMessage]:
    if not raw_messages:
        return []
    formatted_messages: List[HistoryMessage] = []
    for raw in raw_messages:
        formatted_messages.append(
            HistoryMessage(
                role=raw.get("role", "assistant"),
                content=_normalize_message_content(raw.get("content", "")),
                created_at=raw.get("created_at")
            )
        )
    return formatted_messages


def _format_run(raw_run: Dict[str, Any]) -> HistoryRun:
    return HistoryRun(
        run_id=raw_run.get("run_id", ""),
        parent_run_id=raw_run.get("parent_run_id"),
        agent_id=raw_run.get("agent_id"),
        user_id=raw_run.get("user_id"),
        session_id=raw_run.get("session_id"),
        run_input=raw_run.get("run_input"),
        content=raw_run.get("content"),
        created_at=raw_run.get("created_at"),
        metrics=raw_run.get("metrics"),
        messages=_format_messages(raw_run.get("messages"))
    )


def _session_name_with_fallback(session: Dict[str, Any], session_type: SessionType) -> str:
    decorated = {**session, "session_type": session.get("session_type") or session_type.value}
    name = get_session_name(decorated)
    return name or session.get("session_id", "")


def _build_session_entry(session: Dict[str, Any], session_type: SessionType) -> HistorySessionEntry:
    runs = session.get("runs") or []
    last_run_at = None
    if isinstance(runs, list) and runs:
        last_run = runs[-1]
        last_run_at = last_run.get("created_at")

    return HistorySessionEntry(
        session_id=session.get("session_id", ""),
        session_name=_session_name_with_fallback(session, session_type),
        user_id=session.get("user_id"),
        session_type=session.get("session_type") or session_type.value,
        created_at=session.get("created_at"),
        updated_at=session.get("updated_at"),
        run_count=len(runs) if isinstance(runs, list) else 0,
        last_run_at=last_run_at
    )


@router.get("/", response_model=HistoryListResponse)
def list_history(
    session_type: Optional[str] = Query(None, description="Session type to filter by (agent/team/workflow)"),
    user_id: Optional[str] = Query(None, description="User ID to scope history"),
    session_name: Optional[str] = Query(None, description="Filter sessions by name fragment"),
    limit: int = Query(20, ge=1, le=100, description="Number of sessions per page"),
    page: int = Query(1, ge=1, description="Page number")
) -> HistoryListResponse:
    resolved_type = _resolve_session_type(session_type)
    sessions_raw, total_count = db.get_sessions(
        session_type=resolved_type,
        user_id=user_id,
        session_name=session_name,
        limit=limit,
        page=page,
        sort_by="created_at",
        sort_order="desc",
        deserialize=False
    )
    total_count = total_count or 0
    entries = [_build_session_entry(session, resolved_type) for session in sessions_raw]
    return HistoryListResponse(data=entries, total=total_count, page=page, limit=limit)


@router.get("/{session_id}", response_model=HistoryDetail)
def history_detail(
    session_id: str,
    session_type: Optional[str] = Query(None, description="Session type (agent/team/workflow) for disambiguation"),
    user_id: Optional[str] = Query(None, description="Optional user ID to further scope the session")
) -> HistoryDetail:
    resolved_type = _resolve_session_type(session_type)
    session = db.get_session(
        session_id=session_id,
        session_type=resolved_type,
        user_id=user_id,
        deserialize=False
    )
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    runs = session.get("runs") or []
    formatted_runs = []
    if isinstance(runs, list):
        for raw_run in runs:
            if isinstance(raw_run, dict):
                formatted_runs.append(_format_run(raw_run))

    session_data = session.get("session_data") or {}
    return HistoryDetail(
        session_id=session.get("session_id", session_id),
        session_name=_session_name_with_fallback(session, resolved_type),
        session_type=session.get("session_type") or resolved_type.value,
        user_id=session.get("user_id"),
        created_at=session.get("created_at"),
        updated_at=session.get("updated_at"),
        session_state=session_data.get("session_state"),
        metadata=session.get("metadata"),
        session_summary=session_data.get("session_summary"),
        runs=formatted_runs
    )
