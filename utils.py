# utils.py
import cv2
import numpy as np
import logging
from datetime import datetime
import os

# Logging configuration
os.makedirs("logs", exist_ok=True)
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
date_str = datetime.now().strftime("%Y%m%d")
log_handler = logging.FileHandler(f"logs/log_utils_{date_str}.log")
log_handler.setFormatter(log_formatter)
error_handler = logging.FileHandler("logs/log_error.log")
error_handler.setFormatter(log_formatter)
error_handler.setLevel(logging.ERROR)

logger = logging.getLogger("utils")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)
logger.addHandler(error_handler)

def detect_lines(roi: np.ndarray) -> bool:
    """Detect lines in ROI using Hough Transform."""
    try:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=50, maxLineGap=10)
        has_lines = lines is not None and len(lines) > 0
        logger.debug(f"Line detection in ROI: {'lines detected' if has_lines else 'no lines'}")
        return has_lines
    except Exception as e:
        logger.error(f"Error detecting lines in ROI: {e}")
        return False

def draw_lines_and_text(frame: np.ndarray, bbox: list, has_lines: bool):
    """Draw bounding box and status label on frame."""
    try:
        x1,y1, x2, y2 = bbox
        color = (0, 255, 0) if has_lines else (0, 0, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = "Co hang" if has_lines else "Khong hang"
        cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        logger.debug(f"Drew bounding box {bbox} with label '{label}'")
    except Exception as e:
        logger.error(f"Error drawing on frame for bbox {bbox}: {e}")