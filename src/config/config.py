import logging

logger = logging.getLogger("config")

CAMERA_URLS = [
    "rtsp://admin:Soncave1!@192.168.1.27:554/streaming/channels/101",
    "rtsp://admin:Soncave1!@192.168.1.28:554/streaming/channels/101",
    "rtsp://admin:Soncave1!@192.168.1.29:554/streaming/channels/101"
    # "rtsp://admin:admin@192.168.1.42:1935"
]

BOUNDING_BOXES = [
    {  # Camera 1: 192.168.1.27
        "starts": [
            [827, 524, 943, 641],  # Task path 10000173
            [655, 522, 785, 630],  # Task path 10000174
            [514, 503, 615, 642],  # Task path 10000175
            [368, 487, 445, 610],   # Task path 10000176
            [238, 477, 283, 599],  # Task path 10000177
            [141, 457, 171, 566],   # Task path 10000178 Start(126, 481), End(153, 634)
            [29, 425, 50, 547]   # Task path 10000179 (4, 442), End Point = (50, 610)
        ],
        "ends": [
            [991, 532, 1079, 623]  # Task path 10000164
        ]
    },
    {  # Camera 2: 192.168.1.28
        "starts": [
            [724, 441, 899, 524],  # Task path 10000146 Start(925, 391), End(958, 486)
            [801, 571, 911, 697]   # Task path 10000234
        ],
        "ends": [
            [570, 253, 668, 322]   # Task path 10000147
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
    },
    # {
    #     "starts": [
    #         [320, 86, 444, 203],    # Task path 10000123
    #         [322, 255, 452, 365]    # Task path 10000124
    #     ],
    #     "ends": [
    #         [509, 85, 623, 202],    # Task path 10000125
    #         [509, 256, 623, 364]    # Task path 10000126
    #     ]
    # }
]

BBOX_TO_TASKPATH = {
    "827_524_943_641": "10000173",
    "655_522_785_630": "10000174",
    "514_503_615_642": "10000175",
    "368_487_445_610": "10000176",
    "238_477_283_599": "10000177",
    "141_457_171_566": "10000178",
    "29_425_50_547": "10000179",
    "991_532_1079_623": "10000164",
    "862_385_948_494": "10000170",
    "643_387_740_495": "10000171",
    "444_384_518_485": "10000172",
    "871_167_947_287": "10000140",
    "655_170_739_280": "10000141",
    "724_441_899_524": "10000146",
    "570_253_668_322": "10000147",
    "801_571_911_697": "10000234",
    "320_86_444_203": "10000123",
    "322_255_452_365": "10000124",
    "509_85_623_202": "10000125",
    "509_256_623_364": "10000126"
}

START_TASK_PATHS = ["10000172","10000173", "10000174", "10000175", "10000176", "10000177", "10000178", "10000179", "10000146", "10000234", "10000123", "10000124"]
END_TASK_PATHS = ["10000164", "10000170", "10000171", "10000140", "10000141", "10000147", "10000125", "10000126"]

AVAILABLE_PAIRS = [
    {  # Camera 1: 192.168.1.27
        "starts": ["10000173", "10000174", "10000175", "10000176", "10000177", "10000178", "10000179"],
        "ends": ["10000170", "10000171", "10000140", "10000141"]  # Camera 3 ends
    },
    {  # Camera 2: 192.168.1.28
        "starts": ["10000146", "10000234"],
        "ends": ["10000164"]  # Camera 1 end
    },
    {  # Camera 3: 192.168.1.29
        "starts": ["10000172"],
        "ends": ["10000147"]  # Camera 2 end
    },
    # {
    #     "starts": ["10000123", "10000124"],
    #     "ends": ["10000125", "10000126"]  # Camera 2 end
    # }
]

API_URL = "http://192.168.1.169:7000/ics/taskOrder/addTask"

FRAME_SIZE = {"width": 1280, "height": 720}

def validate_config(available_pairs):
    """Validate configuration data."""
    try:
        # Validate AVAILABLE_PAIRS
        for camera_id, pairs in enumerate(available_pairs):
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
        logger.info("Configuration validated successfully")
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise