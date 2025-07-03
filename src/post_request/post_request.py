import logging
import threading
import requests
from datetime import datetime
import os
from queue import Queue
import queue
import time

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

def get_and_increment_count(file_path='src/post_request/count.txt'):
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

class PostRequestManager:
    def __init__(self, api_url: str, sent_pairs_queue: Queue):
        self.api_url = api_url
        self.sent_pairs_queue = sent_pairs_queue
        self.post_queue = Queue()
        self.thread = threading.Thread(target=self.process_posts)
        self.running = True
        self.last_post_time = 0  # Track the time of the last POST
        logger.debug("PostRequestManager initialized")

    def start(self):
        self.thread.start()
        logger.info("PostRequestManager started")

    def stop(self):
        self.running = False
        self.thread.join()
        logger.info("PostRequestManager stopped")

    def trigger_post(self, data: str):
        self.post_queue.put(data)
        logger.debug(f"Queued POST request for pair: {data}")

    def process_posts(self):
        while self.running:
            try:
                data = self.post_queue.get(timeout=1)
                start_idx, end_idx = data.split(',')
                current_time = time.time()
                elapsed_since_last_post = current_time - self.last_post_time

                # Wait until 1 second has passed since the last POST
                if elapsed_since_last_post < 1:
                    time.sleep(1 - elapsed_since_last_post)

                start_time = time.time()
                success = self.send_post_request(data)
                self.last_post_time = time.time()  # Update last post time
                elapsed = self.last_post_time - start_time
                logger.debug(f"Processed POST for pair ({start_idx}, {end_idx}) in {elapsed:.2f}s")
                if success:
                    self.sent_pairs_queue.put((start_idx, end_idx, True))
                    logger.info(f"Marked pair ({start_idx}, {end_idx}) as sent")
                else:
                    self.sent_pairs_queue.put((start_idx, end_idx, False))
                    logger.error(f"Failed to send pair ({start_idx}, {end_idx})")
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing POST request: {e}")

    def send_post_request(self, pair: str, max_retries=3):
        count = get_and_increment_count()
        data = {
            "modelProcessCode": "checking_camera_work",
            "fromSystem": "ICS",
            "orderId": f"thaod_1_3_{count}",
            "taskOrderDetail": [
                {"taskPath": f"{pair}"}
            ]
        }
        retries = 0
        while retries < max_retries:
            try:
                response = requests.post(self.api_url, json=data, timeout=10)
                response_json = response.json()
                if response_json.get("code") == 1000:
                    logger.info(f"POST sent for pair {pair}: {response.status_code}")
                    return True
                else:
                    retries += 1
                    logger.warning(
                        f"POST attempt {retries}/{max_retries} failed for pair {pair}: "
                        f"Status {response.status_code}"
                    )
                    time.sleep(1)
            except Exception as e:
                retries += 1
                logger.error(
                    f"POST attempt {retries}/{max_retries} failed for pair {pair}: {e}"
                )
                time.sleep(1)
        logger.error(f"POST failed after {max_retries} retries for pair {pair}")
        return False