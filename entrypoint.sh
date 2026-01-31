#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "=========================================="
echo "Container startup - $(date)"
echo "=========================================="

# 환경 확인
echo "Checking Python environment..."
python --version
echo "Python path: $(which python)"

# 필수 라이브러리 확인
echo ""
echo "Checking required libraries..."
python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA available: {torch.cuda.is_available()}')" || echo "ERROR: PyTorch not working"
python -c "import runpod; print(f'RunPod: OK')" || echo "ERROR: runpod not installed"
python -c "import websocket; print(f'websocket-client: OK')" || echo "ERROR: websocket-client not installed"
python -c "import onnxruntime; print(f'onnxruntime: {onnxruntime.__version__}')" || echo "WARNING: onnxruntime not installed"

# Optional libraries
echo ""
echo "Checking optional libraries..."
python -c "import triton; print(f'triton: OK')" 2>/dev/null || echo "WARNING: triton not installed"
python -c "import sageattention; print(f'sageattention: OK')" 2>/dev/null || echo "WARNING: sageattention not installed"
python -c "import taichi; print(f'taichi: OK')" 2>/dev/null || echo "WARNING: taichi not installed"

# ComfyUI 확인
echo ""
echo "Checking ComfyUI..."
if [ -f "/ComfyUI/main.py" ]; then
    echo "ComfyUI main.py found"
else
    echo "ERROR: ComfyUI main.py not found!"
    exit 1
fi

# Start ComfyUI in the background
echo ""
echo "Starting ComfyUI in the background..."
# SageAttention이 없을 경우를 대비해 fallback 시도
if python -c "import sageattention" 2>/dev/null; then
    echo "SageAttention available, using it..."
    python /ComfyUI/main.py --listen --use-sage-attention &
else
    echo "SageAttention not available, starting without it..."
    python /ComfyUI/main.py --listen &
fi

# Wait for ComfyUI to be ready
echo "Waiting for ComfyUI to be ready..."
max_wait=180  # 최대 3분 대기 (SCAIL 14B 모델 로딩 시간 고려)
wait_count=0
while [ $wait_count -lt $max_wait ]; do
    if curl -s http://127.0.0.1:8188/ > /dev/null 2>&1; then
        echo "ComfyUI is ready!"
        break
    fi
    echo "Waiting for ComfyUI... ($wait_count/$max_wait)"
    sleep 2
    wait_count=$((wait_count + 2))
done

if [ $wait_count -ge $max_wait ]; then
    echo "Error: ComfyUI failed to start within $max_wait seconds"
    exit 1
fi

# NLF 모델 캐시 확인 (SCAIL 워크플로우용)
NLF_CACHE_PATH="/root/.cache/torch/hub/checkpoints/nlf_l_multi_0.3.2.torchscript"
if [ ! -f "$NLF_CACHE_PATH" ]; then
    echo "Warning: NLF model cache not found at $NLF_CACHE_PATH"
    echo "First SCAIL workflow execution may take longer due to model download"
fi

# Start the handler in the foreground
# 이 스크립트가 컨테이너의 메인 프로세스가 됩니다.
echo "Starting the handler..."
exec python handler.py