import os
import json
from dotenv import load_dotenv
import google.ai.generativelanguage as gl
from google.api_core.client_options import ClientOptions

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "models/gemini-flash-latest")

CLIENT_OPTIONS = ClientOptions(api_key=API_KEY) if API_KEY else None


def get_ai_response_stream(messages, files=None):
    if not API_KEY:
        yield f"data: {json.dumps({'text': 'No GEMINI_API_KEY configured. Set GEMINI_API_KEY in .env.'})}\n\n"
        yield "data: [DONE]\n\n"
        return

    prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
    if files:
        file_text = "\n\n".join(files)
        prompt += f"\n\nAttached files:\n{file_text}"

    try:
        client = gl.GenerativeServiceClient(client_options=CLIENT_OPTIONS)
        request = {
            "model": MODEL_NAME,
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }
        response = client.generate_content(request=request)

        text = ""
        if response.candidates:
            candidate = response.candidates[0]
            content = getattr(candidate, "content", None)
            if content:
                if hasattr(content, "text") and content.text:
                    text = content.text
                else:
                    parts = getattr(content, "parts", []) or []
                    text = "".join(getattr(part, "text", "") for part in parts)

        if not text:
            text = "No response received from the AI model. Please try again."

        yield f"data: {json.dumps({'text': text})}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'text': '❌ Error: ' + str(e)})}\n\n"
        yield "data: [DONE]\n\n"