from typing import List

from fastapi import APIRouter, HTTPException
from openai import OpenAI
from pydantic import BaseModel

from config.settings import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

router = APIRouter()


# GPT를 이용한 스토리보드 생성
def gpt_generate_storyboard(destination, purpose, companions, companion_count, season, title, intro, outro, description,
                            image_urls):
    prompt = f"""
        ### 지시사항 ###
        당신은 여행 영상 스토리보드 생성 전문가입니다. 주어진 정보를 바탕으로 적당한 개수의 씬으로 나눠서 스토리보드를 작성해주세요. 스토리보드 작성 시, 각 항목의 지침을 철저히 따르고 정확하게 작성해주세요. 다음의 지시사항을 따르면 팁을 제공할 것입니다.
        씬을 제외하고는 어떠한 추가적인 내용을 포함하지 말아주세요.

        스토리보드 양식:
        - scene (여기에 씬 순서를 넣어주세요.) "여기에 씬 제목을 넣어주세요.":
            1. **영상**: 이 씬에서 어떤 장면이 나오는지 자세히 설명해주세요. (중요: 자연스럽고 사람과 같은 스타일로 서술)
            2. **화각**: 카메라가 어떤 각도에서 장면을 촬영하는지 설명해주세요. 
            3. **카메라 무빙**: 카메라가 어떻게 움직이는지, 특별한 촬영 기법이 있다면 설명해주세요. (특정 장비나 기법 언급 없이, 단순히 카메라 움직임에만 집중)
            4. **구도**: 화면에서 대상이 어떻게 배치되고, 어떤 느낌을 주는지 설명해주세요.

        ### 예시 ###
        - scene 1 "별과 역사의 시작":
        1. **영상**: 소백산 천문대의 전경과 주변 자연경관을 보여주는 장면으로 시작. 푸른 하늘 아래 우뚝 서 있는 천문대의 모습과 숲으로 둘러싸인 아름다운 경치를 보여줍니다.
        2. **화각**: 드론 카메라로 공중에서 천문대와 주변 풍경을 넓게 담습니다.
        3. **카메라 무빙**: 천문대를 중심으로 둥글게 빙글빙글 돌며 점점 하강해 천문대의 근접 샷으로 이어집니다.
        4. **구도**: 천문대를 중심으로 하늘과 숲이 좌우 대칭으로 배치되어 있고, 천문대가 하늘을 향해 솟아오른 느낌을 줍니다.

        당신의 작업은 여행지와 인간의 움직임이 조화롭게 어우러지는 영상을 기반으로, 스토리보드 내용의 자연스러운 흐름을 만들어주세요. 
        여행지의 매력을 돋보이게 하고, 여행자들의 감정을 담아낼 수 있는 구성으로 작성해주세요.

        여행지: {destination}
        여행지 특성: {description}
        여행 목적: {purpose}
        여행지 계절: {season}
        동행인: {companions} ({companion_count}명)
        제목: {title}
        인트로: {intro}
        아웃트로: {outro}
        이미지 URL: {image_urls}
        """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt}
        ],
        temperature=0.2
    )

    storyboard = response.choices[0].message.content
    # print(storyboard)
    # 씬별로 나누어 저장하기 위한 리스트
    storyboard_scenes = []

    # GPT 응답을 씬별로 분할하여 리스트에 저장
    scenes = storyboard.split("- scene")  # 씬 구분을 위해 "scene"을 기준으로 분할
    for i, scene in enumerate(scenes[1:], 1):  # 첫 번째 항목은 빈 항목이므로 제외하고 처리
        formatted_scene = f"- scene{scene.strip()}"  # 씬 번호는 기존 GPT 응답에서 유지
        storyboard_scenes.append(formatted_scene)

    return storyboard_scenes


def parse_storyboard(data):
    """
    스토리보드 텍스트 데이터를 [[scene 번호, 제목, 세부 정보 딕셔너리], ...] 형태로 변환합니다.

    Args:
        data (list): 스토리보드 데이터 (['- scene1 "제목": ...', ...] 형태)

    Returns:
        list: 정리된 스토리보드 데이터 리스트
              예: [[1, "꽃길을 걷다", {"영상": ..., "화각": ..., "카메라 무빙": ..., "구도": ...}], ...]
    """
    storyboard_scenes = []

    # 데이터를 하나의 문자열로 병합한 후, 씬 단위로 분리
    full_text = "\n".join(data)
    scenes = full_text.split("- scene")

    for scene in scenes:
        if scene.strip():  # 빈 내용 제외
            lines = scene.strip().split("\n")
            # 첫 줄에서 제목 추출
            title_line = lines[0]
            order_num, scene_title = title_line.split(" ", 1)
            scene_title = scene_title.strip('"').replace('":', "")

            # 나머지 줄에서 세부 정보 추출
            details = {}
            for line in lines[1:]:
                if ": " in line:  # "키: 값" 형태인 경우
                    key, value = line.split(": ", 1)
                    # 키에서 번호와 장식 제거
                    cleaned_key = key.split(". ")[1].strip("*") if ". " in key else key.strip("*")
                    details[cleaned_key] = value.strip()

            # 씬 정보를 리스트에 추가
            storyboard_scenes.append({
                "order_num": int(order_num),
                "scene_title": scene_title,
                "description": details.get("영상", ""),
                "camera_angle": details.get("화각", ""),
                "camera_movement": details.get("카메라 무빙", ""),
                "composition": details.get("구도", "")
            })

    return storyboard_scenes


class StoryboardRequest(BaseModel):
    destination: str  # 여행지
    purpose: str  # 여행 목적
    companions: str  # 동행인 종류
    companion_count: int  # 동행인 수
    season: str  # 계절
    title: str  # 영상 제목
    intro: str  # 인트로
    outro: str  # 아웃트로
    description: str  # 여행지 특성
    image_urls: List[str]  # 참조 이미지 URL 리스트


class StoryboardResponse(BaseModel):
    storyboard_scenes: List[dict]  # 생성된 스토리보드 씬 리스트


# FastAPI 엔드포인트: 스토리보드 생성
@router.post("/storyboards", response_model=StoryboardResponse)
def generate_storyboard(request: StoryboardRequest):
    print(request.dict())  # 수신된 데이터를 출력

    try:
        # GPT 스토리보드 생성 함수 호출
        storyboard_scenes = gpt_generate_storyboard(
            destination=request.destination,
            purpose=request.purpose,
            companions=request.companions,
            companion_count=request.companion_count,
            season=request.season,
            title=request.title,
            intro=request.intro,
            outro=request.outro,
            description=request.description,
            image_urls=request.image_urls,
        )
        print("Generated Storyboard Scenes:", storyboard_scenes)
        chunked_scenes_data = parse_storyboard(storyboard_scenes)
        print("Parsed Storyboard Data:", chunked_scenes_data)

        return StoryboardResponse(storyboard_scenes=chunked_scenes_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
