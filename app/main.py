from fastapi import FastAPI

app = FastAPI(title="AI Telegram News Bot")


@app.get("/health")
def health_check():
    return {"status": "ok"}