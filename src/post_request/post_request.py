import logging
import threading
import requests
from datetime import datetime
import os

# Logging configuration
date_str = datetime.now().strftime("%Y%m%d")
os.makedirs("logs/logs_post_request", exist_ok=True)
os.makedirs("logs/logs_errors/logs_errors_post_request", exist_ok=True)

log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_handler = logging.FileHandler(f"logs/logs_post_request/log_post_request_{date_str}.log")
log_handler.setFormatter(log_formatter)

error_handler = logging.FileHandler(f"logs/logs_errors/logs_errors_post_request/logs_errors_post_request_{date_str}.log")
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

def send_post_request(pair_manager, camera_id: int, start_idx: str, end_idx: str, api_url: str, max_retries=3):
    count = get_and_increment_count()
    data = {
        "modelProcessCode": "checking_camera_work",
        "fromSystem": "ICS",
        "orderId": f"thaod_1_2_{count}",
        "taskOrderDetail": [{"taskPath": f"{start_idx},{end_idx}"}]
    }
    pair_key = (camera_id, start_idx, end_idx)
    retries = 0
    post_lock = threading.Lock()
    while retries < max_retries:
        try:
            response = requests.post(api_url, json=data, timeout=10)
            response_json = response.json()
            if response_json.get("code") == 1000:
                pair_manager.pair_state_manager.mark_post_sent(camera_id, start_idx, end_idx, True, success=True, lock=post_lock)
                logger.info(
                    f"POST sent for camera {camera_id + 1}, pair ({start_idx}, {end_idx}): "
                    f"{response.status_code}, response: {response_json}"
                )
                return True
            else:
                retries += 1
                pair_manager.pair_lock_manager.retry_counts[pair_key] = retries
                logger.warning(
                    f"POST attempt {retries}/{max_retries} failed for camera {camera_id + 1}, "
                    f"pair ({start_idx}, {end_idx}): Status {response.status_code}, response: {response_json}"
                )
                time.sleep(1)
        except Exception as e:
            retries += 1
            pair_manager.pair_lock_manager.retry_counts[pair_key] = retries
            logger.error(
                f"POST attempt {retries}/{max_retries} failed for camera {camera_id + 1}, "
                f"pair ({start_idx}, {end_idx}): {e}"
            )
            time.sleep(1)
    pair_manager.pair_state_manager.mark_post_sent(camera_id, start_idx, end_idx, False, success=False, lock=post_lock)
    logger.error(
        f"POST failed after {max_retries} retries for camera {camera_id + 1}, pair ({start_idx}, {end_idx})"
    )
    return False

def delay_post_request(pair_manager, camera_id: int, start_idx: str, end_idx: str, api_url: str):
    logger.info(f"Starting delay_post_request for camera {camera_id}, pair ({start_idx}, {end_idx})")
    post_lock = threading.Lock()
    try:
        start_state = pair_manager.pair_state_manager.state_manager.get_state(camera_id, f"starts_{start_idx}")
        end_camera_id = pair_manager.end_task_camera_map.get(end_idx, camera_id)
        end_state = pair_manager.pair_state_manager.state_manager.get_state(end_camera_id, f"ends_{end_idx}")
        logger.debug(
            f"Delay check for camera {camera_id}, pair ({start_idx}, {end_idx}): "
            f"start={start_state}, end={end_state}, end_camera={end_camera_id}"
        )
        if start_state is True and end_state is False:
            success = send_post_request(pair_manager, camera_id, start_idx, end_idx, api_url)
            if not success:
                logger.info(
                    f"POST failed for camera {camera_id}, pair ({start_idx}, {end_idx}), "
                    f"releasing for next cycle"
                )
        else:
            logger.info(
                f"States changed before POST for camera {camera_id}, pair ({start_idx}, {end_idx}), "
                f"releasing pair"
            )
            pair_manager.pair_state_manager.mark_post_sent(camera_id, start_idx, end_idx, False, success=False, lock=post_lock)
    except Exception as e:
        logger.error(f"Error in delay_post_request for camera {camera_id}, pair ({start_idx}, {end_idx}): {e}", exc_info=True)
        pair_manager.pair_state_manager.mark_post_sent(camera_id, start_idx, end_idx, False, success=False, lock=post_lock)