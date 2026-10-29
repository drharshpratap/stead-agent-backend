
import logging

from dotenv import load_dotenv
from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import sarvam

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("indian-voice-bot")


class IndianVoiceAssistant(Agent):
    def __init__(self):
        super().__init__(
            instructions="""
            You are a friendly Indian-language voice assistant.

            Speak naturally and keep answers concise.
            Respond in Hindi using natural, conversational language.
            If the user speaks English, you may answer in English.
            Avoid long monologues. Ask a short follow-up question
            when appropriate.
            """,
            stt=sarvam.STT(
                language="hi-IN",
                model="saaras:v4",
                mode="transcribe",
            ),
            llm=sarvam.LLM(
                model="sarvam-105b-conversations",
            ),
            tts=sarvam.TTS(
                target_language_code="hi-IN",
                model="bulbul:v3",
                speaker="shubh",
            ),
        )

    async def on_enter(self):
        self.session.generate_reply(
            instructions=(
                "Greet the user in Hindi and ask how you can help."
            )
        )


async def entrypoint(ctx: JobContext):
    logger.info("Connecting to room: %s", ctx.room.name)

    session = AgentSession()

    await session.start(
        agent=IndianVoiceAssistant(),
        room=ctx.room,
    )


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(entrypoint_fnc=entrypoint)
    )
