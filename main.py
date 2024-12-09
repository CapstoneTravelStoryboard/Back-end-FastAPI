from fastapi import FastAPI, HTTPException

from routers import recommends

app = FastAPI()
app.include_router(recommends.router, prefix="/recommend", tags=["recommend"])


@app.get("/")
async def root():
    return {"message": "Hello World"}