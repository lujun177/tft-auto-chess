"""
Card detection module using YOLOv8
"""
import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO

from utils.logger import logger
from config.settings import (
    MODEL_PATH, CONFIDENCE_THRESHOLD, IOU_THRESHOLD,
    USE_GPU, GPU_DEVICE
)


class CardDetector:
    """
    YOLO-based card detector for TFT game.
    Detects champions and items in game screen.
    """
    
    def __init__(self, model_path=None, confidence_threshold=CONFIDENCE_THRESHOLD):
        """
        Initialize card detector.
        
        Args:
            model_path: Path to YOLOv8 model (default: config path)
            confidence_threshold: Minimum confidence for detections
        """
        self.model_path = model_path or MODEL_PATH
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.device = None
        
        self._load_model()
    
    def _load_model(self):
        """Load YOLOv8 model."""
        try:
            # Check if model file exists
            if not Path(self.model_path).exists():
                logger.warning(f"Model not found at {self.model_path}")
                logger.info("Downloading YOLOv8 model...")
                # YOLO will auto-download if not found
            
            # Load model
            device = GPU_DEVICE if USE_GPU else "cpu"
            self.model = YOLO(str(self.model_path))
            self.model.to(device)
            self.device = device
            
            logger.info(f"Model loaded successfully on device: {device}")
        
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def detect(self, image, conf=None):
        """
        Detect cards in image.
        
        Args:
            image: Input image (BGR format, numpy array)
            conf: Optional confidence threshold override
        
        Returns:
            List of detections: [(class_name, confidence, bbox), ...]
            where bbox is (x1, y1, x2, y2)
        """
        if self.model is None:
            logger.error("Model not loaded")
            return []
        
        try:
            confidence = conf or self.confidence_threshold
            
            # Run inference
            results = self.model.predict(
                source=image,
                conf=confidence,
                iou=IOU_THRESHOLD,
                verbose=False
            )
            
            detections = []
            if results and len(results) > 0:
                result = results[0]
                
                if result.boxes is not None and len(result.boxes) > 0:
                    for box in result.boxes:
                        # Get coordinates
                        x1, y1, x2, y2 = map(float, box.xyxy[0])
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        
                        # Get class name
                        class_name = self.model.names.get(
                            class_id, f"class_{class_id}"
                        )
                        
                        detections.append({
                            'name': class_name,
                            'confidence': confidence,
                            'bbox': (int(x1), int(y1), int(x2), int(y2)),
                            'class_id': class_id,
                            'center': (
                                int((x1 + x2) / 2),
                                int((y1 + y2) / 2)
                            )
                        })
            
            logger.debug(f"Detected {len(detections)} cards")
            return detections
        
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return []
    
    def detect_batch(self, images, conf=None):
        """
        Detect cards in multiple images.
        
        Args:
            images: List of images
            conf: Optional confidence threshold override
        
        Returns:
            List of detection lists
        """
        return [self.detect(img, conf) for img in images]
    
    def filter_detections(self, detections, class_filter=None, min_confidence=None):
        """
        Filter detections by class and/or confidence.
        
        Args:
            detections: List of detections from detect()
            class_filter: Filter by class names (list of strings)
            min_confidence: Minimum confidence threshold
        
        Returns:
            Filtered detections list
        """
        filtered = detections.copy()
        
        if min_confidence is not None:
            filtered = [d for d in filtered if d['confidence'] >= min_confidence]
        
        if class_filter is not None:
            filtered = [d for d in filtered if d['name'] in class_filter]
        
        return filtered
    
    def get_model_info(self):
        """Get model information."""
        if self.model is None:
            return None
        
        return {
            'model_path': str(self.model_path),
            'device': self.device,
            'num_classes': self.model.nc,
            'classes': self.model.names
        }
    
    def update_model(self, new_model_path):
        """Update to a new model."""
        self.model_path = new_model_path
        self._load_model()
        logger.info(f"Model updated to: {new_model_path}")


class MultiScaleCardDetector(CardDetector):
    """
    Multi-scale card detector for better detection across different card sizes.
    """
    
    def detect_multi_scale(self, image, scales=(0.5, 1.0, 1.5), conf=None):
        """
        Detect cards at multiple scales.
        
        Args:
            image: Input image
            scales: List of scale factors
            conf: Optional confidence threshold
        
        Returns:
            Merged detections from all scales
        """
        all_detections = []
        height, width = image.shape[:2]
        
        for scale in scales:
            if scale == 1.0:
                scaled_img = image
            else:
                new_width = int(width * scale)
                new_height = int(height * scale)
                scaled_img = cv2.resize(image, (new_width, new_height))
            
            detections = self.detect(scaled_img, conf)
            
            # Scale back bounding boxes
            if scale != 1.0:
                for det in detections:
                    x1, y1, x2, y2 = det['bbox']
                    det['bbox'] = (
                        int(x1 / scale),
                        int(y1 / scale),
                        int(x2 / scale),
                        int(y2 / scale)
                    )
                    det['center'] = (
                        int(det['center'][0] / scale),
                        int(det['center'][1] / scale)
                    )
            
            all_detections.extend(detections)
        
        # Remove duplicates using NMS (Non-Maximum Suppression)
        return self._nms_detections(all_detections)
    
    def _nms_detections(self, detections, iou_threshold=0.5):
        """
        Apply Non-Maximum Suppression to remove duplicate detections.
        
        Args:
            detections: List of detections
            iou_threshold: IoU threshold for NMS
        
        Returns:
            Filtered detections
        """
        if len(detections) == 0:
            return []
        
        # Sort by confidence
        detections = sorted(detections, key=lambda d: d['confidence'], reverse=True)
        
        keep = []
        while detections:
            best = detections.pop(0)
            keep.append(best)
            
            # Remove detections with high IoU with best
            remaining = []
            for det in detections:
                iou = self._calculate_iou(best['bbox'], det['bbox'])
                if iou < iou_threshold:
                    remaining.append(det)
            detections = remaining
        
        return keep
    
    @staticmethod
    def _calculate_iou(box1, box2):
        """Calculate IoU between two boxes."""
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2
        
        inter_xmin = max(x1_min, x2_min)
        inter_ymin = max(y1_min, y2_min)
        inter_xmax = min(x1_max, x2_max)
        inter_ymax = min(y1_max, y2_max)
        
        if inter_xmax < inter_xmin or inter_ymax < inter_ymin:
            return 0.0
        
        inter_area = (inter_xmax - inter_xmin) * (inter_ymax - inter_ymin)
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = box1_area + box2_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0