
import json
import logging

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
    inference,
    room_io,
    function_tool, 
    RunContext
)

load_dotenv()
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("english-agent")

TTS_PROFILES = {
    "default": {"model": "cartesia/sonic-3", "language": "en"},
    "hindi": {"model": "cartesia/sonic-3-latest", "language": "hi"},
}


def get_tts_profile(job_metadata: str) -> dict[str, str]:
    """Read an allowlisted voice profile from LiveKit job metadata."""
    try:
        metadata = json.loads(job_metadata or "{}")
    except (TypeError, json.JSONDecodeError):
        metadata = {}

    voice = metadata.get("voice") if isinstance(metadata, dict) else None
    if not isinstance(voice, str):
        voice = None
    return TTS_PROFILES.get(voice, TTS_PROFILES["default"])


class VoiceAssistant(Agent):
    def __init__(self, language: str):
        instructions = (
            "You are Neosh's voice assistant. Use the knowledge "
            "search tool for Neosh product questions. Answer only "
            "from retrieved evidence and abstain when information "
            "is missing. Speak naturally and keep answers concise."
            "When the user asks to show or hide an interface element, "
            "call agent_action_set_ui_visibility. Use target='bottle' for the "
            "bottle dialog, or a screen target such as 'product-gallery', "
            "'product-detail', 'orders', 'cart', 'image-gallery', 'terms', "
            "or 'display'. Set visible=true to show and false to hide. "
        )

        super().__init__(instructions=instructions)

    
    @function_tool()
    async def agent_action_set_ui_visibility(
        self,
        context: RunContext,
        target: str,
        visible: bool,
    ) -> str:
        """Show or hide an allowlisted frontend UI element.

        target may be 'bottle', 'display', 'product-gallery', 'image-gallery',
        'product-detail', 'orders', 'cart', or 'terms'.
        Set visible=true to show and false to hide.
        """

        allowed_targets = {
            "bottle",
            "display",
            "product-gallery",
            "image-gallery",
            "product-detail",
            "orders",
            "cart",
            "terms",
        }
        if target not in allowed_targets:
            return f"Unsupported interface target: {target}"

        room = context.session.room_io.room

        # For this prototype, use the connected browser participant.
        participants = list(room.remote_participants.values())

        if not participants:
            return "Unable to update the interface: no frontend participant is connected."

        destination_identity = participants[0].identity

        try:
            response = await room.local_participant.perform_rpc(
                destination_identity=destination_identity,
                method="updateUIVisibility",
                payload=json.dumps({"target": target, "visible": visible}),
                response_timeout=5,
            )

            print(f"Tried calling updateUIVisibility for {target}")

            result = json.loads(response)

            if not result.get("success"):
                return f"The visibility update failed for {target}."

            return f"{target} is now {'visible' if visible else 'hidden'}."

        except Exception as exc:
            logger.exception("Failed to execute UI visibility RPC")
            return f"Unable to update {target}: {exc}"

    
    @function_tool()
    async def search_knowledge_base(
        self,
        context: RunContext,
        question: str,
    ) -> str:
        """Search Neosh product information to answer factual questions."""

        print(f"Knowledge search requested: {question}")

        return (
            "Neosh offers three children's book types: "
            "Mandala Drawing Book, Creative Activity Book, and "
            "Storytelling and Illustration Book. "
            "Neosh offers a children water bottles"
            "It offers Polished Copper Bottle and Hammered Copper Bottle. "
            "Prices and sales figures are not available."
            
        )

async def entrypoint(ctx: JobContext):
    tts_profile = get_tts_profile(ctx.job.metadata)
    language = tts_profile["language"]

    session = AgentSession(
        stt=inference.STT(
            model="deepgram/nova-3",
            language="multi",
        ),
        llm=inference.LLM(
            model="google/gemma-4-31b-it",
        ),
        tts=inference.TTS(
            model=tts_profile["model"],
            language=language,
        ),
    )

    await session.start(
        agent=VoiceAssistant(language),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            text_output=room_io.TextOutputOptions(
                sync_transcription=True,
            ),
        ),
    )

    await session.generate_reply(
        instructions=(
            "Greet the user in English and ask how you can help."
            if language == "en"
            else "Greet the user in Hindi and ask how you can help."
        )
    )


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(entrypoint_fnc=entrypoint, agent_name="english-agent")
    )
