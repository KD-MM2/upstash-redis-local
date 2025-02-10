#cython: annotation_typing=False
import base64
import json
import os
import time
from typing import Any, Dict, List, Optional

import redis
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse

load_dotenv()

app = FastAPI()
local_redis = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
)


# Validate token (mock for compatibility; adjust as needed)
def validate_token(token: str):
    # Implement actual token validation logic if required
    return True  # Bypass for local use


# Parse command from URL path (e.g., /SET/foo/bar → ["SET", "foo", "bar"])
def parse_command_from_path(path: str) -> List[str]:
    parts = path.strip("/").split("/")
    return [part.replace("_", " ") for part in parts]  # Handle URL-encoded spaces


# Execute Redis command and format response
def execute_redis_command(command: List[str], body: Optional[bytes] = None) -> Any:
    try:
        cmd = command[0].upper()
        args = command[1:]

        # Handle POST data as last argument
        if body:
            args.append(body.decode("utf-8", "replace"))

        # Execute command
        result = local_redis.execute_command(cmd, *args)

        # Format response
        if result is True:
            converted_result = "OK"  # Map Redis "OK" to string
        elif result is None:
            converted_result = None  # Keep null for JSON
        elif isinstance(result, bytes):
            converted_result = result.decode("utf-8", "replace")
        elif isinstance(result, list):
            converted_result = [
                (
                    "OK"
                    if item is True
                    else (
                        item.decode("utf-8", "replace")
                        if isinstance(item, bytes)
                        else item
                    )
                )
                for item in result
            ]
        else:
            converted_result = result
        return {"result": converted_result}
    except redis.RedisError as e:
        return {"error": str(e)}  # Return error message


# Handle base64 and RESP2 encoding
def encode_response(data: Any, encoding: Optional[str], response_format: Optional[str]):
    if response_format == "resp2":
        # Convert to RESP2 format (simplified example)
        if isinstance(data, str):
            return f"+{data}\r\n".encode()
        elif isinstance(data, int):
            return f":{data}\r\n".encode()
        # Add more types as needed
    elif encoding == "base64":
        if isinstance(data, str):
            return base64.b64encode(data.encode()).decode()
    return data


# Root endpoint for commands via path
@app.api_route("/{rest_of_path:path}", methods=["GET", "POST", "PUT", "HEAD"])
async def handle_command(
    request: Request,
    rest_of_path: str,
    _token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    upstash_encoding: Optional[str] = Header(None),
    upstash_response_format: Optional[str] = Header(None),
):
    # Validate token
    token = _token or (authorization.split("Bearer ")[1] if authorization else None)
    if not token or not validate_token(token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Parse command
    if request.method == "POST" and "pipeline" in rest_of_path:
        return await handle_pipeline(request)
    if request.method == "POST" and "multi-exec" in rest_of_path:
        return await handle_transaction(request)

    command = parse_command_from_path(rest_of_path)
    body = await request.body() if request.method == "POST" else None

    # Execute command
    response_data = execute_redis_command(command, body)
    if "error" in response_data:
        raise HTTPException(status_code=400, detail=response_data["error"])

    # Apply encoding
    result = response_data["result"]
    encoded_result = encode_response(result, upstash_encoding, upstash_response_format)

    return JSONResponse(content={"result": encoded_result})


# Handle pipeline endpoint
async def handle_pipeline(request: Request):
    commands = await request.json()
    responses = []
    for cmd in commands:
        response = execute_redis_command(cmd)
        responses.append(response)
    return JSONResponse(content=responses)


# Handle transaction endpoint
async def handle_transaction(request: Request):
    commands = await request.json()
    pipe = local_redis.pipeline(transaction=True)
    for cmd in commands:
        pipe.execute_command(cmd[0], *cmd[1:])
    try:
        results = pipe.execute()
        responses = [{"result": res} for res in results]
        return JSONResponse(content=responses)
    except redis.RedisError as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)


# Monitor endpoint (SSE)
@app.post("/monitor")
async def monitor_endpoint():
    pubsub = local_redis.pubsub()
    pubsub.monitor()

    def event_stream():
        try:
            for message in pubsub.listen():
                if message["type"] == "monitor":
                    yield f"data: {json.dumps(message)}\n\n"
        finally:
            pubsub.close()

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# Pub/sub endpoints (simplified)
@app.post("/subscribe/{channel}")
async def subscribe(channel: str):
    pubsub = local_redis.pubsub()
    pubsub.subscribe(channel)

    def event_stream():
        try:
            for message in pubsub.listen():
                if message["type"] == "message":
                    yield f"data: {message['data']}\n\n"
        finally:
            pubsub.close()

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/publish/{channel}/{message}")
async def publish(channel: str, message: str):
    result = local_redis.publish(channel, message)
    return JSONResponse(content={"result": result})


def main() -> int:
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("SERVER_HOST", "0.0.0.0"),
        port=int(os.getenv("SERVER_PORT", 3000)),
        workers=int(os.getenv("SERVER_WORKERS", 1)),
    )
    return 0
