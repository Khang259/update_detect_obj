
import logging

logger = logging.getLogger("config")

CAMERA_URLS = [
    # "rtsp://admin:Soncave1!@192.168.1.27:554/streaming/channels/101",
    # "rtsp://admin:Soncave1!@192.168.1.28:554/streaming/channels/101",
    # "rtsp://admin:Soncave1!@192.168.1.29:554/streaming/channels/101",
    "rtsp://admin:Soncave1!@192.168.1.30:554/streaming/channels/101",
    "rtsp://admin:Soncave1!@192.168.1.31:554/streaming/channels/101"
    # "rtsp://admin:admin@192.168.0.113:8554/live"
    # "rtsp://admin:admin@166.13.151.65:8554/live"

]

BOUNDING_BOXES = [
    # {  # Camera 1: 192.168.1.27
    #     "starts": [
    #         [827, 524, 943, 641],  # Task path 10000173
    #         [655, 522, 785, 630],  # Task path 10000174
    #         [514, 503, 615, 642],  # Task path 10000175
    #         [368, 487, 445, 610],   # Task path 10000176
    #         [238, 477, 283, 599],  # Task path 10000177
    #         [141, 457, 171, 566],   # Task path 10000178 Start(126, 481), End(153, 634)
    #         [29, 425, 50, 547]   # Task path 10000179 (4, 442), End Point = (50, 610)
    #     ],
    #     "ends": [
    #         [991, 532, 1079, 623]  # Task path 10000164
    #     ]
    # },
    # {  # Camera 2: 192.168.1.28
    #     "starts": [
    #         [724, 441, 899, 524],  # Task path 10000146 Start(925, 391), End(958, 486)
    #     #    [801, 571, 911, 697]   # Task path 10000234
    #     ],
    #     "ends": [
    #         [570, 253, 668, 322]   # Task path 10000147
    #     ]
    # },
    # {  # Camera 3: 192.168.1.29
    #     "starts": [
    #         [444, 384, 518, 485]   # Task path 10000172
    #     ],
    #     "ends": [
    #         [862, 385, 948, 494],  # Task path 10000170
    #         [643, 387, 740, 495],  # Task path 10000171
    #         [871, 167, 947, 287],  # Task path 10000140
    #         [655, 170, 739, 280]   # Task path 10000141
    #     ]
    # },
    {  # Camera 4: 192.168.1.30
        "starts": [
            [888, 29, 996, 101]  # Task path 10000565
        ],
        "ends": [
            [165, 52, 313, 114],  # Task path 10000557 [Camera 1] Bounding Box: Start(177, 51), End(338, 102)
            [340, 26, 499, 91],  # Task path 10000558
            [522, 21, 672, 89],  # Task path 10000559 Bounding Box: Start(522, 21), End(672, 89)
            [693, 21, 816, 92],   # Task path 10000560 
        ],
    },
    {  # Camera 5: 192.168.1.31
        "starts": [
            [220, 351, 255, 471],  # Task path 10000452
            [363, 386, 414, 485],  # Task path 10000455  Start(363, 386), End(414, 485)
            [461, 383, 535, 493],   # Task path 10000458  Bounding Box: Start(461, 383), End(535, 493)
            [567, 384, 638, 492],  # Task path 10000461
            [678, 386, 748, 500], # 464
            [789, 384, 857, 494], # 544
            [898, 410, 946, 497],   # 547 Start(898, 410), End(946, 497)
            [991, 405, 1030, 488]   # 550
        ],
        "ends": [
            [369, 278, 421, 311]  # Task path 10000556
        ]
    },
    # { #camera test Iphone
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
    "509_256_623_364": "10000126",

    #.30
    "165_52_313_114": "10000557", #[Camera 1] Bounding Box: Start(177, 51), End(338, 102)
    "340_26_499_91": "10000558",
    "522_21_672_89": "10000559", #
    "693_21_816_92": "10000560", #Bounding Box:  Start(693, 21), End(816, 92)
    "888_29_996_101": "10000565",
    #.31
    "369_278_421_311": "10000556",
    "220_351_255_471": "10000452",
    "363_386_414_485": "10000455",
    "461_383_535_493": "10000458",
    "567_384_638_492": "10000461",
    "678_386_748_500": "10000464",
    "789_384_857_494": "10000544",
    "898_410_946_497": "10000547",
    "991_405_1030_488": "10000550"
}

START_TASK_PATHS = ["10000172","10000173", "10000174", "10000175", "10000176", "10000177", "10000178", "10000179", 
                    "10000146", "10000234", 
                    "10000123", "10000124",
                    "10000452", "10000455", "10000458", "10000461", "10000464", "10000544", "10000547", "10000550", "10000565"]
END_TASK_PATHS = ["10000164", 
                  "10000170", "10000171", "10000140", "10000141", 
                  "10000147", 
                  "10000125", "10000126", 
                  "10000557", "10000558", "10000559", "10000560", "10000556"]

AVAILABLE_PAIRS = [
    # {
    #     "starts": ["10000173", "10000174", "10000175", "10000176", "10000177", "10000178", "10000179"],
    #     "ends": ["10000170", "10000171", "10000140", "10000141"]  
    # },
    # {
    #     "starts": ["10000146", "10000234"],
    #     "ends": ["10000164"]  
    # },
    # {
    #     "starts": ["10000172"],
    #     "ends": ["10000147"]  
    # },
    # {
    #     "starts": ["10000556"],
    #     "ends": ["10000565"] 
    # },
    # {
    #     "starts": ["10000452", "10000455", "10000458", "10000461", "10000464", "10000544", "10000547", "10000550"],
    #     "ends": ["10000557", "10000558", "10000559", "10000560"]  
    # },
    # {
    #     "starts": ["10000565"],
    #     "ends": ["10000147"]  
    # },
    #     {
    #     "starts": ["10000146"],
    #     "ends": ["10000556"]  
    # },
    {
        "starts": ["10000452"],
        "ends": ["10000557"]  
    },
    {
        "starts": ["10000455"],
        "ends": ["10000558"]  
    },
    {
        "starts": ["10000458"],
        "ends": ["10000559"]  
    },
    {
        "starts": ["10000461"],
        "ends": ["10000560"]  
    }
    # {
    #     "starts": ["10000123", "10000124"],
    #     "ends": ["10000125", "10000126"]  # Camera 2 end
    # }
]

API_URL = "http://192.168.1.169:7000/ics/taskOrder/addTask"
#API_URL = "http://192.168.0.108:7000/ics/taskOrder/addTask"

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