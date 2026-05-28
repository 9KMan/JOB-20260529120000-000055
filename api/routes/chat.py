"""Chat routes - streaming chat and thread management."""
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from typing import Optional
import json
import uuid
from datetime import datetime

from ..models import ChatRequest, ChatResponse, ThreadResponse, ChatMessage, MessageRole
from ..middleware.tenant import get_tenant_id

router = APIRouter(prefix="/chat", tags=["chat"])

# In-memory storage for demo (replace with actual storage in production)
threads_store = {}


async def chat_stream_generator(thread_id: str, message: str, tenant_id: str):
    """Generate streaming response for chat message."""
    # Simulate agent processing with streaming chunks
    response_chunks = [
        json.dumps({"type": "status", "content": "processing"}),
        json.dumps({"type": "token", "content": "Thinking"}),
        json.dumps({"type": "token", "content": "..."}),
        json.dumps({"type": "token", "content": " "}),
    ]

    # Simulate response
    response_text = f"AgentFlow processed your message: '{message}'"
    for char in response_text:
        response_chunks.append(json.dumps({"type": "token", "content": char}))

    response_chunks.append(json.dumps({"type": "done", "thread_id": thread_id}))

    for chunk in response_chunks:
        yield f"{chunk}\n"


@router.post("/", response_class=StreamingResponse)
async def send_message(request: ChatRequest, http_request: Request):
    """
    Send a chat message and receive a streaming response.

    Returns streaming response with token-by-token updates.
    """
    tenant_id = get_tenant_id(http_request)
    thread_id = request.thread_id or str(uuid.uuid4())

    return StreamingResponse(
        chat_stream_generator(thread_id, request.message, tenant_id),
        media_type="application/x-ndjson",
        headers={
            "X-Thread-ID": thread_id,
        }
    )


@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(thread_id: str, request: Request):
    """
    Get all messages for a specific thread.

    Args:
        thread_id: Thread identifier

    Returns:
        Thread with messages
    """
    tenant_id = get_tenant_id(request)

    # Get thread from storage (use tenant-specific storage in production)
    storage_key = f"{tenant_id}:{thread_id}"
    if storage_key not in threads_store:
        # Return empty thread for demo
        now = datetime.utcnow()
        return ThreadResponse(
            thread_id=thread_id,
            messages=[],
            created_at=now,
            updated_at=now
        )

    return threads_store[storage_key]


@router.post("/threads/{thread_id}/messages")
async def add_message(
    thread_id: str,
    role: MessageRole,
    content: str,
    request: Request
):
    """Add a message to a thread."""
    tenant_id = get_tenant_id(request)
    storage_key = f"{tenant_id}:{thread_id}"

    message = ChatMessage(
        role=role,
        content=content,
        timestamp=datetime.utcnow()
    )

    if storage_key not in threads_store:
        now = datetime.utcnow()
        threads_store[storage_key] = ThreadResponse(
            thread_id=thread_id,
            messages=[],
            created_at=now,
            updated_at=now
        )

    threads_store[storage_key].messages.append(message)
    threads_store[storage_key].updated_at = datetime.utcnow()

    return {"status": "ok", "message": message}