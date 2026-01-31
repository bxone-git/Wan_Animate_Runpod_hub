#!/usr/bin/env python3
"""
로컬 Docker 테스트 스크립트
사용법: python test_local.py
"""

import json
import base64
import urllib.request
import time

# 컨테이너 내부 이미지 경로 사용 (Dockerfile에서 복사됨)
TEST_IMAGE_PATH = "/ComfyUI/input/test_image.jpg"

def test_scail_workflow():
    """SCAIL Dance 워크플로우 테스트 (10프레임 빠른 테스트)"""

    # 테스트 입력 데이터
    test_input = {
        "input": {
            "workflow_type": "scail_dance",
            "image_path": TEST_IMAGE_PATH,
            # video_path는 생략 - 기본값 default_video.mp4 사용
            "prompt": "the human starts to dance",
            "negative_prompt": "static, blurry, low quality",
            "seed": 12345,
            "width": 416,
            "height": 672,
            "fps": 24,
            "cfg": 1.0,
            "steps": 6
        }
    }

    print("=" * 60)
    print("XiCON Dance SCAIL 워크플로우 테스트 (10프레임)")
    print("=" * 60)
    print(f"\n입력 파라미터:")
    print(json.dumps(test_input, indent=2, ensure_ascii=False))

    # handler.py의 handler 함수 직접 호출
    try:
        from handler import handler

        print("\n처리 중...")
        start_time = time.time()

        result = handler(test_input)

        elapsed_time = time.time() - start_time
        print(f"\n처리 완료 (소요 시간: {elapsed_time:.2f}초)")

        if "error" in result:
            print(f"\n❌ 오류 발생: {result['error']}")
            return False

        if "video" in result:
            # Base64 비디오 데이터를 파일로 저장
            video_data = base64.b64decode(result["video"])
            output_path = "/tmp/test_output.mp4"
            with open(output_path, "wb") as f:
                f.write(video_data)

            print(f"\n✅ 성공!")
            print(f"출력 비디오 크기: {len(video_data) / 1024:.2f} KB")
            print(f"저장 위치: {output_path}")
            return True

        print(f"\n⚠️ 예상치 못한 응답: {result}")
        return False

    except Exception as e:
        print(f"\n❌ 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_comfyui_connection():
    """ComfyUI 연결 테스트"""
    print("\nComfyUI 연결 테스트...")
    try:
        response = urllib.request.urlopen("http://127.0.0.1:8188/", timeout=5)
        print("✅ ComfyUI 연결 성공")
        return True
    except Exception as e:
        print(f"❌ ComfyUI 연결 실패: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("XiCON Dance SCAIL 로컬 테스트")
    print("=" * 60)

    # 1. ComfyUI 연결 확인
    if not test_comfyui_connection():
        print("\n⚠️ ComfyUI가 실행 중이 아닙니다.")
        print("먼저 'python /ComfyUI/main.py --listen --use-sage-attention' 실행 필요")
        exit(1)

    # 2. SCAIL 워크플로우 테스트
    success = test_scail_workflow()

    print("\n" + "=" * 60)
    if success:
        print("✅ 테스트 통과")
    else:
        print("❌ 테스트 실패")
    print("=" * 60)
