# WanAnimate SCAIL 배포 가이드

이 문서는 WanAnimate SCAIL 14B 모델을 Docker 이미지로 빌드하고 RunPod Serverless에 배포하는 완전한 절차를 설명합니다.

## 목차

1. [개요](#개요)
2. [시스템 요구사항](#시스템-요구사항)
3. [Docker 이미지 빌드](#docker-이미지-빌드)
4. [Docker Hub 푸시](#docker-hub-푸시)
5. [RunPod 배포](#runpod-배포)
6. [API 테스트](#api-테스트)
7. [모델 파일 정보](#모델-파일-정보)
8. [트러블슈팅](#트러블슈팅)
9. [성능 최적화](#성능-최적화)
10. [변경 사항 요약](#변경-사항-요약)

---

## 개요

이 프로젝트는 WanAnimate 2.1 14B SCAIL 모델을 RunPod Serverless에서 실행하기 위한 완전한 배포 패키지입니다.

### 주요 특징

- **SCAIL 워크플로우 통합**: 춤 애니메이션 최적화 워크플로우 (XiCON Dance SCAIL)
- **자동 모델 다운로드**: 빌드 시 모든 필요한 모델 자동 다운로드 (~27GB)
- **다중 워크플로우 지원**: 기존 워크플로우와의 하위 호환성 유지
- **향상된 대기 시간**: ComfyUI 초기화 시간 고려 (180초)
- **포즈 감지**: NLF 및 VitPose를 통한 정확한 포즈 추정

### 수정된 컴포넌트

| 파일 | 변경 사항 |
|------|---------|
| `Dockerfile` | SCAIL 모델 4개 추가 다운로드 |
| `handler.py` | `workflow_type` 파라미터로 SCAIL 분기 처리 |
| `entrypoint.sh` | ComfyUI 대기 시간 120초 → 180초로 증가 |
| **추가**: XiCON_Dance_SCAIL_api.json | SCAIL 전용 워크플로우 |
| **추가**: asset/default_video.mp4 | 기본 동영상 파일 |

---

## 시스템 요구사항

### 로컬 빌드 환경

- **Docker**: 최신 버전 (20.10 이상)
- **디스크 공간**: 최소 40GB (모델 다운로드 ~27GB + 빌드 캐시)
- **RAM**: 최소 8GB (권장: 16GB 이상)
- **인터넷**: 안정적인 고속 연결 (모델 다운로드 ~1시간 소요)

### RunPod 인스턴스 요구사항

- **GPU**: A100 40GB 이상 (SCAIL 14B 모델)
  - 또는 H100 (권장)
  - 또는 RTX 6000 Ada (최소)
- **VRAM**: 최소 24GB (권장: 40GB)
- **CPU**: 8 코어 이상
- **RAM**: 최소 64GB
- **스토리지**: 50GB 이상 (컨테이너 디스크)

### 인스턴스 비교

| 인스턴스 | VRAM | 성능 | 가격 | 권장 |
|---------|------|------|------|------|
| A100 40GB | 40GB | 1배 | $0.25/초 | 최적 |
| A100 80GB | 80GB | 1.5배 | $0.45/초 | 최고 |
| H100 | 80GB | 2배 | $0.55/초 | 최고 |
| RTX 6000 Ada | 48GB | 0.8배 | $0.15/초 | 최소 |

---

## Docker 이미지 빌드

### 1단계: 저장소 클론

```bash
git clone https://github.com/your-username/Wan_Animate_Runpod_hub.git
cd Wan_Animate_Runpod_hub
```

### 2단계: Dockerfile 확인

빌드 전에 Dockerfile의 베이스 이미지를 확인하세요:

```bash
head -5 Dockerfile
```

현재 Dockerfile은 다음을 사용합니다:
```dockerfile
FROM wlsdml1114/multitalk-base:1.7 as runtime
```

### 3단계: 로컬 빌드

**기본 빌드 (권장):**
```bash
docker build -t wananimate-scail:latest .
```

**빌드 진행 상황 보기:**
```bash
docker build -t wananimate-scail:latest --progress=plain .
```

**특정 빌드 단계만 캐시 무효화:**
```bash
docker build --no-cache -t wananimate-scail:latest .
```

### 빌드 진행 과정

빌드는 다음 단계를 거칩니다 (총 소요 시간: 1-2시간):

1. **베이스 이미지 가져오기**: ~5분
2. **Python 패키지 설치**: ~10분
   - runpod, websocket-client, huggingface_hub
3. **ComfyUI 클론 및 설정**: ~20분
4. **커스텀 노드 설치**: ~30분
   - ComfyUI-Manager
   - ComfyUI-WanVideoWrapper
   - ComfyUI-KJNodes
   - ComfyUI-VideoHelperSuite
   - ComfyUI-WanAnimatePreprocess
   - ComfyUI-segment-anything-2
   - 기타 최적화 노드
5. **모델 다운로드**: ~50분 (인터넷 속도에 따라 변함)
   - 기본 모델: 6개 (~7GB)
   - SCAIL 모델: 4개 (~12GB)
   - 감지 모델: 3개 (~1GB)
   - LoRA 모델: 4개 (~3GB)

### 빌드 완료 확인

```bash
# 이미지 확인
docker images | grep wananimate-scail

# 이미지 크기 (보통 25-35GB)
docker images wananimate-scail --format "{{.Size}}"
```

### 빌드 문제 해결

**빌드 실패: 모델 다운로드 오류**
```bash
# 재시도: 인터넷 연결 확인 후 다시 빌드
docker build --no-cache -t wananimate-scail:latest .
```

**디스크 공간 부족**
```bash
# Docker 캐시 정리
docker system prune -a --volumes

# 사용 가능한 디스크 확인
df -h /var/lib/docker
```

**메모리 부족으로 인한 오류**
```bash
# Docker 메모리 제한 증가 (Docker Desktop 설정)
# Settings > Resources > Memory: 최소 16GB 할당
```

---

## Docker Hub 푸시

### 1단계: Docker Hub 로그인

```bash
docker login
```

메시지가 나타나면 Docker Hub 계정 정보를 입력하세요.

### 2단계: 이미지 태그 지정

```bash
# 기본 태그
docker tag wananimate-scail:latest <username>/wananimate-scail:latest

# 버전별 태그 (권장)
docker tag wananimate-scail:latest <username>/wananimate-scail:v1.0
```

예시 (`<username>` = `john-doe`인 경우):
```bash
docker tag wananimate-scail:latest john-doe/wananimate-scail:latest
docker tag wananimate-scail:latest john-doe/wananimate-scail:v1.0
```

### 3단계: Docker Hub에 푸시

```bash
# 최신 버전 푸시
docker push <username>/wananimate-scail:latest

# 버전별 태그 푸시
docker push <username>/wananimate-scail:v1.0
```

### 푸시 진행 상황 모니터링

```bash
# 실시간 진행 상황 보기
docker push <username>/wananimate-scail:latest --verbose
```

### 푸시 시간 예상

- 이미지 크기: 25-35GB
- 업로드 속도: 인터넷 연결에 따라 변함
- 예상 시간: 30분 ~ 2시간

### 푸시 완료 확인

Docker Hub 웹사이트에서 확인:
1. [Docker Hub](https://hub.docker.com)에 로그인
2. 저장소 탭에서 `wananimate-scail` 확인
3. 태그 섹션에서 `latest` 및 버전 태그 확인

---

## RunPod 배포

### 방법 1: RunPod Dashboard (권장)

#### 1단계: 템플릿 생성

1. [RunPod 대시보드](https://console.runpod.io) 접속
2. **My Templates** → **Create Template** 클릭
3. 다음 정보 입력:

| 항목 | 값 |
|------|-----|
| **Template Name** | WanAnimate SCAIL |
| **Container Image** | `<username>/wananimate-scail:latest` |
| **Container Registry** | Docker Hub |
| **Container Disk** | 50 GB 이상 |
| **Min vCPUs** | 8 |
| **Min Memory (GB)** | 64 |
| **GPU** | Select GPU (A100 40GB 이상) |

#### 2단계: 환경 변수 설정 (선택사항)

| 환경 변수 | 값 | 설명 |
|----------|-----|------|
| SERVER_ADDRESS | 0.0.0.0 | ComfyUI 서버 주소 |
| HF_TOKEN | `your-token` | HuggingFace 토큰 (선택) |

#### 3단계: Endpoint 생성

1. 템플릿 저장
2. **Endpoints** → **Create Endpoint** 클릭
3. 다음 설정:

| 설정 | 값 |
|------|-----|
| **Endpoint Name** | wananimate-scail-endpoint |
| **Select Template** | WanAnimate SCAIL |
| **GPU Count** | 1 |
| **Workers** | 1 (초기) |
| **Allow Requests from Community** | OFF (프라이빗) |

#### 4단계: 워커 시작

1. Endpoint 페이지에서 **Deploy** 클릭
2. 워커 상태 모니터링 (Ready까지 약 3-5분 소요)
3. **Ready** 상태 확인

### 방법 2: RunPod CLI

#### 1단계: RunPod CLI 설치

```bash
pip install runpod
```

#### 2단계: RunPod API 키 설정

```bash
export RUNPOD_API_KEY="your-api-key"
```

[RunPod 설정](https://www.runpod.io/console/settings/api-keys)에서 API 키 발급

#### 3단계: 템플릿 생성

```bash
runpod template create \
  --name "WanAnimate SCAIL" \
  --image "<username>/wananimate-scail:latest" \
  --container-disk 50 \
  --gpu-count 1 \
  --volume-size 50
```

#### 4단계: Endpoint 생성

```bash
runpod endpoint create \
  --name "wananimate-scail-endpoint" \
  --template-id "<template-id>" \
  --gpu-count 1 \
  --workers 1
```

#### 5단계: 워커 배포

```bash
runpod deploy \
  --endpoint-id "<endpoint-id>" \
  --worker-count 1
```

### 방법 3: RunPod 프로비저닝 (On-Demand)

Serverless 워커 대신 On-Demand 인스턴스 사용:

1. RunPod 대시보드 → **Pods** → **Create Pod**
2. **Container Image**: `<username>/wananimate-scail:latest`
3. **GPU 선택**: A100 40GB
4. **Volume**: 50GB 이상
5. **Create** 클릭

---

## API 테스트

### Endpoint ID 확인

RunPod 대시보드에서:
1. **Endpoints** → 생성한 endpoint 선택
2. **Endpoint ID** 복사 (예: `abc123def456`)

### Python 클라이언트 사용 (권장)

#### 기본 요청 (SCAIL 워크플로우)

```python
import requests
import json
import base64

# 설정
ENDPOINT_ID = "your-endpoint-id"
API_KEY = "your-runpod-api-key"
URL = f"https://api.runpod.io/v1/{ENDPOINT_ID}/run"

# SCAIL 워크플로우 요청
payload = {
    "input": {
        "workflow_type": "scail_dance",
        "image_url": "https://example.com/dancer.jpg",
        "video_url": "https://example.com/dance.mp4",
        "prompt": "the human starts to dance",
        "negative_prompt": "static, low quality, distorted",
        "seed": 641625144137451,
        "width": 416,
        "height": 672,
        "fps": 24,
        "cfg": 1.0,
        "steps": 6
    }
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# 요청 전송
response = requests.post(URL, json=payload, headers=headers)
result = response.json()

# 작업 ID 추출
job_id = result.get("id")
print(f"Job submitted: {job_id}")

# 결과 조회 (폴링)
import time
status_url = f"https://api.runpod.io/v1/{ENDPOINT_ID}/status/{job_id}"

while True:
    status_response = requests.get(status_url, headers=headers)
    status = status_response.json()

    if status.get("status") == "COMPLETED":
        print("Generation completed!")
        output = status.get("output")
        print(f"Video (Base64): {output.get('video')[:100]}...")
        break
    elif status.get("status") == "FAILED":
        print(f"Generation failed: {status.get('error')}")
        break
    else:
        print(f"Status: {status.get('status')}")
        time.sleep(5)
```

#### Base64 이미지 입력

```python
# 이미지 파일을 Base64로 변환
with open("image.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

payload = {
    "input": {
        "workflow_type": "scail_dance",
        "image_base64": image_base64,
        "video_url": "https://example.com/dance.mp4",
        "prompt": "the human starts to dance",
        "seed": 641625144137451,
        "width": 416,
        "height": 672,
        "fps": 24,
        "cfg": 1.0,
        "steps": 6
    }
}
```

#### 기존 워크플로우 (하위 호환성)

```python
# 기존 워크플로우 (workflow_type 미지정)
payload = {
    "input": {
        "image_url": "https://example.com/image.jpg",
        "video_url": "https://example.com/video.mp4",
        "prompt": "a person dancing",
        "seed": 12345,
        "width": 832,
        "height": 480,
        "fps": 24,
        "cfg": 1.0,
        "steps": 4
    }
}
```

### cURL로 테스트

#### SCAIL 요청

```bash
curl -X POST https://api.runpod.io/v1/YOUR_ENDPOINT_ID/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "input": {
      "workflow_type": "scail_dance",
      "image_url": "https://example.com/dancer.jpg",
      "video_url": "https://example.com/dance.mp4",
      "prompt": "the human starts to dance",
      "negative_prompt": "static, low quality",
      "seed": 641625144137451,
      "width": 416,
      "height": 672,
      "fps": 24,
      "cfg": 1.0,
      "steps": 6
    }
  }'
```

#### 상태 확인

```bash
curl -X GET https://api.runpod.io/v1/YOUR_ENDPOINT_ID/status/JOB_ID \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### API 파라미터 설명

#### SCAIL 워크플로우 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `workflow_type` | string | 아니오 | `"default"` | SCAIL 사용: `"scail_dance"` |
| `image_url` | string | 예(1) | - | 이미지 URL |
| `image_path` | string | 예(1) | - | 이미지 파일 경로 |
| `image_base64` | string | 예(1) | - | Base64 인코딩 이미지 |
| `video_url` | string | 예(1) | - | 동영상 URL |
| `video_path` | string | 예(1) | - | 동영상 파일 경로 |
| `video_base64` | string | 예(1) | - | Base64 인코딩 동영상 |
| `prompt` | string | 예 | - | 긍정 프롬프트 |
| `negative_prompt` | string | 아니오 | - | 부정 프롬프트 |
| `seed` | integer | 예 | - | 난수 시드 (0-2147483647) |
| `width` | integer | 예 | - | 출력 너비 (픽셀) |
| `height` | integer | 예 | - | 출력 높이 (픽셀) |
| `fps` | integer | 예 | - | 초당 프레임 수 |
| `cfg` | float | 예 | - | Classifier-Free Guidance 스케일 |
| `steps` | integer | 아니오 | 6 | 디노이징 스텝 수 |

#### 입력 소스 선택 규칙

- **이미지**: `image_url`, `image_path`, `image_base64` 중 하나 필수
- **동영상**: `video_url`, `video_path`, `video_base64` 중 하나 필수
- 여러 개 지정 시: URL → Path → Base64 순서로 우선순위 적용

#### 권장 설정

**SCAIL 워크플로우:**
```json
{
  "width": 416,
  "height": 672,
  "fps": 24,
  "cfg": 1.0,
  "steps": 6
}
```

**기존 워크플로우:**
```json
{
  "width": 832,
  "height": 480,
  "fps": 24,
  "cfg": 1.0,
  "steps": 4
}
```

### 응답 형식

#### 성공 응답

```json
{
  "id": "job-uuid-12345",
  "status": "COMPLETED",
  "output": {
    "video": "data:video/mp4;base64,AAAAHGZ0eXBpc29tAAA..."
  }
}
```

#### 처리 중 응답

```json
{
  "id": "job-uuid-12345",
  "status": "IN_PROGRESS"
}
```

#### 오류 응답

```json
{
  "id": "job-uuid-12345",
  "status": "FAILED",
  "error": "Image input is required..."
}
```

---

## 모델 파일 정보

### 다운로드되는 모델 (총 ~27GB)

#### SCAIL 워크플로우 전용 모델

| 파일명 | 크기 | 용도 | 다운로드 시간 |
|--------|------|------|----------|
| `Wan21-14B-SCAIL-preview_fp8_e4m3fn_scaled_KJ.safetensors` | ~10GB | SCAIL 디퓨전 모델 | 10-15분 |
| `Wan2.1_VAE.pth` | ~1GB | VAE (SCAIL) | 1-2분 |
| `lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors` | ~500MB | LightX2V LoRA | <1분 |
| `nlf_l_multi_0.3.2.torchscript` | ~300MB | NLF 포즈 모델 | <1분 |

#### 기존 워크플로우 모델

| 파일명 | 크기 | 용도 |
|--------|------|------|
| `Wan2_1_VAE_bf16.safetensors` | ~2GB | VAE (기존) |
| `Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors` | ~5GB | WanAnimate 디퓨전 모델 |
| `clip_vision_h.safetensors` | ~1.5GB | CLIP Vision 모델 |
| `umt5-xxl-enc-bf16.safetensors` | ~2GB | 텍스트 인코더 |

#### LoRA 모델

| 파일명 | 크기 | 용도 |
|--------|------|------|
| `lightx2v_elite_it2v_animate_face.safetensors` | ~300MB | 얼굴 애니메이션 |
| `WAN22_MoCap_fullbodyCOPY_ED.safetensors` | ~200MB | 전신 모션 캡처 |
| `FullDynamic_Ultimate_Fusion_Elite.safetensors` | ~300MB | 다이나믹 모션 |
| `Wan2.2-Fun-A14B-InP-Fusion-Elite.safetensors` | ~250MB | 스타일 적용 |

#### 감지 모델

| 파일명 | 크기 | 용도 |
|--------|------|------|
| `yolov10m.onnx` | ~170MB | YOLO 객체 감지 |
| `vitpose_h_wholebody_model.onnx` | ~170MB | VitPose 포즈 감지 |
| `vitpose_h_wholebody_data.bin` | ~30MB | VitPose 데이터 |

### 모델 다운로드 위치

컨테이너 내 모델 경로:
- `/ComfyUI/models/diffusion_models/` - 디퓨전 모델
- `/ComfyUI/models/vae/` - VAE 모델
- `/ComfyUI/models/loras/` - LoRA 모델
- `/ComfyUI/models/clip_vision/` - CLIP Vision 모델
- `/ComfyUI/models/text_encoders/` - 텍스트 인코더
- `/ComfyUI/models/detection/` - 감지 모델

### 모델 출처

| 모델 | HuggingFace 저장소 |
|------|------------------|
| SCAIL | `Kijai/WanVideo_comfy_fp8_scaled` |
| WanAnimate | `Kijai/WanVideo_comfy_fp8_scaled` |
| LoRA | `Kijai/WanVideo_comfy`, `eddy1111111/lightx2v_it2v_adaptive_fusionv_1` |
| 감지 모델 | `Kijai/vitpose_comfy`, `Wan-AI/Wan2.2-Animate-14B` |

---

## 트러블슈팅

### 빌드 단계

#### 문제: "Temporary failure in name resolution" (다운로드 실패)

**원인**: 인터넷 연결 문제 또는 DNS 해석 실패

**해결:**
```bash
# 1. 인터넷 연결 확인
ping 8.8.8.8

# 2. DNS 설정 변경 (선택)
# /etc/resolv.conf에 다음 추가
nameserver 8.8.8.8
nameserver 8.8.4.4

# 3. 재시도
docker build --no-cache -t wananimate-scail:latest .
```

#### 문제: "No space left on device"

**원인**: 디스크 공간 부족

**해결:**
```bash
# 1. Docker 캐시 정리
docker system prune -a --volumes

# 2. 다른 이미지 삭제
docker rmi <image-id>

# 3. 디스크 용량 확인
df -h /var/lib/docker

# 4. 최소 40GB 여유 확인 후 재시도
```

#### 문제: "Cannot allocate memory" 또는 "Out of memory"

**원인**: 빌드 중 메모리 부족

**해결:**
```bash
# Docker Desktop (Mac/Windows)
# Settings > Resources > Memory를 16GB 이상으로 설정

# Linux (증가 필요한 경우)
# 1. 메모리 제한 증가
ulimit -l unlimited

# 2. 스왑 파일 추가
fallocate -l 8G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

#### 문제: "wget: command not found"

**원인**: 베이스 이미지에 wget 미포함

**해결**: Dockerfile 상단에 추가
```dockerfile
RUN apt-get update && apt-get install -y wget curl
```

### 푸시 단계

#### 문제: "denied: requested access to the resource is denied"

**원인**: Docker Hub 로그인 안 됨

**해결:**
```bash
# 1. 로그인 확인
docker login

# 2. 자격증명 확인
cat ~/.docker/config.json

# 3. 재로그인
docker logout
docker login
```

#### 문제: "connection refused" 또는 "network error"

**원인**: 인터넷 연결 문제

**해결:**
```bash
# 1. 연결 확인
curl https://hub.docker.com

# 2. DNS 확인
nslookup hub.docker.com

# 3. 재시도 (자동 재시도)
docker push <username>/wananimate-scail:latest --verbose
```

### RunPod 배포 단계

#### 문제: "Worker failed to start"

**원인**: 이미지가 잘못되었거나 리소스 부족

**해결:**
1. Docker 이미지 태그 확인
2. RunPod 콘솔 로그 확인
3. GPU 가용성 확인
4. 컨테이너 디스크 크기 증가 (최소 50GB)

#### 문제: 워커가 3분 이상 "Starting" 상태 유지

**원인**: ComfyUI 초기화 시간 초과 또는 모델 로딩 지연

**해결:**
1. entrypoint.sh의 대기 시간 확인 (최소 180초)
2. GPU 메모리 부족 확인
3. 워커 재시작
4. 더 큰 GPU 인스턴스로 변경

### API 테스트 단계

#### 문제: "Connection refused" (Endpoint 연결 실패)

**원인**: 엔드포인트가 준비되지 않음

**해결:**
```bash
# 1. 엔드포인트 상태 확인
runpod status <endpoint-id>

# 2. "Ready" 상태까지 대기
sleep 30
curl -X GET https://api.runpod.io/v1/<endpoint-id>/status/<job-id> \
  -H "Authorization: Bearer YOUR_API_KEY"

# 3. 엔드포인트 재시작
runpod restart <endpoint-id>
```

#### 문제: 일반적인 오류 응답

**UnboundLocalError:**
```json
{
  "error": "UnboundLocalError: local variable 'prompt' referenced before assignment"
}
```

**해결**: handler.py의 `workflow_type` 유효성 확인

**공식 문서 참조:**
- [handler.py 코드](handler.py#L195-L209)

#### 문제: "Video generation timeout"

**원인**: 생성 시간이 너무 오래 걸림

**해결:**
```python
# 1. 스텝 수 줄이기
"steps": 4  # 6에서 4로 감소

# 2. 해상도 줄이기
"width": 416,
"height": 672  # 또는 더 작은 값

# 3. 타임아웃 시간 증가 (API 호출 시)
timeout=300  # 기본값에서 증가
```

---

## 성능 최적화

### 생성 속도 향상

#### 1. 해상도 선택

**빠른 생성 (권장 - SCAIL):**
```json
{
  "width": 416,
  "height": 672,
  "fps": 24,
  "steps": 6
}
```

**빠른 생성 (기존 워크플로우):**
```json
{
  "width": 416,
  "height": 672,
  "fps": 16,
  "steps": 4
}
```

**고품질 생성:**
```json
{
  "width": 832,
  "height": 480,
  "fps": 24,
  "steps": 10
}
```

#### 2. CFG 스케일 튜닝

| CFG 값 | 특징 | 권장 |
|--------|------|------|
| 0.5 | 빠르고 창의적 | 스타일 중심 |
| 1.0 | 균형잡힌 (기본) | 일반적 사용 |
| 1.5 | 프롬프트 충실도 높음 | 정밀 제어 |
| 2.0+ | 매우 느림 | 고급 사용 |

#### 3. 시드 활용

```python
# 재현 가능한 결과
"seed": 12345

# 다양한 결과 생성
import random
"seed": random.randint(0, 2147483647)
```

### 메모리 최적화

#### RunPod 인스턴스 비용 절감

**A100 40GB 기준 비용 계산:**
- 시간당: $0.25 × 3600 = $900
- 생성 시간: 1-3분 (평균 2분)
- 작업당 비용: $0.25 × (2/60) ≈ $0.008

**배치 처리로 비용 절감:**
```python
# 10개 작업을 연속 처리
jobs = []
for i in range(10):
    job = client.submit_job({...})
    jobs.append(job.id)

# 총 20분 소요
# 비용: $0.25 × (20/60) ≈ $0.083 (작업당 $0.008)
```

#### 컨테이너 디스크 최적화

현재 이미지 크기: 25-35GB

**증가 추이:**
- 베이스 이미지: 5GB
- ComfyUI + 노드: 3GB
- 모델: 27GB
- 총합: ~35GB

---

## 변경 사항 요약

### 수정된 파일

#### Dockerfile
```dockerfile
# SCAIL 모델 추가
RUN wget -q https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/SCAIL/... \
    -O /ComfyUI/models/diffusion_models/Wan21-14B-SCAIL-preview_fp8_e4m3fn_scaled_KJ.safetensors

# 워크플로우 및 asset 파일 복사
COPY "XiCON_Dance_Runpod_Refact/XiCON_Dance_SCAIL(API).json" /XiCON_Dance_SCAIL_api.json
COPY asset/default_video.mp4 /ComfyUI/input/default_video.mp4
```

**변경 이유**: SCAIL 모델 통합으로 춤 애니메이션 최적화

#### handler.py
```python
# workflow_type 파라미터 추가
workflow_type = job_input.get("workflow_type", "default")

# SCAIL 워크플로우 분기
if workflow_type == "scail_dance":
    prompt = load_workflow('/XiCON_Dance_SCAIL_api.json')
    # SCAIL 노드 매핑...
```

**변경 이유**: 다중 워크플로우 지원 및 사용자 선택 가능

#### entrypoint.sh
```bash
# ComfyUI 대기 시간 증가 (120초 → 180초)
max_wait=180
```

**변경 이유**: SCAIL 모델 로딩 시간 고려

### 추가된 파일

#### XiCON_Dance_Runpod_Refact/XiCON_Dance_SCAIL(API).json
- SCAIL 14B 모델을 위한 최적화 워크플로우
- NLF 포즈 감지 포함
- 춤 애니메이션 전문

#### asset/default_video.mp4
- 워크플로우 노드 130에서 기본값으로 사용
- 빌드 시 `/ComfyUI/input/default_video.mp4`로 복사

### Git 히스토리

```
최신 커밋: SCAIL 워크플로우 통합
- 4개 SCAIL 모델 추가 (~12GB)
- handler.py workflow_type 분기 추가
- entrypoint.sh 대기 시간 180초로 증가
- XiCON_Dance_SCAIL_api.json 추가
- asset/default_video.mp4 추가
```

### 하위 호환성

기존 코드는 완벽하게 호환됩니다:

```python
# 기존 요청 (workflow_type 미지정)
payload = {
    "input": {
        "image_url": "...",
        "video_url": "...",
        "prompt": "...",
        "seed": 12345,
        "width": 832,
        "height": 480,
        "fps": 24,
        "cfg": 1.0,
        "steps": 4
    }
}
# 자동으로 기존 워크플로우 사용
```

---

## 추가 리소스

### 공식 문서

- [RunPod Documentation](https://docs.runpod.io)
- [ComfyUI GitHub](https://github.com/comfyanonymous/ComfyUI)
- [WanAnimate GitHub](https://github.com/humaigc/WanAnimate)

### 유용한 명령어

```bash
# Docker 이미지 정보
docker inspect wananimate-scail:latest

# 컨테이너 로그 확인
docker logs <container-id>

# 실행 중인 컨테이너 확인
docker ps -a

# 이미지 히스토리 확인
docker history wananimate-scail:latest

# 빌드 시간 측정
time docker build -t wananimate-scail:latest .
```

### 커뮤니티 지원

- GitHub Issues: [Wan_Animate_Runpod_hub](https://github.com/your-username/Wan_Animate_Runpod_hub/issues)
- RunPod Community: [Discord](https://discord.gg/runpod)

---

## FAQ

**Q: SCAIL과 기존 WanAnimate의 차이점은?**

A: SCAIL은 14B 모델로 춤 애니메이션에 최적화되었습니다. 기존 모델보다 더 정확한 포즈 감지와 자연스러운 움직임을 제공합니다.

**Q: 생성 시간은?**

A: A100 40GB에서 평균 1-3분 (해상도, 스텝, 프롬프트 복잡도에 따라 변함)

**Q: 비용은?**

A: 작업당 약 $0.008 (A100 40GB 기준, 2분 생성)

**Q: 더 빠른 결과를 원하면?**

A: 해상도 감소, 스텝 수 감소, CFG 값 조정

**Q: 오프라인에서 실행할 수 있나?**

A: 네, 로컬 Docker로 실행 가능합니다. 단, 모델 파일 (~27GB)이 필요합니다.

---

문서 버전: v1.0
마지막 수정: 2024년
작성자: WanAnimate 배포 팀
