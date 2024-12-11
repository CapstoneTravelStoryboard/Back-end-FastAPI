# from fastapi import FastAPI, HTTPException

from routers import recommends, storyboards, images, gpt_images

import logging
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from utils.s3_image import download_image_from_url, upload_to_s3

app = FastAPI()
app.include_router(recommends.router, prefix="/recommend", tags=["recommend"])
app.include_router(storyboards.router, prefix="/fastapi", tags=["storyboards"])
# app.include_router(images.router, prefix="/fastapi", tags=["images"])
app.include_router(gpt_images.router, prefix="/fastapi", tags=["images"])

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
    logging.error(f"{request}: {exc_str}")
    content = {'status_code': 10422, 'message': exc_str, 'data': None}
    return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


@app.get("/")
async def root():
    return {"message": "Hello World"}
