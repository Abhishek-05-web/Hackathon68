from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import weather_service


app = FastAPI(title="WeatherGPT API")


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://abhishek-05-web.github.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODEL
# ============================================================

class ChatRequest(BaseModel):
    question: str
    latitude: float
    longitude: float


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health():
    return {
        "status": "WeatherGPT backend is running"
    }


# ============================================================
# CHAT API
# ============================================================

@app.post("/chat")
def chat(request: ChatRequest):

    try:

        data, decoded = weather_service.get_weather(
            request.latitude,
            request.longitude,
            request.question
        )

        answer = weather_service.natural_response(
            data,
            request.question,
            decoded
        )

        return {
            "answer": answer,
            "location": data.get("location"),
            "requested_date": data.get("requested_date"),
            "warnings": data.get(
                "warnings",
                {"warnings": []}
            )
        }

    except Exception as error:

        print("WeatherGPT ERROR:", error)

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# FRONTEND
# IMPORTANT: KEEP THIS AFTER API ROUTES
# ============================================================

FRONTEND_DIR = (
    Path(__file__).resolve().parent.parent
    / "Frontend68"
)

app.mount(
    "/",
    StaticFiles(
        directory=str(FRONTEND_DIR),
        html=True
    ),
    name="frontend"
)