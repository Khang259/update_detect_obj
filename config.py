CAMERA_URLS = [
    "rtsp://admin:Soncave1!@192.168.1.27:554/streaming/channels/101",
    "rtsp://admin:Soncave1!@192.168.1.28:554/streaming/channels/101",
    "rtsp://admin:Soncave1!@192.168.1.29:554/streaming/channels/101"
]

BOUNDING_BOXES = [
    {  # Camera 1: 192.168.1.27
        "starts": [
            [303, 319, 362, 399],  # Task path 10000160
            [435, 303, 566, 383],  # Task path 10000161
            [631, 297, 782, 375],  # Task path 10000162
            [851, 289, 996, 375]   # Task path 10000163
        ],
        "ends": [
            [1069, 286, 1171, 358]  # Task path 10000164
        ]
    },
    {  # Camera 2: 192.168.1.28
        "starts": [
            [759, 423, 879, 485],  # Task path 10000146
            [801, 571, 911, 697]   # Task path 10000234
        ],
        "ends": [
            [573, 259, 651, 307]   # Task path 10000147
        ]
    },
    {  # Camera 3: 192.168.1.29
        "starts": [
            [444, 384, 518, 485]   # Task path 10000172
        ],
        "ends": [
            [862, 385, 948, 494],  # Task path 10000170
            [643, 387, 740, 495],  # Task path 10000171
            [871, 167, 947, 287],  # Task path 10000140
            [655, 170, 739, 280]   # Task path 10000141
        ]
    }
]

BBOX_TO_TASKPATH = {
    "303_319_362_399": "10000160",
    "435_303_566_383": "10000161",
    "631_297_782_375": "10000162",
    "851_289_996_375": "10000163",
    "1069_286_1171_358": "10000164",
    "862_385_948_494": "10000170",
    "643_387_740_495": "10000171",
    "444_384_518_485": "10000172",
    "871_167_947_287": "10000140",
    "655_170_739_280": "10000141",
    "759_423_879_485": "10000146",
    "573_259_651_307": "10000147",
    "801_571_911_697": "10000234"
}

START_TASK_PATHS = ["10000160", "10000161", "10000162", "10000163", "10000172", "10000146", "10000234"]
END_TASK_PATHS = ["10000164", "10000170", "10000171", "10000140", "10000141", "10000147"]

AVAILABLE_PAIRS = [
    {  # Camera 1: 192.168.1.27
        "starts": ["10000160", "10000161", "10000162", "10000163"],
        "ends": ["10000170", "10000171", "10000140", "10000141"]  # Camera 3 ends
    },
    {  # Camera 2: 192.168.1.28
        "starts": ["10000146", "10000234"],
        "ends": ["10000164"]  # Camera 1 end
    },
    {  # Camera 3: 192.168.1.29
        "starts": ["10000172"],
        "ends": ["10000147"]  # Camera 2 end
    }
]

API_URL = "http://192.168.1.99:8000/ics/taskOrder/addTask"

FRAME_SIZE = {"width": 1280, "height": 720}

def validate_config():
    """Validate configuration data."""
    if len(CAMERA_URLS) != len(BOUNDING_BOXES):
        raise ValueError("Mismatch between CAMERA_URLS and BOUNDING_BOXES")
    if len(CAMERA_URLS) != len(AVAILABLE_PAIRS):
        raise ValueError("Mismatch between CAMERA_URLS and AVAILABLE_PAIRS")
    
    # Validate bounding boxes
    for camera_id, bboxes in enumerate(BOUNDING_BOXES):
        for task_type in ["starts", "ends"]:
            for x1, y1, x2, y2 in bboxes[task_type]:
                if not (0 <= x1 < x2 <= FRAME_SIZE["width"] and 0 <= y1 < y2 <= FRAME_SIZE["height"]):
                    raise ValueError(f"Invalid bounding box [{x1},{y1},{x2},{y2}] for camera {camera_id}")
                bbox_key = f"{x1}_{y1}_{x2}_{y2}"
                if bbox_key not in BBOX_TO_TASKPATH:
                    raise ValueError(f"Bounding box {bbox_key} not mapped in BBOX_TO_TASKPATH")
    
    # Validate AVAILABLE_PAIRS
    for camera_id, pairs in enumerate(AVAILABLE_PAIRS):
        for task_type in ["starts", "ends"]:
            for task_path in pairs[task_type]:
                if task_path not in BBOX_TO_TASKPATH.values():
                    raise ValueError(f"Task path {task_path} in AVAILABLE_PAIRS[{camera_id}][{task_type}] not found in BBOX_TO_TASKPATH")
                if task_type == "starts" and task_path not in START_TASK_PATHS:
                    raise ValueError(f"Start task path {task_path} in AVAILABLE_PAIRS not in START_TASK_PATHS")
                if task_type == "ends" and task_path not in END_TASK_PATHS:
                    raise ValueError(f"End task path {task_path} in AVAILABLE_PAIRS not in END_TASK_PATHS")
    
    # Validate task paths
    for task_path in START_TASK_PATHS + END_TASK_PATHS:
        if task_path not in BBOX_TO_TASKPATH.values():
            raise ValueError(f"Task path {task_path} not found in BBOX_TO_TASKPATH")

validate_config()