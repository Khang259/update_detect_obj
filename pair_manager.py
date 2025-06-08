import threading
import time
from collections import deque
from post_request import delay_post_request

class PairManager:
    def __init__(self, available_pairs, state_manager, api_url):
        self.available_pairs = available_pairs  # {camera_id: {"starts": [idx], "ends": [idx]}}
        self.state_manager = state_manager
        self.api_url = api_url
        self.running = True
        self.lock = threading.Lock()
        # Initialize round-robin queues and pair states
        self.start_queues = {}  # camera_id -> deque of start indices
        self.end_queues = {}    # camera_id -> deque of end indices
        self.pair_states = {}   # (camera_id, start_idx, end_idx) -> {"post_sent": bool, "timer": float}
        for camera_id in available_pairs:
            self.start_queues[camera_id] = deque(available_pairs[camera_id]["starts"])
            self.end_queues[camera_id] = deque(available_pairs[camera_id]["ends"])
            # Initialize pair states for current pair
            if self.start_queues[camera_id] and self.end_queues[camera_id]:
                start_idx = self.start_queues[camera_id][0]
                end_idx = self.end_queues[camera_id][0]
                self.pair_states[(camera_id, start_idx, end_idx)] = {"post_sent": False, "timer": None}

    def mark_post_sent(self, camera_id, start_idx, end_idx, value):
        with self.lock:
            self.pair_states[(camera_id, start_idx, end_idx)]["post_sent"] = value

    def rotate_queues(self, camera_id):
        with self.lock:
            if camera_id in self.start_queues and camera_id in self.end_queues:
                # Rotate queues to select next pair
                self.start_queues[camera_id].rotate(-1)
                self.end_queues[camera_id].rotate(-1)
                # Remove old pair states
                old_pairs = [(k, v) for k, v in self.pair_states.items() if k[0] == camera_id]
                for (cid, sidx, eidx), _ in old_pairs:
                    del self.pair_states[(cid, sidx, eidx)]
                # Add new pair state
                if self.start_queues[camera_id] and self.end_queues[camera_id]:
                    start_idx = self.start_queues[camera_id][0]
                    end_idx = self.end_queues[camera_id][0]
                    self.pair_states[(camera_id, start_idx, end_idx)] = {"post_sent": False, "timer": None}

    def monitor_pairs(self):
        while self.running:
            for (camera_id, start_idx, end_idx), info in list(self.pair_states.items()):
                start_state = self.state_manager.get_state(camera_id, f"starts_{start_idx}")
                end_state = self.state_manager.get_state(camera_id, f"ends_{end_idx}")

                if start_state is True and end_state is False and not info["post_sent"]:
                    if info["timer"] is None:
                        info["timer"] = time.time()
                    elif time.time() - info["timer"] >= 10:
                        # Send POST and rotate queues
                        threading.Thread(
                            target=delay_post_request,
                            args=(self, camera_id, start_idx, end_idx, self.api_url)
                        ).start()
                        info["timer"] = None
                        self.rotate_queues(camera_id)
                else:
                    info["timer"] = None
                    if info["post_sent"] and (start_state is False or end_state is True):
                        self.mark_post_sent(camera_id, start_idx, end_idx, False)

            time.sleep(0.1)