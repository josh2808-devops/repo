from typing import Dict, List, Tuple

from .utils import clamp


def compute_signal_plan(lane_to_vehicle_count: Dict[int, int]) -> Tuple[int, List[int]]:
	"""
	Returns:
	- selected_lane: index of the lane that should get green now
	- green_durations: list of green durations (seconds) for each lane
	"""
	if not lane_to_vehicle_count:
		return 0, []
	lanes = sorted(lane_to_vehicle_count.keys())
	counts = [max(0, int(lane_to_vehicle_count[l])) for l in lanes]
	total = sum(counts)
	min_green, max_green = 10, 60
	if total == 0:
		# Default cycle 15s each
		return lanes[0], [15 for _ in lanes]
	green_durations: List[int] = []
	for c in counts:
		share = c / total
		seconds = int(round(clamp(share * 90, min_green, max_green)))
		green_durations.append(seconds)
	selected_lane = lanes[counts.index(max(counts))]
	return selected_lane, green_durations