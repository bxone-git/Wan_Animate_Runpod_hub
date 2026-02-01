# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WanAnimate RunPod Serverless - A production deployment for the WanAnimate AI model that converts static images into animated videos using pose estimation and motion reference videos. Runs as a RunPod serverless worker with ComfyUI backend.

## Build & Deploy Commands

```bash
# Build Docker image (must use linux/amd64 for RunPod)
docker build --platform linux/amd64 -t wananimate-runpod:latest .

# Push to Docker Hub
docker push <username>/wananimate-runpod:latest

# Local testing (requires NVIDIA GPU)
docker run --gpus all -it wananimate-runpod:latest /bin/bash
# Inside container:
python /ComfyUI/main.py --listen &
python test_local.py
```

## Architecture

```
Request Flow:
RunPod API → handler.py → WebSocket → ComfyUI (port 8188) → Workflow JSON → Video (Base64)

Container Startup:
entrypoint.sh → Validate deps → Start ComfyUI (background) → Wait 180s max → Start handler.py
```

### Key Files

- `handler.py` - RunPod serverless handler, routes to workflows based on `workflow_type` and `points_store`
- `entrypoint.sh` - Container startup, validates PyTorch/CUDA, starts ComfyUI then handler
- `Dockerfile` - Multi-stage build: base image → ComfyUI + 8 custom nodes → ~27GB models
- `wananimate_s3_client.py` - Python client for API with S3 upload support

### Workflow Selection Logic (handler.py)

```python
if workflow_type == "scail_dance":       → XiCON_Dance_SCAIL_api.json  # SCAIL 14B model
elif points_store is None:               → newWanAnimate_noSAM_api.json  # No control points
else:                                    → newWanAnimate_point_api.json  # With control points
```

### Input Processing

Handler accepts three input formats for both image and video:
- `*_path` - Local/network volume path
- `*_url` - Download via wget
- `*_base64` - Decode and save to temp file

## API Parameters

Required: `prompt`, `seed`, `width`, `height`, `fps`, `cfg`
Optional: `steps` (default 6), `negative_prompt`, `workflow_type`, `points_store`

Typical values: width=416, height=672, fps=24, cfg=1.0, steps=6

### Input Formats

The handler accepts two input format styles:

**Flat Format (original):**
- `image_path` / `image_url` / `image_base64` - Reference image
- `video_path` / `video_url` / `video_base64` - Dance video

**Nested Format (new):**
- `images.reference_image` - Auto-detects URL/path/base64
- `videos.dance_video` - Auto-detects URL/path/base64

Both formats are fully supported. The handler auto-detects the input type for nested format values.

## GPU Requirements

- GPU: RTX 6000 Ada / A100 40GB recommended
- CUDA: 12.8
- Container disk: 50GB
- Cold start: ~180 seconds (SCAIL 14B model loading)

## ComfyUI Custom Nodes

Critical nodes (breaking if missing):
- ComfyUI-WanVideoWrapper - WanVideo model interface
- ComfyUI-WanAnimatePreprocess - Pose detection preprocessing
- ComfyUI-segment-anything-2 - SAM2 segmentation

## Models (~27GB total)

- `Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors` - Main animation model
- `Wan21-14B-SCAIL-preview_fp8_e4m3fn_scaled_KJ.safetensors` - SCAIL dance model
- `umt5-xxl-enc-bf16.safetensors` - Text encoder
- `Wan2.1_VAE.pth` / `Wan2_1_VAE_bf16.safetensors` - VAE models
- Various LoRA adapters in `/ComfyUI/models/loras/`

## Debugging

Check container startup:
```bash
# Inside container
python -c "import torch; print(torch.cuda.is_available())"  # Should be True
curl http://127.0.0.1:8188/  # ComfyUI health check
```

Optional acceleration libraries (warnings OK if missing):
- `sageattention` - Attention acceleration
- `triton` - Kernel optimization
- `taichi` - NLF pose rendering
