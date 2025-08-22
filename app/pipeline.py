import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

import cv2
import numpy as np

from .detectors import VehicleAndIncidentDetector
from .utils import draw_boxes


@dataclass
class StreamState:
	frame_bgr: Optional[np.ndarray] = None
	vehicle_count: int = 0
	incidents: Dict[str, bool] = field(default_factory=lambda: {"accident": False, "fire": False, "flood": False})
	last_updated_ts: float = 0.0


class VideoWorker(threading.Thread):
	def __init__(self, stream_id: int, source_path: str, model_name: str, conf: float) -> None:
		super().__init__(daemon=True)
		self.stream_id = stream_id
		self.source_path = source_path
		self.detector = VehicleAndIncidentDetector(model_name, conf)
		self.state = StreamState()
		self._stop_event = threading.Event()

	def stop(self) -> None:
		self._stop_event.set()

	def run(self) -> None:
		cap = cv2.VideoCapture(self.source_path)
		if not cap.isOpened():
			return
		while not self._stop_event.is_set():
			ret, frame = cap.read()
			if not ret:
				cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
				continue
			dets = self.detector.detect_vehicles(frame)
			boxes = [d.bbox for d in dets]
			labels = [d.label for d in dets]
			scores = [f"{d.score:.2f}" for d in dets]
			overlay = draw_boxes(frame, boxes, labels, [(0, 255, 0)] * len(boxes), scores)
			incidents = self.detector.detect_incidents(frame)
			self.state.frame_bgr = overlay
			self.state.vehicle_count = len(dets)
			self.state.incidents = incidents
			self.state.last_updated_ts = time.time()
			time.sleep(0.03)
		cap.release()