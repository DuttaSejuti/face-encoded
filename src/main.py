from fastapi import FastAPI
from src.app.core.config import PROJECT_NAME, API_V1_STR, get_async_db_url

app = FastAPI(
    title=PROJECT_NAME,
    openapi_url=f"{API_V1_STR}/openapi.json"
)

@app.get("/")
def root():
    return {"message": "Face Encoding API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
