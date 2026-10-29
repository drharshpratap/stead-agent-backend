cat >> ~/.zshrc <<'EOF'

# Stead Agent shortcuts

command 1 : harshtomar@Harshs-MacBook-Air src % uv run python english-agent.

uv add llama-index llama-index-embeddings-huggingface sentence-transformers

py dev

uv run python english-agent.py console

uv run uvicorn stead_agent.token_server:app --app-dir src --reload --port 8000

ui :

npm run dev                                   


http://localhost:8000/api/token?voice=sonic-3-latest


http://localhost:8000/api/token

# app approach
React requests a room token from your Python backend.


The backend generates a short-lived token using the LiveKit API key and secret, then returns the token and LiveKit server URL.


React uses that token to join a LiveKit room. The Python agent worker joins the same room using its server-side credentials.


React streams the user's microphone audio through LiveKit. The agent processes it and publishes its audio response back through the room.


The agent publishes transcript, state, and tool-execution events so React can show what's happening.