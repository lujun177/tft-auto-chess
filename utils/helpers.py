"""
Helper functions for TFT Auto Chess
"""
import cv2
import numpy as np
from pathlib import Path


def crop_region(image, region):
    """
    Crop image to specified region.
    
    Args:
        image: Input image (numpy array)
        region: Tuple of (top, left, bottom, right) as percentage (0-1)
    
    Returns:
        Cropped image
    """
    height, width = image.shape[:2]
    top, left, bottom, right = region
    
    y1 = int(height * top)
    x1 = int(width * left)
    y2 = int(height * bottom)
    x2 = int(width * right)
    
    return image[y1:y2, x1:x2]


def resize_image(image, width=None, height=None, inter=cv2.INTER_AREA):
    """
    Resize image while maintaining aspect ratio.
    
    Args:
        image: Input image
        width: Target width
        height: Target height
        inter: Interpolation method
    
    Returns:
        Resized image
    """
    (h, w) = image.shape[:2]
    
    if width is None and height is None:
        return image
    
    if width is None:
        ratio = height / float(h)
        width = int(w * ratio)
    elif height is None:
        ratio = width / float(w)
        height = int(h * ratio)
    
    resized = cv2.resize(image, (width, height), interpolation=inter)
    return resized


def draw_detections(image, detections, class_names=None):
    """
    Draw bounding boxes on image.
    
    Args:
        image: Input image
        detections: List of detections [(x1, y1, x2, y2, conf, class_id), ...]
        class_names: Optional list of class names
    
    Returns:
        Image with drawn detections
    """
    annotated = image.copy()
    colors = np.random.randint(0, 255, size=(len(detections), 3))
    
    for i, (x1, y1, x2, y2, conf, class_id) in enumerate(detections):
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
        color = tuple(map(int, colors[i]))
        
        # Draw bounding box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        
        # Draw label
        label = f"{class_names[int(class_id)] if class_names else class_id}: {conf:.2f}"
        cv2.putText(annotated, label, (x1, y1 - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    return annotated


def get_center_point(bbox):
    """
    Calculate center point of bounding box.
    
    Args:
        bbox: Bounding box (x1, y1, x2, y2)
    
    Returns:
        Center point (x, y)
    """
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) // 2, (y1 + y2) // 2)


def calculate_iou(box1, box2):
    """
    Calculate Intersection over Union.
    
    Args:
        box1: Bounding box (x1, y1, x2, y2)
        box2: Bounding box (x1, y1, x2, y2)
    
    Returns:
        IoU value (0-1)
    """
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2
    
    # Calculate intersection
    inter_xmin = max(x1_min, x2_min)
    inter_ymin = max(y1_min, y2_min)
    inter_xmax = min(x1_max, x2_max)
    inter_ymax = min(y1_max, y2_max)
    
    if inter_xmax < inter_xmin or inter_ymax < inter_ymin:
        return 0.0
    
    inter_area = (inter_xmax - inter_xmin) * (inter_ymax - inter_ymin)
    
    # Calculate union
    box1_area = (x1_max - x1_min) * (y1_max - y1_min)
    box2_area = (x2_max - x2_min) * (y2_max - y2_min)
    union_area = box1_area + box2_area - inter_area
    
    return inter_area / union_area if union_area > 0 else 0


def ensure_dir(path):
    """Ensure directory exists."""
    Path(path).mkdir(parents=True, exist_ok=True)


def save_image(image, path):
    """Save image to file."""
    ensure_dir(Path(path).parent)
    cv2.imwrite(str(path), image)


def load_image(path):
    """Load image from file."""
    return cv2.imread(str(path))