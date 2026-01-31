import runpod
from runpod.serverless.utils import rp_upload
import os
import websocket
import base64
import json
import uuid
import logging
import urllib.request
import urllib.parse
import binascii # Base64 에러 처리를 위해 import
import subprocess
import time

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


server_address = os.getenv('SERVER_ADDRESS', '127.0.0.1')
client_id = str(uuid.uuid4())
def save_data_if_base64(data_input, temp_dir, output_filename):
    """
    입력 데이터가 Base64 문자열인지 확인하고, 맞다면 파일로 저장 후 경로를 반환합니다.
    만약 일반 경로 문자열이라면 그대로 반환합니다.
    """
    # 입력값이 문자열이 아니면 그대로 반환
    if not isinstance(data_input, str):
        return data_input

    try:
        # Base64 문자열은 디코딩을 시도하면 성공합니다.
        decoded_data = base64.b64decode(data_input)
        
        # 디렉토리가 존재하지 않으면 생성
        os.makedirs(temp_dir, exist_ok=True)
        
        # 디코딩에 성공하면, 임시 파일로 저장합니다.
        file_path = os.path.abspath(os.path.join(temp_dir, output_filename))
        with open(file_path, 'wb') as f: # 바이너리 쓰기 모드('wb')로 저장
            f.write(decoded_data)
        
        # 저장된 파일의 경로를 반환합니다.
        print(f"✅ Base64 입력을 '{file_path}' 파일로 저장했습니다.")
        return file_path

    except (binascii.Error, ValueError):
        # 디코딩에 실패하면, 일반 경로로 간주하고 원래 값을 그대로 반환합니다.
        print(f"➡️ '{data_input}'은(는) 파일 경로로 처리합니다.")
        return data_input
    
def queue_prompt(prompt):
    url = f"http://{server_address}:8188/prompt"
    logger.info(f"Queueing prompt to: {url}")
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    url = f"http://{server_address}:8188/view"
    logger.info(f"Getting image from: {url}")
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"{url}?{url_values}") as response:
        return response.read()

def get_history(prompt_id):
    url = f"http://{server_address}:8188/history/{prompt_id}"
    logger.info(f"Getting history from: {url}")
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read())

def get_videos(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_videos = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break
        else:
            continue

    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        videos_output = []
        if 'gifs' in node_output:
            for video in node_output['gifs']:
                # fullpath를 이용하여 직접 파일을 읽고 base64로 인코딩
                with open(video['fullpath'], 'rb') as f:
                    video_data = base64.b64encode(f.read()).decode('utf-8')
                videos_output.append(video_data)
        output_videos[node_id] = videos_output

    return output_videos

def load_workflow(workflow_path):
    with open(workflow_path, 'r') as file:
        return json.load(file)


def process_input(input_data, temp_dir, output_filename, input_type):
    """입력 데이터를 처리하여 파일 경로를 반환하는 함수"""
    if input_type == "path":
        # 경로인 경우 그대로 반환
        logger.info(f"📁 경로 입력 처리: {input_data}")
        return input_data
    elif input_type == "url":
        # URL인 경우 다운로드
        logger.info(f"🌐 URL 입력 처리: {input_data}")
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.abspath(os.path.join(temp_dir, output_filename))
        return download_file_from_url(input_data, file_path)
    elif input_type == "base64":
        # Base64인 경우 디코딩하여 저장
        logger.info(f"🔢 Base64 입력 처리")
        return save_base64_to_file(input_data, temp_dir, output_filename)
    else:
        raise Exception(f"지원하지 않는 입력 타입: {input_type}")

        
def download_file_from_url(url, output_path):
    """URL에서 파일을 다운로드하는 함수"""
    try:
        # wget을 사용하여 파일 다운로드
        result = subprocess.run([
            'wget', '-O', output_path, '--no-verbose', url
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ URL에서 파일을 성공적으로 다운로드했습니다: {url} -> {output_path}")
            return output_path
        else:
            logger.error(f"❌ wget 다운로드 실패: {result.stderr}")
            raise Exception(f"URL 다운로드 실패: {result.stderr}")
    except subprocess.TimeoutExpired:
        logger.error("❌ 다운로드 시간 초과")
        raise Exception("다운로드 시간 초과")
    except Exception as e:
        logger.error(f"❌ 다운로드 중 오류 발생: {e}")
        raise Exception(f"다운로드 중 오류 발생: {e}")


def save_base64_to_file(base64_data, temp_dir, output_filename):
    """Base64 데이터를 파일로 저장하는 함수"""
    try:
        # Base64 문자열 디코딩
        decoded_data = base64.b64decode(base64_data)
        
        # 디렉토리가 존재하지 않으면 생성
        os.makedirs(temp_dir, exist_ok=True)
        
        # 파일로 저장
        file_path = os.path.abspath(os.path.join(temp_dir, output_filename))
        with open(file_path, 'wb') as f:
            f.write(decoded_data)
        
        logger.info(f"✅ Base64 입력을 '{file_path}' 파일로 저장했습니다.")
        return file_path
    except (binascii.Error, ValueError) as e:
        logger.error(f"❌ Base64 디코딩 실패: {e}")
        raise Exception(f"Base64 디코딩 실패: {e}")

def handler(job):
    job_input = job.get("input", {})

    logger.info(f"Received job input: {job_input}")
    task_id = f"task_{uuid.uuid4()}"


    image_path = None
    # 이미지 입력 처리 (image_path, image_url, image_base64 중 하나만 사용)
    if "image_path" in job_input:
        image_path = process_input(job_input["image_path"], task_id, "input_image.jpg", "path")
    elif "image_url" in job_input:
        image_path = process_input(job_input["image_url"], task_id, "input_image.jpg", "url")
    elif "image_base64" in job_input:
        image_path = process_input(job_input["image_base64"], task_id, "input_image.jpg", "base64")

    video_path = None
    # 비디오 입력 처리 (video_path, video_url, video_base64 중 하나만 사용)
    if "video_path" in job_input:
        video_path = process_input(job_input["video_path"], task_id, "input_video.mp4", "path")
    elif "video_url" in job_input:
        video_path = process_input(job_input["video_url"], task_id, "input_video.mp4", "url")
    elif "video_base64" in job_input:
        video_path = process_input(job_input["video_base64"], task_id, "input_video.mp4", "base64")

    check_coord = job_input.get("points_store", None)
    workflow_type = job_input.get("workflow_type", "default")

    # Validate required inputs
    if image_path is None:
        raise Exception("Image input is required. Provide image_path, image_url, or image_base64")
    if video_path is None:
        raise Exception("Video input is required. Provide video_path, video_url, or video_base64")

    # Initialize prompt variable to avoid UnboundLocalError
    prompt = None

    # SCAIL 워크플로우 선택
    if workflow_type == "scail_dance":
        prompt = load_workflow('/XiCON_Dance_SCAIL_api.json')

        # XiCON Dance SCAIL 노드 매핑
        prompt["106"]["inputs"]["image"] = image_path
        prompt["130"]["inputs"]["video"] = video_path
        prompt["130"]["inputs"]["force_rate"] = job_input["fps"]
        prompt["139"]["inputs"]["frame_rate"] = job_input["fps"]
        prompt["368"]["inputs"]["positive_prompt"] = job_input["prompt"]
        if "negative_prompt" in job_input:
            prompt["368"]["inputs"]["negative_prompt"] = job_input["negative_prompt"]
        prompt["348"]["inputs"]["seed"] = job_input["seed"]
        prompt["238"]["inputs"]["value"] = job_input["cfg"]
        prompt["349"]["inputs"]["steps"] = job_input.get("steps", 6)
        prompt["203"]["inputs"]["value"] = job_input["width"]
        prompt["204"]["inputs"]["value"] = job_input["height"]

    elif check_coord == None:
        if job_input.get("mode", "replace") == "animate":
            prompt = load_workflow('/newWanAnimate_noSAM_animate_api.json')
        else:
            prompt = load_workflow('/newWanAnimate_noSAM_api.json')

        prompt["57"]["inputs"]["image"] = image_path
        prompt["63"]["inputs"]["video"] = video_path
        prompt["63"]["inputs"]["force_rate"] = job_input["fps"]
        prompt["30"]["inputs"]["frame_rate"] = job_input["fps"]
        prompt["65"]["inputs"]["positive_prompt"] = job_input["prompt"]
        if "negative_prompt" in job_input:
            prompt["65"]["inputs"]["negative_prompt"] = job_input["negative_prompt"]
        prompt["27"]["inputs"]["seed"] = job_input["seed"]
        prompt["27"]["inputs"]["cfg"] = job_input["cfg"]
        prompt["27"]["inputs"]["steps"] = job_input.get("steps", 4)
        prompt["150"]["inputs"]["value"] = job_input["width"]
        prompt["151"]["inputs"]["value"] = job_input["height"]
    else:
        if job_input.get("mode", "replace") == "animate":
            prompt = load_workflow('/newWanAnimate_point_animate_api.json')
        else:
            prompt = load_workflow('/newWanAnimate_point_api.json')
        
        prompt["57"]["inputs"]["image"] = image_path
        prompt["63"]["inputs"]["video"] = video_path
        prompt["63"]["inputs"]["force_rate"] = job_input["fps"]
        prompt["30"]["inputs"]["frame_rate"] = job_input["fps"]
        prompt["65"]["inputs"]["positive_prompt"] = job_input["prompt"]
        if "negative_prompt" in job_input:
            prompt["65"]["inputs"]["negative_prompt"] = job_input["negative_prompt"]
        prompt["27"]["inputs"]["seed"] = job_input["seed"]
        prompt["27"]["inputs"]["cfg"] = job_input["cfg"]
        prompt["27"]["inputs"]["steps"] = job_input.get("steps", 4)
        prompt["150"]["inputs"]["value"] = job_input["width"]
        prompt["151"]["inputs"]["value"] = job_input["height"]

        prompt["107"]["inputs"]["points_store"] = job_input["points_store"]
        prompt["107"]["inputs"]["coordinates"] = job_input["coordinates"]
        prompt["107"]["inputs"]["neg_coordinates"] = job_input["neg_coordinates"]
        # prompt["107"]["inputs"]["width"] = job_input["width"]
        # prompt["107"]["inputs"]["height"] = job_input["height"]
    
    # Validate prompt was assigned
    if prompt is None:
        raise RuntimeError("Failed to load workflow. Prompt was not initialized.")
    

    ws_url = f"ws://{server_address}:8188/ws?clientId={client_id}"
    logger.info(f"Connecting to WebSocket: {ws_url}")
    
    # 먼저 HTTP 연결이 가능한지 확인
    http_url = f"http://{server_address}:8188/"
    logger.info(f"Checking HTTP connection to: {http_url}")
    
    # HTTP 연결 확인 (최대 1분)
    max_http_attempts = 180
    for http_attempt in range(max_http_attempts):
        try:
            import urllib.request
            response = urllib.request.urlopen(http_url, timeout=5)
            logger.info(f"HTTP 연결 성공 (시도 {http_attempt+1})")
            break
        except Exception as e:
            logger.warning(f"HTTP 연결 실패 (시도 {http_attempt+1}/{max_http_attempts}): {e}")
            if http_attempt == max_http_attempts - 1:
                raise Exception("ComfyUI 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
            time.sleep(1)
    
    ws = websocket.WebSocket()
    # 웹소켓 연결 시도 (최대 3분)
    max_attempts = int(180/5)  # 3분 (1초에 한 번씩 시도)
    for attempt in range(max_attempts):
        import time
        try:
            ws.connect(ws_url)
            logger.info(f"웹소켓 연결 성공 (시도 {attempt+1})")
            break
        except Exception as e:
            logger.warning(f"웹소켓 연결 실패 (시도 {attempt+1}/{max_attempts}): {e}")
            if attempt == max_attempts - 1:
                raise Exception("웹소켓 연결 시간 초과 (3분)")
            time.sleep(5)
    videos = get_videos(ws, prompt)
    ws.close()

    # 이미지가 없는 경우 처리
    for node_id in videos:
        if videos[node_id]:
            return {"video": videos[node_id][0]}
    
    return {"error": "비디오를 찾을 수 없습니다."}

runpod.serverless.start({"handler": handler})