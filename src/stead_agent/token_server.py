
import json
import os
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
from datetime import timedelta

load_dotenv()

app = FastAPI(title="Stead Agent Token Server")

VOICE_PROFILE_BY_NAME = {
    "default": "default",
    "hindi": "hindi",
    "sonic-3-latest": "hindi",
}
AGENT_NAME = "english-agent"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/token")
async def get_token(voice: str | None = Query(default=None)):
    livekit_url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not all([livekit_url, api_key, api_secret]):
        raise HTTPException(
            status_code=500,
            detail="LiveKit server configuration is missing",
        )

    room_name = f"stead-room-{uuid.uuid4().hex[:8]}"
    participant_identity = f"user-{uuid.uuid4().hex[:8]}"
    selected_voice = VOICE_PROFILE_BY_NAME.get(voice, "default")

    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity(participant_identity)
        .with_name("Stead User")
        .with_room_config(
            api.RoomConfiguration(
                agents=[
                    api.RoomAgentDispatch(
                        agent_name=AGENT_NAME,
                        metadata=json.dumps({"voice": selected_voice}),
                    )
                ]
            )
        )
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            )
        )
        .with_ttl(timedelta(minutes=10))
    )

    return {
        "serverUrl": livekit_url,
        "participantToken": token.to_jwt(),
        "roomName": room_name,
    }
