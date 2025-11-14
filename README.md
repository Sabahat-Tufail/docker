Sure! Here’s a **README** specifically for your **Docker repo** for the FastAPI chatbot backend:

---

# FastAPI Chatbot (Docker)

This repository contains a **containerized FastAPI backend** for a real-time streaming chatbot. It is designed to be deployed with **Docker** or **Docker Compose**, providing a public URL for the chatbot frontend or widget.

---

## **Repo Structure**

```
docker/
├─ main.py               # FastAPI backend
├─ .env.example          # Example environment variables (do NOT include real secrets)
├─ requirements.txt      # Python dependencies
├─ Dockerfile            # To build the container
└─ docker-compose.yml    # Optional: for easy local setup
```

---

## **Setup**

### 1️⃣ Environment Variables

Copy `.env.example` to `.env` and fill in your secret keys:

```bash
cp .env.example .env
```

Example `.env.example`:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
API_KEY=your_secret_api_key
```

---

### 2️⃣ Install Dependencies (Optional for Local Testing)

```bash
pip install -r requirements.txt
```

---

## **3️⃣ Running with Docker**

### Build the Docker image:

```bash
docker build -t fastapi-chatbot .
```

### Run the container:

```bash
docker run -p 8000:8000 --env-file .env fastapi-chatbot
```

* Backend will be available at:

```
http://localhost:8000
```

### Using Docker Compose

```bash
docker-compose up --build
```

* This will build the container and map port `8000` to your local machine.

---

## **Backend Endpoints**

### 1. Root

```http
GET /
```

Response:

```json
{"message": "Backend is running. Use /chat/stream to interact."}
```

### 2. Health Check

```http
GET /health
```

Response:

```json
{"status": "ok"}
```

### 3. Chat Streaming

```http
POST /chat/stream
```

**Headers:**

* `x-session-id`: unique session ID per browser
* `reset` (optional): `true` to reset conversation

**Body Example:**

```json
{
  "conversation": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help you?"}
  ]
}
```

* Streams AI response via **Server-Sent Events (SSE)**.
* Handles session-based conversation tracking.
* Resets backend conversation trace if `reset=true`.

--
