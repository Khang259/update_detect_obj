import threading

#Manages a thread-safe dictionary (states) to store the state of each task path
class StateManager:
    def __init__(self):
        # camera_id -> task_path_id -> state (True/False)
        self.states = {}
        self.lock = threading.Lock()

    # Provides update_state to set the state
    def update_state(self, camera_id, task_path_id, state):
        with self.lock:
            if camera_id not in self.states:
                self.states[camera_id] = {}
            self.states[camera_id][task_path_id] = state

    # Provides get_state to retrieve the state
    def get_state(self, camera_id, task_path_id):
        with self.lock:
            return self.states.get(camera_id, {}).get(task_path_id, None)