import os
import datetime
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv, find_dotenv

from sqlalchemy import (
    create_engine, MetaData, Table, Column, BigInteger, Integer, String,
    DateTime, Float, Text, JSON, ForeignKey, func, Boolean
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import text, inspect  


# ---------- SCHEMA ----------

metadata = MetaData()

runs = Table(
    "runs", metadata,
    Column("process_id", BigInteger, primary_key=True),
    Column("topic", String, nullable=False),
    Column("product", JSONB, nullable=False),
    Column("product_ranking", JSONB, nullable=False, server_default=text("'{}'::jsonb")), 
    Column("finished", Boolean, nullable=False, server_default="false"),  # uusi sarake
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()),
)

run_timeline = Table(
    "run_timeline", metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("process_id", BigInteger, ForeignKey("runs.process_id", ondelete="CASCADE"), index=True, nullable=False),
    Column("step_index", Integer, nullable=False),       # 0..n
    Column("node", Integer, nullable=True),              # from transition[i]
    Column("ts", DateTime(timezone=True), nullable=True),# from timestamps[i]
    Column("agent_score", Float, nullable=True),         # from agent_scores[i]
)

run_messages = Table(
    "run_messages", metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("process_id", BigInteger, ForeignKey("runs.process_id", ondelete="CASCADE"), index=True, nullable=False),
    Column("turn_index", Integer, nullable=False),
    Column("role", String, nullable=False),              # "human" | "ai" | "system" | "tool" etc.
    Column("content", Text, nullable=False),
    Column("meta", JSONB, nullable=True),                # store extra fields if needed
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

run_explanations = Table(
    "run_explanations", metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("process_id", BigInteger, ForeignKey("runs.process_id", ondelete="CASCADE"), index=True, nullable=False),
    Column("idx", Integer, nullable=False),
    Column("key", String, nullable=True),
    Column("text", Text, nullable=False),
    Column("meta", JSONB, nullable=True),
)

# ---------- SETUP / INIT ----------

def get_engine(database_url: Optional[str] = None) -> Engine:
    """
    DATABASE_URL example (Aiven PostgreSQL):
    postgres://USER:PASSWORD@HOST:PORT/DBNAME?sslmode=require
    """
    load_dotenv(find_dotenv(usecwd=True))
    url = database_url or os.getenv("SQLALCHEMY_DATABASE_URI")
    if not url:
        raise ValueError("SQLALCHEMY_DATABASE_URI environment variable is not set.")
    return create_engine(url, pool_pre_ping=True, future=True)

def init_db(engine: Engine) -> None:
    """Create tables if they don't exist."""
    metadata.create_all(engine)

# ---------- HELPERS ----------

def _to_iso(dt: Any) -> Optional[datetime.datetime]:
    if dt is None:
        return None
    if isinstance(dt, datetime.datetime):
        return dt if dt.tzinfo else dt.replace(tzinfo=datetime.timezone.utc)
    # best-effort parse if string; otherwise drop
    try:
        from dateutil import parser  # optional: install python-dateutil
        parsed = parser.parse(str(dt))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=datetime.timezone.utc)
    except Exception:
        return None

def _align_time_series(transition: List[int],
                       timestamps: List[datetime.datetime],
                       agent_scores: List[float]) -> List[Tuple[int, Optional[int], Optional[datetime.datetime], Optional[float]]]:
    """
    Returns rows as (step_index, node, timestamp, agent_score).
    Safely aligns lists of potentially different lengths.
    """
    n = max(len(transition or []), len(timestamps or []), len(agent_scores or []))
    rows = []
    for i in range(n):
        node = transition[i] if i < len(transition) else None
        ts = _to_iso(timestamps[i]) if i < len(timestamps) else None
        score = float(agent_scores[i]) if i < len(agent_scores) else None
        rows.append((i, node, ts, score))
    return rows

def _msg_role(msg: BaseMessage) -> str:
    if isinstance(msg, HumanMessage): return "human"
    if isinstance(msg, AIMessage): return "ai"
    if isinstance(msg, SystemMessage): return "system"
    # Fallback to msg.type (e.g., "tool", "function", etc.)
    return getattr(msg, "type", "unknown")

def _msg_content_as_text(content: Any) -> str:
    # LangChain can store content as str or list[dict]. Persist a readable string.
    if isinstance(content, str):
        return content
    try:
        import json as _json
        return _json.dumps(content, ensure_ascii=False)
    except Exception:
        return str(content)

# ---------- PUBLIC API ----------

def save_state_to_aiven(state: Dict[str, Any], engine: Optional[Engine] = None) -> None:
    """
    Persist a single run snapshot to Aiven PostgreSQL:
      - runs (process-level)
      - run_timeline (aligned time series)
      - run_messages (for semantic evaluation later)
      - run_explanations (for semantic evaluation later)
    Keeps it idempotent per process_id: upserts runs, replaces child rows on each call.
    """
    required = ["process_id", "topic", "product", "transition", "timestamps", "agent_scores"]
    for k in required:
        if k not in state:
            raise ValueError(f"state missing required key: '{k}'")

    process_id = int(state["process_id"])
    topic = str(state["topic"])
    product = state["product"]  # dict, stored as JSONB
    finished = bool(state.get("finished", False))  # uusi kenttä

    transition = state.get("transition", []) or []
    timestamps = state.get("timestamps", []) or []
    agent_scores = state.get("agent_scores", []) or []
    product_ranking = state.get("product_ranking", {}) or {}
    messages = state.get("messages", []) or []
    explanations = state.get("explanation", []) or []

    engine = engine or get_engine()
    init_db(engine)

    time_rows = _align_time_series(transition, timestamps, agent_scores)

    try:
        with engine.begin() as conn:
            # Upsert into runs
            # Portable upsert using PostgreSQL ON CONFLICT:
            # conn.exec_driver_sql(
            #     """
            #     INSERT INTO runs (process_id, topic, product)
            #     VALUES (:process_id, :topic, CAST(:product AS JSONB))
            #     ON CONFLICT (process_id)
            #     DO UPDATE SET topic = EXCLUDED.topic,
            #                   product = EXCLUDED.product,
            #                   updated_at = now()
            #     """,
            #     {"process_id": process_id, "topic": topic, "product": product, "finished": finished},
            # )

            ins = pg_insert(runs).values(
            process_id=process_id,
            topic=topic,
            product=product,
            product_ranking=product_ranking,     # dict -> JSONB ok
            finished=finished,   # ✅ talletetaan myös finished
            )
            upsert = ins.on_conflict_do_update(
                index_elements=[runs.c.process_id],
                set_=dict(
                    topic=ins.excluded.topic,
                    product=ins.excluded.product,
                    product_ranking=ins.excluded.product_ranking,
                    finished=ins.excluded.finished,  # päivittyy upsertissa
                    updated_at=func.now(),
                )
            )
            conn.execute(upsert)

            # Clear existing child rows for this run (simple and reliable)
            conn.execute(run_timeline.delete().where(run_timeline.c.process_id == process_id))
            conn.execute(run_messages.delete().where(run_messages.c.process_id == process_id))
            conn.execute(run_explanations.delete().where(run_explanations.c.process_id == process_id))

            # Insert timeline
            if time_rows:
                conn.execute(
                    run_timeline.insert(),
                    [
                        {
                            "process_id": process_id,
                            "step_index": i,
                            "node": node,
                            "ts": ts,
                            "agent_score": score,
                        }
                        for (i, node, ts, score) in time_rows
                    ],
                )

            # Insert messages (role, content)
            if messages:
                # Keep only simple fields now; you can add embeddings later offline.
                payload = []
                for i, msg in enumerate(messages):
                    role = _msg_role(msg)
                    content = _msg_content_as_text(getattr(msg, "content", ""))
                    meta = {}
                    # If you want to store raw message dict:
                    try:
                        meta = {"message_type": getattr(msg, "type", None)}
                    except Exception:
                        pass
                    payload.append({
                        "process_id": process_id,
                        "turn_index": i,
                        "role": role,
                        "content": content,
                        "meta": meta,
                    })
                conn.execute(run_messages.insert(), payload)

            # Insert explanations (key + text)
            if explanations:
                exp_rows = []
                for i, item in enumerate(explanations):
                    key = None
                    text = None
                    meta = None
                    if isinstance(item, dict):
                        key = item.get("key")
                        text = item.get("text") or item.get("explanation") or ""
                        meta = {k: v for k, v in item.items() if k not in ("key", "text", "explanation")}
                    else:
                        text = str(item)
                    if text:
                        exp_rows.append({
                            "process_id": process_id,
                            "idx": i,
                            "key": key,
                            "text": text,
                            "meta": meta,
                        })
                if exp_rows:
                    conn.execute(run_explanations.insert(), exp_rows)

    except SQLAlchemyError as e:
        # Bubble up a clear error with context
        raise RuntimeError(f"Failed to save state for process_id={process_id}: {e}") from e

