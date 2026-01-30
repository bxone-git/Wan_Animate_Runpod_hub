#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Start ComfyUI in the background
echo "Starting ComfyUI in the background..."
python /ComfyUI/main.py --listen --use-sage-attention &

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