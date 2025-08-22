import io
import random
from typing import List, Tuple

import cv2
import numpy as np
from dataclasses import dataclass
from enum import Enum

from utils.notifications import AlertType


class SignalColor(str, Enum):
	RED = "RED"
	YELLOW = "YELLOW"
	GREEN = "GREEN"


@dataclass
class IncidentEvent:
	type: AlertType
	confidence: float


def _decode_video_to_frames(video_bytes: bytes, max_frames: int = 16) -> List[np.ndarray]:
	# Decode with OpenCV from memory buffer
	tmp = np.frombuffer(video_bytes, dtype=np.uint8)
	cap = cv2.VideoCapture()
	cap.open(cv2.imdecode(tmp, cv2.IMREAD_COLOR))
	# Fallback using VideoCapture from buffer not always supported; use VideoCapture with filename if needed.
	# For demo, attempt imdecode frames; if fails, generate placeholder frames.
	frames = []
	for i in range(max_frames):
		# Placeholder synthetic frames to avoid codec issues in demo
		frame = np.zeros((240, 320, 3), dtype=np.uint8)
		cv2.putText(frame, f"Frame {i}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
		frames.append(frame)
	return frames


def _count_vehicles(frames: List[np.ndarray]) -> int:
	# Simple motion-based heuristic as placeholder
	if not frames:
		return 0
	gray_frames = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
	diff_sum = 0
	for i in range(1, len(gray_frames)):
		diff = cv2.absdiff(gray_frames[i], gray_frames[i-1])
		_, th = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
		diff_sum += th.sum()
	# Map motion magnitude to a pseudo vehicle count
	count = int(min(50, diff_sum / 1e6))
	return count


def _detect_incidents(frames: List[np.ndarray]) -> List[IncidentEvent]:
	# Placeholder: random rare events to simulate detections
	incidents: List[IncidentEvent] = []
	if random.random() < 0.05:
		incidents.append(IncidentEvent(type=AlertType.ACCIDENT, confidence=round(random.uniform(0.6, 0.95), 2)))
	if random.random() < 0.02:
		incidents.append(IncidentEvent(type=AlertType.FIRE, confidence=round(random.uniform(0.6, 0.9), 2)))
	if random.random() < 0.02:
		incidents.append(IncidentEvent(type=AlertType.FLOOD, confidence=round(random.uniform(0.6, 0.9), 2)))
	return incidents


def process_frame_batch(video_bytes: bytes, frames_per_batch: int = 16) -> Tuple[np.ndarray, int, List[IncidentEvent]]:
	frames = _decode_video_to_frames(video_bytes, max_frames=frames_per_batch)
	vehicle_count = _count_vehicles(frames)
	incidents = _detect_incidents(frames)
	# Compose a grid image for display
	rows = 4
	cols = 4
	h, w, c = frames[0].shape
	canvas = np.zeros((rows*h, cols*w, 3), dtype=np.uint8)
	for idx, frame in enumerate(frames[:rows*cols]):
		r = idx // cols
		cidx = idx % cols
		canvas[r*h:(r+1)*h, cidx*w:(cidx+1)*w] = frame
	return canvas, vehicle_count, incidents