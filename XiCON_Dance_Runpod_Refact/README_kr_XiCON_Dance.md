# XiCON Dance SCAIL - WanAnimate RunPod Serverless

이 프로젝트는 RunPod의 서버리스 엔드포인트를 통해 **WanAnimate SCAIL** 모델을 사용하여 댄스 애니메이션 비디오를 생성하는 Python 클라이언트를 제공합니다. XiCON Dance SCAIL 워크플로우는 고품질 댄스 모션과 자연스러운 동작을 위한 최적화된 설정을 제공합니다.

[![Runpod](https://api.runpod.io/badge/wlsdml1114/Wan_Animate_Runpod_hub)](https://console.runpod.io/hub/wlsdml1114/Wan_Animate_Runpod_hub)

**XiCON Dance SCAIL**은 WanAnimate 2.1 14B SCAIL 모델을 기반으로 하며, 포즈 추정(NLF), 얼굴 인식(VitPose), 그리고 SCAIL 참조 및 포즈 임베딩을 결합하여 고품질 댄스 애니메이션을 생성합니다.

## 🎨 Engui Studio 통합

[![EnguiStudio](https://raw.githubusercontent.com/wlsdml1114/Engui_Studio/main/assets/banner.png)](https://github.com/wlsdml1114/Engui_Studio)

이 WanAnimate 클라이언트는 포괄적인 AI 모델 관리 플랫폼인 **Engui Studio**를 위해 주로 설계되었습니다. API를 통해 사용할 수 있지만, Engui Studio는 향상된 기능과 더 넓은 모델 지원을 제공합니다.

## ✨ XiCON Dance SCAIL의 주요 기능

*   **WanAnimate 2.1 14B SCAIL**: FP8 양자화된 고성능 모델 사용
*   **NLF 포즈 추정**: 자연스러운 라이트필드(NLF) 기반 포즈 감지 및 추정
*   **VitPose 통합**: 전신 포즈 감지를 위한 VitPose 모델 활용
*   **SCAIL 이중 임베딩**: 참조 이미지와 포즈 이미지를 위한 SCAIL 임베딩 지원
*   **고품질 댄스 애니메이션**: 부드럽고 자연스러운 댄스 모션 생성
*   **텍스트 프롬프트 제어**: UMT5-XXL 텍스트 인코더를 통한 정밀한 프롬프트 제어
*   **배치 처리**: 단일 작업에서 여러 이미지 처리
*   **오류 처리**: 포괄적인 오류 처리 및 로깅

## 🚀 RunPod Serverless 템플릿

이 템플릿에는 **XiCON Dance SCAIL**을 RunPod Serverless Worker로 실행하는 데 필요한 모든 구성 요소가 포함되어 있습니다.

*   **Dockerfile**: WanAnimate SCAIL 모델 실행에 필요한 모든 종속성 설치
*   **handler.py**: RunPod Serverless용 요청을 처리하는 핸들러 함수
*   **entrypoint.sh**: 워커 시작 시 초기화 작업 수행
*   **XiCON_Dance_SCAIL.json**: 댄스 애니메이션을 위한 최적화된 워크플로우 구성

## 🔧 XiCON Dance SCAIL 워크플로우 구성

이 워크플로우는 다음과 같은 고급 기능을 제공합니다:

### 모델 및 인코더
- **WanVideo Model**: Wan21-14B-SCAIL-preview_fp8_e4m3fn_scaled_KJ.safetensors
- **VAE**: Wan2.1_VAE.pth (bf16 정밀도)
- **CLIP Vision**: clip_vision_h.safetensors
- **Text Encoder**: umt5-xxl-enc-bf16.safetensors

### 포즈 감지
- **NLF Model**: nlf_l_multi_0.3.2.torchscript (자연스러운 포즈 추정)
- **VitPose Model**: vitpose_h_wholebody_model.onnx (전신 포즈 감지)
- **YOLO Detector**: yolov10m.onnx (객체 및 사람 감지)

### 처리 파이프라인
1. **이미지 전처리**: 참조 이미지를 지정된 해상도로 리샘플링
2. **비디오 로딩**: 참조 비디오 로딩 및 프레임 추출
3. **포즈 추정**: NLF 모델을 사용한 비디오 프레임 포즈 추정
4. **참조 포즈 감지**: VitPose를 사용한 참조 이미지 포즈 감지
5. **포즈 렌더링**: 감지된 포즈를 이미지로 렌더링
6. **SCAIL 임베딩**:
   - 참조 이미지 SCAIL 임베딩 (강도: 1.0, 적용 범위: 0-100%)
   - 포즈 이미지 SCAIL 임베딩 (강도: 1.0, 적용 범위: 0-50%)
7. **텍스트 인코딩**: 프롬프트 및 네거티브 프롬프트 인코딩
8. **샘플링**: DPM++ SDE 스케줄러를 사용한 6단계 샘플링
9. **디코딩**: VAE를 사용한 최종 비디오 디코딩
10. **출력**: 24fps H.264 MP4 비디오 생성

## 📖 Python 클라이언트 사용법

### 기본 사용법

```python
from wananimate_s3_client import WanAnimateS3Client

# 클라이언트 초기화
client = WanAnimateS3Client(
    runpod_endpoint_id="your-endpoint-id",
    runpod_api_key="your-runpod-api-key",
    s3_endpoint_url="https://s3api-eu-ro-1.runpod.io/",
    s3_access_key_id="your-s3-access-key",
    s3_secret_access_key="your-s3-secret-key",
    s3_bucket_name="your-bucket-name",
    s3_region="eu-ro-1"
)

# 댄스 애니메이션 생성
result = client.create_animation_from_files(
    image_path="./dancer_reference.jpg",
    video_path="./dance_motion.mp4",
    prompt="the human starts to dance",
    negative_prompt="색조 과도, 과곡, 정적, 세부 흐림, 자막, 스타일, 작품, 그림, 화면, 정지, 전체 회색, 최악 품질, 낮은 품질, JPEG 압축 잔여, 추악한, 손상됨, 추가 손가락, 잘못 그린 손, 잘못 그린 얼굴, 기형, 변형된 사지, 손가락 융합, 정지 화면, 복잡한 배경, 세 다리, 많은 배경 사람, 뒤로 걷기",
    seed=641625144137451,
    width=416,
    height=672,
    fps=24,
    cfg=1.0,
    steps=6
)

# 성공 시 결과 저장
if result.get('status') == 'COMPLETED':
    client.save_video_result(result, "./output_dance_animation.mp4")
else:
    print(f"오류: {result.get('error')}")
```

### 배치 처리

```python
# 여러 댄서 이미지 처리
batch_result = client.batch_process_animations(
    image_folder_path="./dancer_images",
    video_folder_path="./dance_motions",
    output_folder_path="./output_dance_animations",
    prompt="the human starts to dance",
    negative_prompt="색조 과도, 과곡, 정적, 세부 흐림, 자막",
    seed=641625144137451,
    width=416,
    height=672,
    fps=24,
    cfg=1.0,
    steps=6
)

print(f"배치 처리 완료: {batch_result['successful']}/{batch_result['total_files']} 성공")
```

## 🔧 API 참조

### 입력

`input` 객체는 다음 필드를 포함해야 합니다.

#### 이미지 입력 (하나만 사용)
| 매개변수 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `image_path` | `string` | 아니오 | - | 참조 이미지의 로컬 경로 |
| `image_url` | `string` | 아니오 | - | 참조 이미지의 URL |
| `image_base64` | `string` | 아니오 | - | 참조 이미지의 Base64 인코딩 문자열 |

#### 비디오 입력 (하나만 사용)
| 매개변수 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `video_path` | `string` | 아니오 | - | 댄스 모션 비디오의 로컬 경로 |
| `video_url` | `string` | 아니오 | - | 댄스 모션 비디오의 URL |
| `video_base64` | `string` | 아니오 | - | 댄스 모션 비디오의 Base64 인코딩 문자열 |

#### 애니메이션 매개변수
| 매개변수 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `prompt` | `string` | **예** | - | 생성할 댄스 애니메이션 설명 (예: "the human starts to dance") |
| `negative_prompt` | `string` | 아니오 | - | 원하지 않는 요소 제거 프롬프트 |
| `seed` | `integer` | **예** | - | 랜덤 시드 (재현성을 위해 사용) |
| `width` | `integer` | **예** | `416` | 출력 비디오 너비 (픽셀) |
| `height` | `integer` | **예** | `672` | 출력 비디오 높이 (픽셀) |
| `fps` | `integer` | **예** | `24` | 출력 비디오 프레임 속도 |
| `cfg` | `float` | **예** | `1.0` | 분류기 없는 가이던스 스케일 |
| `steps` | `integer` | 아니오 | `6` | 노이즈 제거 단계 수 |

### 출력

#### 성공
```json
{
  "video": "data:video/mp4;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
}
```

#### 오류
```json
{
  "error": "비디오를 찾을 수 없습니다."
}
```

## 🎯 XiCON Dance SCAIL 특징

### SCAIL (Scale-Aware Image-to-Video) 임베딩
- **참조 이미지 임베딩**: 댄서의 외형과 스타일을 전체 애니메이션에 적용 (0-100%)
- **포즈 이미지 임베딩**: 초기 포즈 정보를 애니메이션 시작 부분에 적용 (0-50%)

### 포즈 추정 및 렌더링
- **NLF 포즈 예측**: 비디오 프레임에서 자연스러운 포즈 추출
- **VitPose 감지**: 참조 이미지에서 전신 포즈 감지 (얼굴 및 손 포함)
- **렌더링**: 감지된 포즈를 시각화하여 애니메이션 가이드로 사용

### 컨텍스트 윈도우 설정
- **Uniform Standard 스케줄**: 일관된 프레임 샘플링
- **컨텍스트 프레임**: 81프레임
- **스트라이드**: 4
- **오버랩**: 16프레임
- **FreeNoise**: 활성화 (더 부드러운 모션)

### 블록 스왑 최적화
- **메모리 효율성**: 25개 블록 스왑으로 VRAM 사용 최적화
- **비차단 전송**: 빠른 데이터 전송을 위한 설정

## 🛠️ 직접 API 사용법

1.  이 저장소를 기반으로 RunPod에서 Serverless Endpoint를 생성합니다.
2.  빌드가 완료되고 엔드포인트가 활성화되면 HTTP POST 요청을 통해 작업을 제출합니다.

### 요청 예시

```json
{
  "input": {
    "prompt": "the human starts to dance",
    "negative_prompt": "색조 과도, 과곡, 정적, 세부 흐림, 자막, 스타일, 작품, 그림, 화면, 정지, 전체 회색, 최악 품질, 낮은 품질",
    "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
    "video_base64": "data:video/mp4;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    "seed": 641625144137451,
    "width": 416,
    "height": 672,
    "fps": 24,
    "cfg": 1.0,
    "steps": 6
  }
}
```

## 🎨 권장 설정

### 해상도
- **416 x 672**: 세로 방향 댄서 (권장)
- **832 x 480**: 가로 방향 댄서

### 프롬프트 가이드
- **긍정적 프롬프트**: "the human starts to dance", "dancing gracefully", "performing choreography"
- **부정적 프롬프트**: 정적인 이미지, 흐릿함, 왜곡, 여러 다리, 배경 잡음 등 제외

### 성능 최적화
- **시드 고정**: 재현 가능한 결과를 위해 특정 시드 사용
- **CFG 스케일**: 1.0 (안정적인 생성)
- **단계 수**: 6 (품질과 속도의 균형)

## 🙏 원본 프로젝트

이 프로젝트는 다음 원본 저장소를 기반으로 합니다:

*   **WanAnimate:** [https://humanaigc.github.io/wan-animate/](https://humanaigc.github.io/wan-animate/)
*   **ComfyUI:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
*   **ComfyUI-WanVideoWrapper:** [https://github.com/kijai/ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)
*   **ComfyUI-SCAIL-Pose:** NLF 및 VitPose 통합
*   **ComfyUI-WanAnimatePreprocess:** 포즈 추정 및 전처리

## 📄 라이선스

원본 WanAnimate 프로젝트는 해당 라이선스를 따릅니다. 이 템플릿도 해당 라이선스를 준수합니다.
