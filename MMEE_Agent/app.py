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

app = Flask(__name__, template_folder='templates')

def slugify(text: str) -> str:
    """Helper to generate a clean snake_case filename slug matching agent saves."""
    return re.sub(r'[^a-zA-Z0-9_]', '', text.lower().strip().replace(" ", "_").replace("-", "_"))

async def run_agent_pipeline(query: str):
    """Executes the ADK multi-agent pipeline using the Runner engine."""
    session_service = InMemorySessionService()
    # Create unique session for the query transaction
    session_id = f"sess_{os.urandom(4).hex()}"
    await session_service.create_session(app_name="MakeMedEasyExplain", user_id="user", session_id=session_id)
    
    runner = Runner(agent=root_agent, app_name="MakeMedEasyExplain", session_service=session_service)
    
    final_response = ""
    # Collect asynchronous event streams from the runner
    async for event in runner.run_async(
        user_id="user",
        session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=query)])
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text
            
    return final_response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({"error": "Query cannot be empty."}), 400
        
    try:
        # Run async pipeline synchronously using standard asyncio.run
        response_text = asyncio.run(run_agent_pipeline(query))
        
        # Check if the output contains save info
        filename = f"{slugify(query[:30])}.md"
        
        # Extract clean title from query
        title = query.replace("what is ", "").replace("difference between ", "").title()
        
        return jsonify({
            "analogy": response_text,
            "title": title,
            "filename": filename,
            "sync_status": "Saved to local cache & pushed to GitHub wiki."
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()  # Print the full error stack trace to the PowerShell terminal
        return jsonify({"error": f"Agent Pipeline failed: {str(e)}"}), 500

if __name__ == '__main__':
    # Start local web dashboard
    port = int(os.getenv("PORT", 8000))
    app.run(host='127.0.0.1', port=port, debug=True, use_reloader=False)
