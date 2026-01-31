# Session Follow-up Document

**날짜**: 2026-01-31
**목적**: Windows GPU 환경에서 로컬 테스트 진행

---

## 현재 상황

### 문제
RunPod Serverless에서 컨테이너가 시작 직후 크래시됨:
```
start container for registry.runpod.net/...:301e6f2c9: begin
start container for registry.runpod.net/...:301e6f2c9: begin
...
remove container
```

### 원인 추정
필수 라이브러리 누락 가능성:
- `sageattention` - WanVideo attention acceleration
- `triton` - sageattention 의존성
- `taichi` - NLF pose rendering backend

---

## 수정된 파일들

### 1. Dockerfile (커밋: 301e6f2)
추가된 의존성:
```dockerfile
# SageAttention, Triton (WanVideo attention acceleration)
RUN pip install triton sageattention

# Taichi (NLF Pose rendering backend)
RUN pip install taichi
```

### 2. entrypoint.sh (커밋: 7536eaa)
- SageAttention fallback 로직 추가
- 상세 시작 로깅 추가 (Python, PyTorch, CUDA, 라이브러리 확인)

---

## 로컬 테스트 방법

### 1. Docker 이미지 빌드
```bash
docker build --platform linux/amd64 -t wananimate-runpod:latest .
```

### 2. 컨테이너 실행 (대화형 모드)
```bash
docker run --gpus all -it wananimate-runpod:latest /bin/bash
```

### 3. 내부에서 수동 테스트
```bash
# 환경 확인
python --version
python -c "import torch; print(torch.cuda.is_available())"

# 라이브러리 확인
python -c "import sageattention; print('OK')"
python -c "import triton; print('OK')"
python -c "import taichi; print('OK')"

# ComfyUI 시작
python /ComfyUI/main.py --listen

# 또는 전체 entrypoint
/entrypoint.sh
```

### 4. 전체 테스트 (test_local.py 사용)
컨테이너 내부에서:
```bash
# ComfyUI 먼저 시작
python /ComfyUI/main.py --listen &

# ComfyUI 준비될 때까지 대기 (약 1-3분)
# 그 후 테스트 실행
python /test_local.py
```

---

## 테스트 입력 데이터 (SCAIL Dance)

```json
{
  "input": {
    "workflow_type": "scail_dance",
    "image_path": "/ComfyUI/input/test_image.jpg",
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
```

---

## 관련 파일

| 파일 | 설명 |
|------|------|
| `Dockerfile` | 컨테이너 빌드 설정 |
| `entrypoint.sh` | 컨테이너 시작 스크립트 |
| `handler.py` | RunPod serverless 핸들러 |
| `test_local.py` | 로컬 테스트 스크립트 |
| `XiCON_Dance_Runpod_Refact/XiCON_Dance_SCAIL(API).json` | SCAIL 워크플로우 |

---

## Git 상태

- 브랜치: `main`
- 최신 커밋: `7536eaa` (debug: add detailed startup logging)
- Remote: `https://github.com/bxone-git/Wan_Animate_Runpod_hub.git`

---

## 다음 단계

1. Windows PC에서 `git clone` 또는 `git pull`
2. Docker 빌드 (`--platform linux/amd64` 필요할 수 있음)
3. GPU 환경에서 컨테이너 실행
4. 에러 메시지 확인 및 수정
5. 성공 시 RunPod 재배포

---

## 베이스 이미지 정보

```
FROM wlsdml1114/multitalk-base:1.7
```

이 베이스 이미지에 어떤 라이브러리가 포함되어 있는지 확인 필요.
