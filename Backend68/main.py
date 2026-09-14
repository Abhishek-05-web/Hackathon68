from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import weather_service


app = FastAPI(title="WeatherGPT API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Frontend ko backend access dene ke liye
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Frontend se ye data aayega
class ChatRequest(BaseModel):
    question: str
    latitude: float
    longitude: float


# Backend check
@app.get("/")
def home():
    return {
        "status": "WeatherGPT backend is running"
    }


# AI Chat endpoint
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
            "warnings": data.get("warnings", {"warnings": []})
        }

    except Exception as error:

        print("WeatherGPT ERROR:", error)

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )