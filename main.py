import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from routers import recommends, storyboards, gpt_images

# 로그 설정
logging.basicConfig(
    level=logging.INFO,  # 로그 레벨 설정 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # 로그 출력 형식
    handlers=[
        logging.StreamHandler()  # 로그를 콘솔에 출력
    ],
)

logger = logging.getLogger(__name__)  # 현재 모듈에 맞는 로거 생성

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
    print("Hello World")
    return {"message": "Hello 11World"}
