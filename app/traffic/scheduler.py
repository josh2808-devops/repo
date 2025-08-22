from dataclasses import dataclass


@dataclass
class AdaptiveScheduler:
	min_green: int = 10
	max_green: int = 60
	thresholds: tuple = (5, 15, 30)
	last_signal: str = "RED"
	remaining_seconds: int = 0

	def update_and_get_signal(self, vehicle_count: int) -> str:
		# Simple mapping: higher count -> longer green, else red/yellow
		if vehicle_count >= self.thresholds[2]:
			self.last_signal = "GREEN"
			self.remaining_seconds = min(self.max_green, 60)
		elif vehicle_count >= self.thresholds[1]:
			self.last_signal = "GREEN"
			self.remaining_seconds = 45
		elif vehicle_count >= self.thresholds[0]:
			self.last_signal = "GREEN"
			self.remaining_seconds = 20
		else:
			self.last_signal = "RED"
			self.remaining_seconds = 10
		return self.last_signal