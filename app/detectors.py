from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

import cv2
import numpy as np

try:
	from ultralytics import YOLO  # type: ignore
	_ULTRALYTICS_AVAILABLE = True
except Exception:
	_ULTRALYTICS_AVAILABLE = False

VEHICLE_CLASSES = {"car", "truck", "bus", "motorcycle"}


@dataclass
class Detection:
	bbox: Tuple[int, int, int, int]
	label: str
	score: float


class VehicleAndIncidentDetector:
	def __init__(self, model_name: str = "yolov8n.pt", conf: float = 0.35) -> None:
		self.conf = conf
		self.model = None
		if _ULTRALYTICS_AVAILABLE:
			try:
				self.model = YOLO(model_name)
			except Exception:
				self.model = None
		# State for simple heuristics
		self.prev_gray: Optional[np.ndarray] = None
		self.motion_energy_history: List[float] = []

	def _yolo_detect(self, frame: np.ndarray) -> List[Detection]:
		if self.model is None:
			return []
		results = self.model.predict(source=frame[:, :, ::-1], conf=self.conf, verbose=False)
		detections: List[Detection] = []
		if not results:
			return detections
		res = results[0]
		if res.boxes is None:
			return detections
		for b in res.boxes:
			cls_id = int(b.cls.item()) if hasattr(b.cls, "item") else int(b.cls)
			name = res.names.get(cls_id, str(cls_id)) if hasattr(res, "names") else str(cls_id)
			score = float(b.conf.item()) if hasattr(b.conf, "item") else float(b.conf)
			x1, y1, x2, y2 = [int(v) for v in b.xyxy.cpu().numpy().flatten().tolist()]
			detections.append(Detection((x1, y1, x2, y2), name, score))
		return detections

	def _heuristic_vehicle_detect(self, frame: np.ndarray) -> List[Detection]:
		# Very simple motion-based heuristic: detect moving blobs
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		gray = cv2.GaussianBlur(gray, (5, 5), 0)
		if self.prev_gray is None:
			self.prev_gray = gray
			return []
		diff = cv2.absdiff(self.prev_gray, gray)
		_, th = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
		th = cv2.dilate(th, None, iterations=2)
		contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		detections: List[Detection] = []
		for c in contours:
			area = cv2.contourArea(c)
			if area < 800:
				continue
			x, y, w, h = cv2.boundingRect(c)
			detections.append(Detection((x, y, x + w, y + h), "vehicle", 0.5))
		self.prev_gray = gray
		return detections

	def detect_vehicles(self, frame: np.ndarray) -> List[Detection]:
		if self.model is not None:
			dets = [d for d in self._yolo_detect(frame) if d.label in VEHICLE_CLASSES]
			return dets
		return self._heuristic_vehicle_detect(frame)

	def _compute_motion_energy(self, frame: np.ndarray) -> float:
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		gray = cv2.GaussianBlur(gray, (5, 5), 0)
		if self.prev_gray is None:
			self.prev_gray = gray
			return 0.0
		diff = cv2.absdiff(self.prev_gray, gray)
		energy = float(np.mean(diff))
		self.prev_gray = gray
		self.motion_energy_history.append(energy)
		if len(self.motion_energy_history) > 60:
			self.motion_energy_history = self.motion_energy_history[-60:]
		return energy

	def detect_incidents(self, frame: np.ndarray) -> Dict[str, bool]:
		# Heuristic incidents: accident, fire, flood
		incidents = {"accident": False, "fire": False, "flood": False}

		# Accident: spike in motion followed by sustained low motion with vehicles present
		energy = self._compute_motion_energy(frame)
		veh_present = len(self.detect_vehicles(frame)) >= 1
		if len(self.motion_energy_history) >= 20 and veh_present:
			recent = np.array(self.motion_energy_history[-10:])
			prev = np.array(self.motion_energy_history[-20:-10])
			if prev.mean() > 5.0 and recent.mean() < 2.0 and prev.mean() > recent.mean() * 2.5:
				incidents["accident"] = True

		# Fire: HSV threshold for fire-like regions
		hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
		lower_fire = np.array([0, 100, 150])
		upper_fire = np.array([35, 255, 255])
		mask_fire = cv2.inRange(hsv, lower_fire, upper_fire)
		fire_ratio = float(np.count_nonzero(mask_fire)) / float(frame.shape[0] * frame.shape[1])
		if fire_ratio > 0.05:
			incidents["fire"] = True

		# Flood: blue/cyan large area near bottom
		lower_water = np.array([80, 50, 50])
		upper_water = np.array([120, 255, 255])
		mask_water = cv2.inRange(hsv, lower_water, upper_water)
		bottom = mask_water[int(frame.shape[0] * 0.6) :, :]
		water_ratio = float(np.count_nonzero(bottom)) / float(bottom.size)
		if water_ratio > 0.2:
			incidents["flood"] = True

		return incidents