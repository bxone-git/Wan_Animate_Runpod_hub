# Use specific version of nvidia cuda image
FROM wlsdml1114/multitalk-base:1.7 AS runtime

# Install Python packages in single layer
RUN pip install -U "huggingface_hub[hf_transfer]" runpod websocket-client

WORKDIR /

# Clone ComfyUI and install requirements
RUN git clone https://github.com/comfyanonymous/ComfyUI.git && \
    cd /ComfyUI && \
    pip install -r requirements.txt

# Clone all custom nodes in single layer
RUN cd /ComfyUI/custom_nodes && \
    git clone https://github.com/Comfy-Org/ComfyUI-Manager.git && \
    git clone https://github.com/kijai/ComfyUI-WanVideoWrapper && \
    git clone https://github.com/kijai/ComfyUI-KJNodes && \
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite && \
    git clone https://github.com/kijai/ComfyUI-WanAnimatePreprocess && \
    git clone https://github.com/kijai/ComfyUI-segment-anything-2 && \
    git clone https://github.com/eddyhhlure1Eddy/IntelligentVRAMNode && \
    git clone https://github.com/eddyhhlure1Eddy/auto_wan2.2animate_freamtowindow_server && \
    git clone https://github.com/eddyhhlure1Eddy/ComfyUI-AdaptiveWindowSize && \
    cd ComfyUI-AdaptiveWindowSize/ComfyUI-AdaptiveWindowSize && mv * ../

# Install all custom node requirements in single layer
RUN cd /ComfyUI/custom_nodes/ComfyUI-Manager && pip install -r requirements.txt && \
    cd /ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper && pip install -r requirements.txt && \
    cd /ComfyUI/custom_nodes/ComfyUI-KJNodes && pip install -r requirements.txt && \
    cd /ComfyUI/custom_nodes/ComfyUI-VideoHelperSuite && pip install -r requirements.txt && \
    cd /ComfyUI/custom_nodes/ComfyUI-WanAnimatePreprocess && pip install -r requirements.txt

# Install GPU acceleration packages
RUN pip install --upgrade onnxruntime-gpu==1.22 triton sageattention taichi

# Create model directories
RUN mkdir -p /ComfyUI/models/detection /root/.cache/torch/hub/checkpoints

# Download ALL models in parallel (single layer, ~27GB)
# Group 1: Large diffusion models (~15GB) - run in background
# Group 2: VAE, text encoders, clip (~8GB) - run in background
# Group 3: LoRAs, detection models (~4GB) - run in background
RUN wget -q https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/Wan22Animate/Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors \
        -O /ComfyUI/models/diffusion_models/Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors & \
    wget -q https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/SCAIL/Wan21-14B-SCAIL-preview_fp8_e4m3fn_scaled_KJ.safetensors \
        -O /ComfyUI/models/diffusion_models/Wan21-14B-SCAIL-preview_fp8_e4m3fn_scaled_KJ.safetensors & \
    wget -q https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/umt5-xxl-enc-bf16.safetensors \
        -O /ComfyUI/models/text_encoders/umt5-xxl-enc-bf16.safetensors & \
    wget -q https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan2_1_VAE_bf16.safetensors \
        -O /ComfyUI/models/vae/Wan2_1_VAE_bf16.safetensors & \
    wget -q https://huggingface.co/Wan-AI/Wan2.1-T2V-14B/resolve/main/Wan2.1_VAE.pth \
        -O /ComfyUI/models/vae/Wan2.1_VAE.pth & \
    wget -q https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors \
        -O /ComfyUI/models/clip_vision/clip_vision_h.safetensors & \
    wget -q https://huggingface.co/eddy1111111/lightx2v_it2v_adaptive_fusionv_1.safetensors/resolve/main/lightx2v_elite_it2v_animate_face.safetensors \
        -O /ComfyUI/models/loras/lightx2v_elite_it2v_animate_face.safetensors & \
    wget -q https://huggingface.co/eddy1111111/lightx2v_it2v_adaptive_fusionv_1.safetensors/resolve/main/WAN22_MoCap_fullbodyCOPY_ED.safetensors \
        -O /ComfyUI/models/loras/WAN22_MoCap_fullbodyCOPY_ED.safetensors & \
    wget -q https://huggingface.co/eddy1111111/lightx2v_it2v_adaptive_fusionv_1.safetensors/resolve/main/FullDynamic_Ultimate_Fusion_Elite.safetensors \
        -O /ComfyUI/models/loras/FullDynamic_Ultimate_Fusion_Elite.safetensors & \
    wget -q https://huggingface.co/eddy1111111/lightx2v_it2v_adaptive_fusionv_1.safetensors/resolve/main/Wan2.2-Fun-A14B-InP-Fusion-Elite.safetensors \
        -O /ComfyUI/models/loras/Wan2.2-Fun-A14B-InP-Fusion-Elite.safetensors & \
    wget -q https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Lightx2v/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors \
        -O /ComfyUI/models/loras/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors & \
    wget -q https://huggingface.co/Wan-AI/Wan2.2-Animate-14B/resolve/main/process_checkpoint/det/yolov10m.onnx \
        -O /ComfyUI/models/detection/yolov10m.onnx & \
    wget -q https://huggingface.co/Kijai/vitpose_comfy/resolve/main/onnx/vitpose_h_wholebody_model.onnx \
        -O /ComfyUI/models/detection/vitpose_h_wholebody_model.onnx & \
    wget -q https://huggingface.co/Kijai/vitpose_comfy/resolve/main/onnx/vitpose_h_wholebody_data.bin \
        -O /ComfyUI/models/detection/vitpose_h_wholebody_data.bin & \
    wget -q https://github.com/isarandi/nlf/releases/download/v0.3.2/nlf_l_multi_0.3.2.torchscript \
        -O /root/.cache/torch/hub/checkpoints/nlf_l_multi_0.3.2.torchscript & \
    wait

COPY . .
# XiCON Dance SCAIL 워크플로우 복사
COPY "XiCON_Dance_Runpod_Refact/XiCON_Dance_SCAIL(API).json" /XiCON_Dance_SCAIL_api.json

# Default video 복사 (워크플로우 노드 130에서 사용)
COPY asset/default_video.mp4 /ComfyUI/input/default_video.mp4

# 테스트 이미지 복사
COPY asset/25ab29c61a9212fcdbb1d0d18836073a.jpg /ComfyUI/input/test_image.jpg
RUN mkdir -p /ComfyUI/user/default/ComfyUI-Manager
COPY config.ini /ComfyUI/user/default/ComfyUI-Manager/config.ini
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]