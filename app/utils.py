import cv2
import numpy as np
from typing import List, Tuple


Color = Tuple[int, int, int]


def bgr_to_rgb(image: np.ndarray) -> np.ndarray:
	return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def rgb_to_bgr(image: np.ndarray) -> np.ndarray:
	return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)


def draw_boxes(
	image: np.ndarray,
	boxes: List[Tuple[int, int, int, int]],
	labels: List[str],
	colors: List[Color],
	score_texts: List[str] = None,
	hide_labels: bool = False,
) -> np.ndarray:
	output = image.copy()
	for i, (x1, y1, x2, y2) in enumerate(boxes):
		color = colors[i] if i < len(colors) else (0, 255, 0)
		cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
		if not hide_labels:
			label = labels[i] if i < len(labels) else ""
			score = score_texts[i] if score_texts and i < len(score_texts) else ""
			text = f"{label} {score}".strip()
			if text:
				cv2.putText(output, text, (x1, max(y1 - 5, 0)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
	return output


def put_banner_text(image: np.ndarray, text: str, color: Color = (0, 0, 255)) -> np.ndarray:
	output = image.copy()
	h, w = output.shape[:2]
	cv2.rectangle(output, (0, 0), (w, 24), (0, 0, 0), -1)
	cv2.putText(output, text, (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)
	return output


def clamp(value: float, min_value: float, max_value: float) -> float:
	return max(min_value, min(value, max_value))