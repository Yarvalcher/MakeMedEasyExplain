import os
import re
import sys
import asyncio
from pathlib import Path

# Add project root to sys.path to allow absolute imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Load MMEE_Agent/.env variables manually into os.environ
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            os.environ[key.strip()] = val.strip()

from flask import Flask, render_template, request, jsonify
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from MMEE_Agent.agent import root_agent
from MMEE_Agent.tools.github_tool import sync_wiki_from_github

# Synchronize local knowledge base with the GitHub Wiki at startup (GitOps sync loop)
local_kb_dir = Path(__file__).resolve().parent.parent / "knowledge_base"
if "pytest" not in sys.modules and not os.environ.get("MMEE_NO_SYNC"):
    sync_msg = sync_wiki_from_github(str(local_kb_dir))
    print(f"🔄 GitOps Startup Sync: {sync_msg}")
else:
    print("🔄 GitOps Startup Sync: Skipped (Testing/No-Sync environment detected)")

app = Flask(__name__, template_folder='templates')

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    storage_uri="memory://",
)

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Too many requests. Rate limit exceeded. Please wait a moment."}), 429

def slugify(text: str) -> str:
    """Helper to generate a clean snake_case filename slug matching agent saves."""
    return re.sub(r'[^a-zA-Z0-9_]', '', text.lower().strip().replace(" ", "_").replace("-", "_"))

async def run_agent_pipeline(query: str):
    """Executes the ADK multi-agent pipeline using the Runner engine with backoff retries for rate limits."""
    session_service = InMemorySessionService()
    # Create unique session for the query transaction
    session_id = f"sess_{os.urandom(4).hex()}"
    await session_service.create_session(app_name="MakeMedEasyExplain", user_id="user", session_id=session_id)
    
    runner = Runner(agent=root_agent, app_name="MakeMedEasyExplain", session_service=session_service)
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            final_response = ""
            last_text = ""
            # Collect asynchronous event streams from the runner
            async for event in runner.run_async(
                user_id="user",
                session_id=session_id,
                new_message=types.Content(role="user", parts=[types.Part.from_text(text=query)])
            ):
                if event.content and event.content.parts:
                    txt = event.content.parts[0].text
                    if txt:
                        last_text = txt
                if event.is_final_response():
                    if event.content and event.content.parts:
                        final_response = event.content.parts[0].text
            return final_response or last_text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                if attempt < max_retries - 1:
                    sleep_time = 4 * (attempt + 1)
                    print(f"⚠️ Gemini API rate limited (429). Retrying in {sleep_time} seconds (Attempt {attempt + 1}/{max_retries})...")
                    await asyncio.sleep(sleep_time)
                    continue
            raise e

@app.route('/')
def index():
    return render_template('index.html')

def is_refusal(text: str) -> bool:
    """Helper to detect if the agent response is a refusal/rejection."""
    if not text:
        return True
    text_lower = text.lower()
    refusal_phrases = [
        "cannot respond to that",
        "cannot help you with",
        "unable to respond",
        "unable to help",
        "ask a different question",
        "not appropriate",
        "against my safety",
        "safety guidelines",
        "inappropriate content",
        "request blocked",
        "error: no query metadata",
        "error: could not generate"
    ]
    return any(phrase in text_lower for phrase in refusal_phrases)

@app.route('/translate', methods=['POST'])
@limiter.limit("5 per minute")
async def translate():
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({"error": "Query cannot be empty."}), 400
        
    try:
        # Track files in local KB before running pipeline
        files_before = set(local_kb_dir.glob("*.md")) if local_kb_dir.exists() else set()

        # Await the async pipeline directly on Flask's native event loop
        response_text = await run_agent_pipeline(query)
        
        # Track files in local KB after running pipeline
        files_after = set(local_kb_dir.glob("*.md")) if local_kb_dir.exists() else set()
        new_files = files_after - files_before

        # Determine if it's approved and what the filename/sync status should be
        approved = not is_refusal(response_text)
        
        if not approved:
            filename = None
            sync_status = "Not saved (Refusal / Safety Block)"
        elif new_files:
            filename = list(new_files)[0].name
            sync_status = "Saved to local cache & pushed to GitHub wiki."
        else:
            filename = None
            sync_status = "Loaded from local cache."

        # Extract clean title from query
        title = query.replace("what is ", "").replace("difference between ", "").title()
        
        return jsonify({
            "analogy": response_text,
            "title": title,
            "filename": filename,
            "sync_status": sync_status,
            "approved": approved
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()  # Print the full error stack trace to the PowerShell terminal
        return jsonify({"error": f"Agent Pipeline failed: {str(e)}"}), 500

if __name__ == '__main__':
    # Start local web dashboard
    port = int(os.getenv("PORT", 8000))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
