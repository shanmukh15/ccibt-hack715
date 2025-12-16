from typing import Any, Dict, List, Optional
import json
import uuid
from fastapi import FastAPI, HTTPException, Query
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types as genai_types

from app.agent import root_agent  # uses your existing agent graph
from app.agents.user_registry import get_user_profile
from app.agents.state import init_session_state, get_session_state

app = FastAPI(title="ADK Web App")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")


class CreateSessionRequest(BaseModel):
    user_id: str


class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    message: str
    metadata: Optional[Dict[str, Any]] = None


def _runner() -> Runner:
    return Runner(agent=root_agent, session_service=session_service, app_name="web")


def _extract_text(event: Any) -> str:
    text_chunks: List[str] = []
    content = getattr(event, "content", None)
    if content and getattr(content, "parts", None):
        for part in content.parts:
            val = getattr(part, "text", None)
            if val:
                text_chunks.append(val)
    return "".join(text_chunks)


@app.post("/session")
async def create_session(req: CreateSessionRequest) -> Dict[str, str]:
    sess = await asyncio.to_thread(
        session_service.create_session_sync, user_id=req.user_id, app_name="web"
    )
    conversation_store[sess.id] = []
    profile = get_user_profile(req.user_id)
    if profile:
        session_user_profile[sess.id] = profile
        init_session_state(sess.id, user_profile=profile)
    return {"session_id": sess.id}


@app.post("/chat")
async def chat(req: ChatRequest) -> Dict[str, Any]:
    if req.session_id not in conversation_store:
        raise HTTPException(status_code=404, detail="Unknown session_id")

    conversation_store[req.session_id].append({"role": "user", "content": req.message})

    message = genai_types.Content(
        role="user",
        parts=[
            genai_types.Part.from_text(text=req.message),
            genai_types.Part.from_text(
                text=json.dumps({
                    "session_state": get_session_state(req.session_id)
                })
            ),
        ]
    )

    def _blocking_run() -> str:
        parts: List[str] = []
        for event in _runner().run(
            new_message=message,
            user_id=req.user_id,
            session_id=req.session_id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        ):
            delta = _extract_text(event)
            if delta:
                parts.append(delta)
        return "".join(parts)

    answer = await asyncio.to_thread(_blocking_run)
    conversation_store[req.session_id].append({"role": "assistant", "content": answer})
    return {"answer": answer}


@app.get("/chat/stream")
async def chat_stream(
    session_id: str = Query(...),
    user_id: str = Query(...),
    q: str = Query(..., description="User message"),
):
    if session_id not in conversation_store:
        raise HTTPException(status_code=404, detail="Unknown session_id")

    conversation_store[session_id].append({"role": "user", "content": q})
    message = genai_types.Content(
        role="user",
        parts=[
            genai_types.Part.from_text(text=q),
            genai_types.Part.from_text(
                text=json.dumps({
                    "session_state": get_session_state(session_id)
                })
            ),
        ]
    )

    async def sse() -> Any:
        queue: asyncio.Queue[str] = asyncio.Queue()

        loop = asyncio.get_running_loop()

        def producer() -> None:
            parts: List[str] = []
            for event in _runner().run(
                new_message=message,
                user_id=user_id,
                session_id=session_id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            ):
                delta = _extract_text(event)
                if delta:
                    parts.append(delta)
                    asyncio.run_coroutine_threadsafe(
                        queue.put(json.dumps({"delta": delta})), loop
                    )
            final_answer = "".join(parts)
            conversation_store[session_id].append(
                {"role": "assistant", "content": final_answer}
            )
            asyncio.run_coroutine_threadsafe(
                queue.put(json.dumps({"final": final_answer})), loop
            )

        # Start the blocking producer in a thread without awaiting, so we can stream concurrently.
        _ = loop.run_in_executor(None, producer)

        while True:
            item = await queue.get()
            yield f"data: {item}\n\n"
            if item and json.loads(item).get("final") is not None:
                break

    return StreamingResponse(sse(), media_type="text/event-stream")


@app.get("/history")
async def history(session_id: str) -> Dict[str, Any]:
    if session_id not in conversation_store:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    return {"messages": conversation_store[session_id]}


@app.get("/")
async def read_index():
    return FileResponse("frontend/dist/index.html")
