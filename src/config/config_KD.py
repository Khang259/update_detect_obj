# Cấu hình linh hoạt cho 35 RTSP cameras với khả năng tự động phân chia
# Khi thay RTSP thật vào, hệ thống sẽ tự động phân chia và chạy cho 35 cameras
# Khi thêm cameras, hệ thống sẽ tự động phân chia cho phù hợp

# RTSP URLs thật - sử dụng IP từ cột "IP Honda cấp" thay vào phần IP trong RTSP URL
RTSP_URLS = [
    # Camera 1-10: Khu vực A
    # "rtsp://admin:SPtech2024@192.168.50.15:554/Streaming/Channels/101",
    # # "rtsp://admin:SPtech2024@192.168.50.26:554/Streaming/Channels/101",
    # # "rtsp://admin:SPtech2024@192.168.50.6:554/Streaming/Channels/101",
    # # "rtsp://admin:SPtech2024@192.168.50.28:554/Streaming/Channels/101",
    "rtsp://admin:SPtech2024@192.168.50.13:554/Streaming/Channels/101",
    "rtsp://admin:SPtech2024@192.168.50.4:554/Streaming/Channels/101",
    "rtsp://admin:SPtech2024@192.168.50.14:554/Streaming/Channels/101",
    "rtsp://admin:SPtech2024@192.168.50.27:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.12:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.7:554/Streaming/Channels/101",
    
    # #Camera 11-20: Khu vực B
    # "rtsp://admin:SPtech2024@192.168.50.3:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.17:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.24:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.2:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.23:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.19:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.32:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.8:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.33:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.34:554/Streaming/Channels/101",
    
    # # Camera 21-30: Khu vực C
    # "rtsp://admin:SPtech2024@192.168.50.22:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.20:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.30:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.3:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.10:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.1:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.6:554/Streaming/Channels/101",
    "rtsp://admin:SPtech2024@192.168.50.36:554/Streaming/Channels/101",
    "rtsp://admin:SPtech2024@192.168.50.35:554/Streaming/Channels/101",
    "rtsp://admin:SPtech2024@192.168.50.31:554/Streaming/Channels/101",
    
    # # Camera 31-35: Khu vực D
    "rtsp://admin:SPtech2024@192.168.50.19:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.25:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.18:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.32:554/Streaming/Channels/101",
    # "rtsp://admin:SPtech2024@192.168.50.11:554/Streaming/Channels/101"
]

# Cấu hình tự động phân chia cho 35 cameras
CAMERA_CONFIG = {
    "buffer_size": 1,  # Giảm buffer để realtime hơn
    "fps": 15,  # FPS tối ưu cho 35 cameras
    "timeout": 3,  # Timeout khi đọc frame
    "retry_count": 2,  # Số lần retry khi lỗi
    "poll_interval": 0.067,  # 15 FPS
    "max_cameras_per_process": 7,  # 35 cameras / 5 processes = 7 cameras/process
    "max_processes": 5,  # 5 processes cho 35 cameras
    "queue_size": 1000,  # Queue size cho frames
    "mp_queue_size": 50,  # Multiprocessing queue size
    "health_check_interval": 60,  # Kiểm tra sức khỏe camera mỗi 60 giây
    "error_threshold": 3,  # Số lỗi liên tục tối đa trước khi skip camera
    "graceful_shutdown_timeout": 15,  # Timeout khi shutdown
    
    # Cấu hình tự động phân chia
    "auto_scaling": {
        "enabled": True,  # Bật tự động phân chia
        "min_cameras_per_process": 5,  # Tối thiểu 5 cameras/process
        "max_cameras_per_process": 10,  # Tối đa 10 cameras/process
        "target_cpu_percent": 70,  # Target CPU usage
        "target_memory_percent": 80,  # Target memory usage
        "scale_up_threshold": 85,  # Ngưỡng tăng scale
        "scale_down_threshold": 50,  # Ngưỡng giảm scale
        "check_interval": 30  # Kiểm tra mỗi 30 giây
    },
    
    # Cấu hình RTSP
    "rtsp_config": {
        "protocol": "tcp",  # Sử dụng TCP cho ổn định
        "timeout": 5,  # Timeout kết nối
        "reconnect_interval": 10,  # Thời gian reconnect
        "max_reconnect_attempts": 5,  # Số lần reconnect tối đa
        "buffer_size": 1024 * 1024,  # Buffer size cho RTSP
        "enable_multicast": False,  # Tắt multicast để tránh conflict
        "preferred_fps": 15,  # FPS ưu tiên
        "preferred_resolution": "1280x720"  # Resolution ưu tiên
    }
}

# Cấu hình tối ưu cho 35 cameras
SCALING_CONFIG = {
    "enable_load_balancing": True,  # Bật load balancing
    "enable_health_monitoring": True,  # Bật monitoring sức khỏe
    "enable_auto_restart": True,  # Tự động restart process lỗi
    "memory_limit_mb": 2048,  # Giới hạn memory mỗi process (2GB)
    "cpu_limit_percent": 80,  # Giới hạn CPU mỗi process
    "network_timeout": 5,  # Timeout network cho camera
    "batch_processing": True,  # Xử lý batch thay vì từng frame
    "batch_size": 20,  # Batch size cho 35 cameras
    "enable_compression": True,  # Bật compression để tiết kiệm memory
    "enable_frame_skipping": True,  # Bật frame skipping cho cameras ít quan trọng
    "adaptive_batch_sizing": True,  # Batch size tự động điều chỉnh
    "priority_cameras": [0, 1, 2, 3, 4],  # Cameras ưu tiên (không skip frame)
    "skip_interval": 2,  # Skip 1 frame mỗi 2 frames cho cameras không ưu tiên
    
    # Cấu hình mở rộng
    "expansion_config": {
        "max_total_cameras": 300,  # Tối đa 300 cameras
        "auto_add_cameras": True,  # Tự động thêm cameras
        "camera_discovery": {
            "enabled": True,  # Bật discovery cameras
            "scan_network": "192.168.1.0/24",  # Scan network range
            "scan_interval": 300,  # Scan mỗi 5 phút
            "auto_add_new": True  # Tự động thêm cameras mới
        },
        "load_distribution": {
            "algorithm": "round_robin",  # Thuật toán phân phối tải
            "consider_cpu": True,  # Cân nhắc CPU usage
            "consider_memory": True,  # Cân nhắc memory usage
            "consider_network": True  # Cân nhắc network bandwidth
        }
    }
}

# BOUNDING_BOXES cho 35 cameras
BOUNDING_BOXES = {
    "starts": [
        [359, 275, 488, 438],
        [537, 270, 681, 441],
        [741, 260, 881, 438],
        [281, 251, 400, 418],
        [472, 256, 601, 407],
        [679, 255, 796, 406],
        [869, 243, 982, 407],
        [253, 174, 361, 315],
        [446, 152, 565, 299],
        [679, 145, 822, 303],
        [914, 148, 1040, 317],
    ],
    "ends": [
        [304, 241, 497, 336],
        [430, 152, 635, 265],
        [443, 190, 609, 298],
        [395, 330, 600, 422],
        [638, 390, 829, 499],
        [653, 351, 821, 446],
        [653, 294, 813, 402],
        [663, 337, 860, 424],
        [652, 398, 865, 492],
        [653, 473, 842, 576],
    ]
}
#BOUNDING_BOXES = [SINGLE_BOX.copy() for _ in range(len(RTSP_URLS))]

BBOX_TO_TASKPATH = {
#  "283_369_400_498": "10000296",
#  "423_220_627_335": "10000292",
#  "666_222_883_341": "10000291",
#   "911_362_1025_482": "10000295",
#   "406_351_599_475": "10000289",
#   "641_358_849_480": "10000288",
#   "888_504_993_618": "10000294",
#   "428_354_634_475": "10000286",
#   "673_356_875_478": "10000300",
#   "919_501_1025_612": "10000299",
#   "422_300_620_435": "10000297",
#   "667_313_854_444": "10000285",
#   "763_386_846_487": "10000385",
   "304_241_497_336": "10000381",
#   "308_223_496_334": "10000380",
#   "186_384_296_493": "10000384",
   "430_152_635_265": "10000378",
#   "447_150_630_257": "10000377",
#   "324_312_415_418": "10000383",
   "443_190_609_298": "10000375",
#   "419_188_620_312": "10000389",
#   "294_342_412_463": "10000388",
   "395_330_600_422": "10000386",
#   "387_324_629_439": "10000374",
#   "293_526_392_631": "10000350",
   "638_390_829_499": "10000346",
#   "646_394_832_493": "10000345",
#   "865_529_948_637": "10000349",
   "653_351_821_446": "10000343",
#   "632_347_828_457": "10000342",
#   "852_482_938_592": "10000348",
   "653_294_813_402": "10000340",
#   "646_299_826_403": "10000354",
#   "856_436_933_545": "10000353",
   "663_337_860_424": "10000351",
#   "654_324_848_428": "10000339",
#   "273_286_373_419": "10000470",
   "652_398_865_492": "10000465",
   "653_473_842_576": "10000467",
#   "644_485_848_583": "10000466",
#   "885_276_999_409": "10000469",
#   "929_226_1046_346": "10000078",
#   "699_428_880_546": "10000074",
#   "442_434_635_545": "10000073",
#   "295_261_395_380": "10000077",
#   "699_512_875_609": "10000071",
#   "438_503_636_620": "10000070",
#   "291_310_392_425": "10000076",
#   "660_456_831_573": "10000068",
#   "391_432_602_575": "10000082",
#   "273_242_364_366": "10000081",
#   "691_491_897_598": "10000079",
#   "431_486_645_595": "10000067",
#   "881_589_999_683": "10000045",
#   "751_351_862_548": "10000041",
#   "751_121_869_308": "10000040",
#   "921_557_1040_657": "10000044",
#   "784_333_906_536": "10000038",
#   "775_93_901_292": "10000037",
#   "935_597_1040_691": "10000043",
#   "827_358_926_558": "10000035",
#   "845_123_940_318": "10000049",
#   "734_89_852_295": "10000046",
#   "724_319_826_581": "10000034",
#   "841_191_980_378": "10000677",
#   "1062_211_1141_385": "10000679",
#   "930_179_1019_352": "10001109",
#   "699_165_867_339": "10000659",
#   "448_159_645_351": "10000689",
#   "254_188_418_350": "10000687",
#   "923_294_1064_459": "10000685",
#   "676_290_864_462": "10000683",
#   "439_285_643_465": "10000681",
#   "257_284_415_459": "10000679",
#   "99_299_230_449": "10000677",
   "359_275_488_438": "10000607",
   "537_270_681_441": "10000610",
   "741_260_881_438": "10000613",
   "281_251_400_418": "10000616",
   "472_256_601_407": "10000619",
   "679_255_796_406": "10000622",
   "869_243_982_407": "10000625",
   "253_174_361_315": "10000628",
   "446_152_565_299": "10000632",
   "679_145_822_303": "10000634",
   "914_148_1040_317": "10000636",
   "229_276_372_426": "10000638",
   "440_266_595_419": "10000640",
   "670_259_794_424": "10000642",
   "816_256_978_426": "10000644",
#   "249_213_345_379": "10000579",
#   "383_212_490_376": "10000581",
#   "552_214_651_369": "10000583",
#   "709_222_823_385": "10000585",
#   "872_237_947_388": "10000587",
#   "301_210_385_339": "10000589",
#   "453_195_551_336": "10000591",
#   "609_193_708_340": "10000593",
#   "773_185_880_350": "10000595",
#   "923_190_1016_363": "10001107",
#   "278_201_362_350": "10000599",
#   "437_193_542_354": "10000601"
}

START_TASK_PATHS = ["10000607", "10000610", "10000613", "10000616", "10000619", "10000622", "10000625", "10000628", "10000632", "10000634", "10000636", "10000638", "10000640", "10000642", "10000644"]
END_TASK_PATHS = ["10000381", "10000378", "10000375", "10000386", "10000346", "10000343", "10000340", "10000351", "10000465", "10000467"]

# AVAILABLE_PAIRS cho 35 cameras
AVAILABLE_PAIRS = [{
    "starts": ["10000636"],
    "ends": ["10000381"]
},
{
    "starts": ["10000634"],
    "ends": ["10000378"]
},
{
    "starts": ["10000632"],
    "ends": ["10000375"]
},
{
    "starts": ["10000628"],
    "ends": ["10000386"]
}
]
#AVAILABLE_PAIRS = [SINGLE_PAIR.copy() for _ in range(len(RTSP_URLS))]

API_URL = "http://10.250.161.134:7000/ics/taskOrder/addTask"

FRAME_SIZE = {"width": 1280, "height": 720}

def validate_config():
    """Validate configuration data."""
    if len(RTSP_URLS) != len(BOUNDING_BOXES):
        raise ValueError("Mismatch between RTSP_URLS and BOUNDING_BOXES")
    if len(RTSP_URLS) != len(AVAILABLE_PAIRS):
        raise ValueError("Mismatch between RTSP_URLS and AVAILABLE_PAIRS")
    
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
                if task_type == "starts" and task_path not in START_TASK_PATHS:
                    raise ValueError(f"Start task path {task_path} not in START_TASK_PATHS for camera {camera_id}")
                elif task_type == "ends" and task_path not in END_TASK_PATHS:
                    raise ValueError(f"End task path {task_path} not in END_TASK_PATHS for camera {camera_id}")
    
    print(f"Configuration validated successfully for {len(RTSP_URLS)} cameras")

def get_camera_configs():
    """Tạo danh sách camera configs từ RTSP URLs"""
    camera_configs = []
    for i, url in enumerate(RTSP_URLS):
        camera_configs.append({
            'camera_id': i,
            'url': url,
            'bounding_boxes': BOUNDING_BOXES[i],
            'priority': i in SCALING_CONFIG.get("priority_cameras", []),
            'zone': f"Zone_{i // 10 + 1}" if i < 30 else "Zone_4"  # Phân zone theo camera ID
        })
    return camera_configs

def calculate_optimal_process_distribution(num_cameras):
    """Tính toán phân phối process tối ưu cho số cameras"""
    min_cameras_per_process = CAMERA_CONFIG["auto_scaling"]["min_cameras_per_process"]
    max_cameras_per_process = CAMERA_CONFIG["auto_scaling"]["max_cameras_per_process"]
    
    # Tính số process cần thiết
    optimal_cameras_per_process = min(max_cameras_per_process, 
                                     max(min_cameras_per_process, num_cameras // 5))
    
    num_processes = max(1, (num_cameras + optimal_cameras_per_process - 1) // optimal_cameras_per_process)
    
    return {
        "num_processes": num_processes,
        "cameras_per_process": optimal_cameras_per_process,
        "distribution": []
    }

def generate_camera_distribution(camera_configs):
    """Tạo phân phối cameras cho các processes"""
    distribution = calculate_optimal_process_distribution(len(camera_configs))
    
    cameras_per_process = distribution["cameras_per_process"]
    num_processes = distribution["num_processes"]
    
    # Phân phối cameras
    for i in range(num_processes):
        start_idx = i * cameras_per_process
        end_idx = min(start_idx + cameras_per_process, len(camera_configs))
        process_cameras = camera_configs[start_idx:end_idx]
        
        distribution["distribution"].append({
            "process_id": i,
            "cameras": process_cameras,
            "camera_count": len(process_cameras),
            "zone": f"Zone_{i + 1}"
        })
    
    return distribution

# Validate config khi import
if __name__ == "__main__":
    validate_config()
    print(f"Camera distribution for {len(RTSP_URLS)} cameras:")
    configs = get_camera_configs()
    distribution = generate_camera_distribution(configs)
    for proc in distribution["distribution"]:
        print(f"   Process {proc['process_id']}: {proc['camera_count']} cameras in {proc['zone']}")
else:
    validate_config()