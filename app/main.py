from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Local imports
from api.api import api_router
from config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include the API router
app.include_router(api_router, prefix="/api")

# Home route
@app.get("/")
def root():
    return {"message": "Welcome to the Engagement Analytics API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)