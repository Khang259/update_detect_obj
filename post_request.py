import requests
import threading

def send_post_request(camera_id, start_idx, end_idx, api_url):
    """Gửi POST request đến API."""
    data = {
        "camera_id": camera_id,
        "start_idx": start_idx,
        "end_idx": end_idx,
        "status": "start_has_goods_end_empty"
    }
    try:
        response = requests.post(api_url, json=data)
        print(f"POST sent for camera {camera_id}, pair ({start_idx}, {end_idx}): {response.status_code}")
    except Exception as e:
        print(f"Error sending POST: {e}")

# Delay function to check the state after 10 seconds and send POST request if conditions are met
# This function is called in a separate thread to avoid blocking the main thread

def delay_post_request(pair_manager, camera_id, start_idx, end_idx, api_url):
    """Kiểm tra trạng thái sau 10s và gửi POST nếu không đổi."""
    start_state = pair_manager.state_manager.get_state(camera_id, f"starts_{start_idx}")
    end_state = pair_manager.state_manager.get_state(camera_id, f"ends_{end_idx}")
    
    if start_state is True and end_state is False:
        threading.Thread(target=send_post_request, args=(camera_id, start_idx, end_idx, api_url)).start()
        pair_manager.mark_post_sent(camera_id, start_idx, end_idx, True)