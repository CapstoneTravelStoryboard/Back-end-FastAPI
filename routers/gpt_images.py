import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Thread

import requests
from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from openai import OpenAI
from config.settings import OPENAI_API_KEY
from utils.s3_image import download_image_from_url, upload_to_s3

client = OpenAI(api_key=OPENAI_API_KEY)

router = APIRouter()


class ImageGenerationRequest(BaseModel):
    storyboard_id : int # 스토리보드 ID
    order_num : int # 씬 순서
    scene_description: str  # 씬 설명
    destination: str  # 목적지
    purpose: str  # 여행 목적
    companion: str  # 동행자 종류
    companion_count: int  # 동행자 수
    season: str  # 계절
    image_urls: List[str]  # 참조 이미지 URL 목록


# class ImageGenerationResponse(BaseModel):
#     image_url: List[str]  # 생성된 이미지 URL 리스트



# DALL·E 3를 사용하여 이미지를 생성하고 저장하는 함수
def generate_and_save_image_dalle(storyboard_id, order_num, scene_description, destination, purpose, companion, companion_count, season,
                                  image_urls):
    """
    DALL·E 3 모델을 사용하여 스토리보드 씬 이미지를 생성하고 저장하는 함수입니다.

    이 함수는 주어진 씬 설명과 여행 목적지, 목적, 동행자 정보 등을 기반으로 이미지 생성 프롬프트를 구성합니다.
    이미지는 DALL·E 3 모델을 사용하여 생성되며, 생성된 이미지는 지정된 경로에 저장됩니다.
    이미지에는 오버레이, 사용자 인터페이스 요소, 카메라 장비 또는 촬영 과정의 흔적이 없어야 하며,
    깨끗하고 자연스러운 장면만을 포함해야 합니다.

    Args:
        scene_description (str): 이미지 생성의 기반이 될 씬 설명.
        destination (str): 씬의 배경이 되는 여행 목적지.
        purpose (str): 여행의 목적.
        companion (str): 동행자의 종류(예: 친구, 가족 등).
        companion_count (int): 동행자의 수.
        season (str): 여행지 계절
        image_urls (list): 장면의 시각적 요소를 참고할 수 있는 이미지 URL 리스트.

    Returns:
        None: 생성된 이미지를 지정된 경로에 저장합니다.
    """

    prompt = f"""
        You are an expert in generating images for storyboards. 
        Create a dynamic, cinematic image based on a video storyboard scene description: {scene_description}. 
        This scene is set in {destination}, where the purpose of the trip is {purpose}. 
        The traveler is accompanied by {companion_count} {companion}(s). 
        The scene takes place during the {season} season, which should influence the atmosphere, colors, and overall mood of the image. 
        Reference the following images of the destination for accuracy in visual elements: {', '.join(image_urls)}.
        Under no circumstances should the image include overlays, user interface elements, camera equipment, or any signs of filming processes. 
        The image must solely focus on the scene itself, providing a natural, immersive view that resembles the final, edited shot of a travel video.
        """

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1024",
    )

    image_url = response.data[0].url

    # 이미지 다운로드 및 저장
    # UUID를 사용해 고유한 파일 이름 생성
    unique_id = str(uuid.uuid4())
    local_image_path = f'temp_image_{order_num}_{unique_id}.jpg'
    download_image_from_url(image_url, local_image_path)
    upload_to_s3(local_image_path, f'images/storyboard/{storyboard_id}/{order_num}.jpg')
    # upload_to_s3(local_image_path, 'images.jpg')

    return image_url


def generate_images_multithreaded(requests: List[ImageGenerationRequest], max_threads: int = 7) -> List[str]:
    """
    generate_and_save_image_dalle 함수를 멀티스레드로 처리하는 함수.

    Args:
        requests (List[ImageGenerationRequest]): 이미지 생성 요청 리스트
        max_threads (int): 동시에 실행할 최대 스레드 수.

    Returns:
        List[str]: 생성된 이미지 URL 리스트.
    """
    results = []

    def task(request):
        return generate_and_save_image_dalle(
            storyboard_id=request.storyboard_id,
            order_num=request.order_num,
            scene_description=request.scene_description,
            destination=request.destination,
            purpose=request.purpose,
            companion=request.companion,
            companion_count=request.companion_count,
            season=request.season,
            image_urls=request.image_urls
        )

    # ThreadPoolExecutor를 사용하여 멀티스레드 처리
    with ThreadPoolExecutor(max_threads) as executor:
        future_to_request = {executor.submit(task, req): req for req in requests}

        for future in as_completed(future_to_request):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error processing request {future_to_request[future]}: {e}")

    return results




@router.post("/images")
def generate_images_endpoint(request: List[ImageGenerationRequest]):
    print("Request:", request)
    try:
        responses = generate_images_multithreaded(requests=request)
        # print the generated image URLs for testing
        print("Generated Image URLs:", responses)
        return responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch image generation failed: {str(e)}")