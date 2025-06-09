import requests
import threading
import logging
from datetime import datetime
import os

# Logging configuration
os.makedirs("logs", exist_ok=True)
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
date_str = datetime.now().strftime("%Y%m%d")
log_handler = logging.FileHandler(f"logs/log_post_request_{date_str}.log")
log_handler.setFormatter(log_formatter)
error_handler = logging.FileHandler("logs/log_error.log")
error_handler.setFormatter(log_formatter)
error_handler.setLevel(logging.ERROR)

logger = logging.getLogger("post_request")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)
logger.addHandler(error_handler)

def get_and_increment_count(file_path='count.txt'):
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('1')
        return 1
    with open(file_path, 'r+', encoding='utf-8') as f:
        try:
            count = int(f.read().strip())
        except Exception:
            count = 1
        f.seek(0)
        f.write(str(count + 1))
        f.truncate()
    return count

def send_post_request(pair_manager, camera_id: int, start_idx: str, end_idx: str, api_url: str):
    """Send POST request to API."""
    count = get_and_increment_count()
    data = {
        "modelProcessCode": "checking_camera_work",
        "fromSystem": "ICS",
        "orderId": f"thaod_1_2_{count}",
        "taskOrderDetail": [
            {
                "taskPath": f"{start_idx},{end_idx}"
            }
        ]
    }
    try:
        response = requests.post(api_url, json=data)
        response_json = response.json()
        if response_json.get("code") == 1000:  # Check for status code 1000
            pair_manager.mark_post_sent(camera_id, start_idx, end_idx, True)
            logger.info(f"POST sent for camera {camera_id + 1}, pair ({start_idx}, {end_idx}): {response.status_code}")
        else:
            logger.warning(f"POST failed for camera {camera_id + 1}, pair ({start_idx}, {end_idx}): Status {response.status_code}")
    except Exception as e:
        logger.error(f"Error sending POST for camera {camera_id + 1}, pair ({start_idx}, {end_idx}): {e}")
        raise

def delay_post_request(pair_manager, camera_id: int, start_idx: str, end_idx: str, api_url: str):
    """Recheck state after 10s and send POST if unchanged."""
    try:
        start_state = pair_manager.state_manager.get_state(camera_id, f"starts_{start_idx}")
        end_state = pair_manager.state_manager.get_state(camera_id, f"ends_{end_idx}")
        logger.debug(f"Delay check for camera {camera_id}, pair ({start_idx}, {end_idx}): start={start_state}, end={end_state}")
        
        if start_state is True and end_state is False:
            threading.Thread(target=send_post_request, args=(pair_manager, camera_id, start_idx, end_idx, api_url)).start()
            logger.info(f"POST request initiated for camera {camera_id}, pair ({start_idx}, {end_idx})")
    except Exception as e:
        logger.error(f"Error in delay_post_request for camera {camera_id}, pair ({start_idx}, {end_idx}): {e}")