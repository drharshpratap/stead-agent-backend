
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
            "'notes', or 'display'. Set visible=true to show and false to hide. "
            "For note taking: when the user asks you to take notes, call "
            "agent_action_start_notes. While note taking is active, create a "
            "concise note from each new user contribution with "
            "agent_action_add_note; also capture useful details from the "
            "request that starts note taking. Do not record your own replies. If the "
            "user asks to stop taking notes, call agent_action_stop_notes. "
            "When they ask to show their notes, call agent_action_show_notes. "
        )

        super().__init__(instructions=instructions)
        self.notes_active = False

    
    @function_tool()
    async def agent_action_set_ui_visibility(
        self,
        context: RunContext,
        target: str,
        visible: bool,
    ) -> str:
        """Show or hide an allowlisted frontend UI element.

        target may be 'bottle', 'display', 'product-gallery', 'image-gallery',
        'product-detail', 'orders', 'cart', 'terms', or 'notes'.
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
            "notes",
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

    async def _call_frontend(self, context: RunContext, method: str, payload: dict) -> str:
        room = context.session.room_io.room
        participants = list(room.remote_participants.values())
        if not participants:
            raise RuntimeError("no frontend participant is connected")
        return await room.local_participant.perform_rpc(
            destination_identity=participants[0].identity,
            method=method,
            payload=json.dumps(payload),
            response_timeout=5,
        )

    @function_tool()
    async def agent_action_start_notes(self, context: RunContext) -> str:
        """Start capturing concise notes from what the user says."""
        self.notes_active = True
        try:
            await self._call_frontend(
                context,
                "updateUIVisibility",
                {"target": "notes", "visible": True},
            )
            return "Note taking is on. The Notes notepad is open. Capture the user's key points as notes."
        except Exception as exc:
            logger.exception("Failed to open the Notes window")
            return f"Note taking is on, but the Notes window could not be opened: {exc}"

    @function_tool()
    async def agent_action_add_note(self, context: RunContext, note: str) -> str:
        """Save a concise note based on what the user said."""
        note = note.strip()
        if not note:
            return "No note was added because the note was empty."
        try:
            response = await self._call_frontend(context, "appendNote", {"note": note})
            result = json.loads(response)
            if not result.get("success"):
                return "The note could not be saved."
            return "Note saved to the Notes notepad."
        except Exception as exc:
            logger.exception("Failed to save a note")
            return f"Unable to save the note: {exc}"

    @function_tool()
    async def agent_action_stop_notes(self, context: RunContext) -> str:
        """Stop capturing new notes and keep the saved notes."""
        self.notes_active = False
        return "Note taking is off. The saved notes remain available."

    @function_tool()
    async def agent_action_show_notes(self, context: RunContext) -> str:
        """Open the Notes notepad and retrieve its saved content."""
        try:
            response = await self._call_frontend(
                context,
                "updateUIVisibility",
                {"target": "notes", "visible": True},
            )
            result = json.loads(response)
            notes = result.get("state", {}).get("notes", "")
            return f"The Notes notepad is open. Saved notes:\n{notes or 'There are no saved notes yet.'}"
        except Exception as exc:
            logger.exception("Failed to show saved notes")
            return f"Unable to open the Notes notepad: {exc}"

    
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
