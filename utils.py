import cv2
import numpy as np

def detect_lines(roi):
    """Phát hiện đường thẳng trong vùng ROI bằng Hough Transform."""
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=50, maxLineGap=10)
    return lines is not None and len(lines) > 0

def draw_lines_and_text(frame, bbox, has_lines):
    """Vẽ bounding box và ghi chú trạng thái."""
    x1, y1, x2, y2 = bbox
    color = (0, 255, 0) if has_lines else (0, 0, 255)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    label = "Co hang" if has_lines else "Khong hang"
    cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)