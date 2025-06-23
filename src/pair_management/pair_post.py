# import threading
# import logging
# from src.post_request.post_request import delay_post_request

# logger = logging.getLogger("pair_manager")

# class PairPostManager:
#     def __init__(self, pair_manager, api_url):
#         self.pair_manager = pair_manager
#         self.api_url = api_url

#     def trigger_post(self, camera_id, start_idx, end_idx):
#         threading.Thread(
#             target=delay_post_request,
#             args=(self.pair_manager, camera_id, start_idx, end_idx, self.api_url)
#         ).start()