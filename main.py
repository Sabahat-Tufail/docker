from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, json, requests
from dotenv import load_dotenv
from langfuse import Langfuse

# ------------------ ENV SETUP ------------------
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path, override=True)

API_KEY = os.getenv("API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ------------------ App Setup ------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ------------------ Langfuse ------------------
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

# ------------------ OpenRouter ------------------
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
}

# ------------------ Routes ------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/chat/stream")
async def stream_chat(request: Request):
    # ----------- API Key Auth -----------
    key = request.headers.get("x-api-key")
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API Key")

    # ----------- Extract Conversation -----------
    data = await request.json()
    conversation = data if isinstance(data, list) else data.get("conversation", [])
    if not conversation:
        return {"error": "Empty conversation"}

    # ----------- Langfuse Trace -----------
    trace_id = langfuse.create_trace_id()
    print(f"Langfuse trace started: {trace_id}")

    # ----------- Extract Last User Input -----------
    user_input = ""
    for msg in reversed(conversation):
        if msg.get("role") == "user" and msg.get("content"):
            user_input = msg["content"]
            break
    if not user_input:
        return {"error": "No valid user message found"}

    # ----------- Fetch Langfuse Prompt -----------
    system_prompt = langfuse.get_prompt("system/default")  # replace with your prompt path
    system_content = system_prompt.get("text", "You are a helpful assistant.")  # fallback

    # ----------- Streaming Response -----------
    def event_stream():
        collected_output = ""
        try:
            payload = {
                "model": "meta-llama/llama-3.1-70b-instruct",
                "messages": [
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_input}
                ],
                "max_tokens": 200,
                "stream": True,
            }

            with requests.post(OPENROUTER_URL, headers=HEADERS, json=payload, stream=True) as r:
                for line in r.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8")
                        if decoded_line.startswith("data:"):
                            data_str = decoded_line[len("data:"):].strip()
                            if data_str == "[DONE]":
                                yield "data: [DONE]\n\n"
                                break
                            try:
                                json_data = json.loads(data_str)
                                text = json_data["choices"][0]["delta"].get("content", "")
                                if text:
                                    collected_output += text
                                    yield f"data: {json.dumps({'content': text})}\n\n"
                            except:
                                continue
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            print(f"Trace ID: {trace_id}")
            print(f"User Input: {user_input}")
            print(f"Model Output (truncated): {collected_output[:300]}")

    return StreamingResponse(event_stream(), media_type="text/event-stream")
