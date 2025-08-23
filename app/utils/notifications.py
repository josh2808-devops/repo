import os
import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

import requests
import logging

class AlertType(Enum):
	ACCIDENT = "Accident"
	FIRE = "Fire"
	FLOOD = "Flood"


@dataclass
class AlertTarget:
	phone_numbers: List[str]
	emails: List[str]


class Notifier:
	def __init__(self) -> None:
		self.twilio_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
		self.twilio_token = os.getenv("TWILIO_AUTH_TOKEN", "")
		self.twilio_from = os.getenv("TWILIO_FROM_NUMBER", "")
		self.smtp_host = os.getenv("SMTP_HOST", "")
		self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
		self.smtp_username = os.getenv("SMTP_USERNAME", "")
		self.smtp_password = os.getenv("SMTP_PASSWORD", "")
		self.smtp_from = os.getenv("SMTP_FROM_EMAIL", "")
		self._last_sent_at = {}

	def _targets_for(self, alert_type: AlertType) -> AlertTarget:
		phone_env = {
			AlertType.ACCIDENT: os.getenv("ALERT_NUMBERS_ACCIDENT", ""),
			AlertType.FIRE: os.getenv("ALERT_NUMBERS_FIRE", ""),
			AlertType.FLOOD: os.getenv("ALERT_NUMBERS_FLOOD", ""),
		}[alert_type]
		email_env = {
			AlertType.ACCIDENT: os.getenv("ALERT_EMAILS_ACCIDENT", ""),
			AlertType.FIRE: os.getenv("ALERT_EMAILS_FIRE", ""),
			AlertType.FLOOD: os.getenv("ALERT_EMAILS_FLOOD", ""),
		}[alert_type]
		phones = [p.strip() for p in phone_env.split(",") if p.strip()]
		emails = [e.strip() for e in email_env.split(",") if e.strip()]
		return AlertTarget(phone_numbers=phones, emails=emails)

	def _debounced(self, key: str, seconds: int = 120) -> bool:
		now = time.time()
		last = self._last_sent_at.get(key, 0)
		if now - last >= seconds:
			self._last_sent_at[key] = now
			return True
		return False

	def notify_incident(self, incident_event, location_text: str) -> None:
		alert_type = incident_event.type
		message = f"{alert_type.value} detected at {location_text}. Confidence {incident_event.confidence:.2f}"
		key = f"{alert_type.value}:{location_text}"
		if not self._debounced(key):
			return
		targets = self._targets_for(alert_type)
		for number in targets.phone_numbers:
			self._send_sms(number, message)
		for email in targets.emails:
			self._send_email(email, f"{alert_type.value} Alert", message)

	def _send_sms(self, to_number: str, message: str) -> None:
		if not (self.twilio_sid and self.twilio_token and self.twilio_from):
			return
		try:
			url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json"
			resp = requests.post(url, auth=(self.twilio_sid, self.twilio_token), data={
				"From": self.twilio_from,
				"To": to_number,
				"Body": message,
			}, timeout=10)
			resp.raise_for_status()
		except Exception as exc:
			logging.exception("Failed to send SMS alert: %s", exc)

	def _send_email(self, to_email: str, subject: str, body: str) -> None:
		# Simplified: prefer using a service or SMTP library. Placeholder stub.
		# Intentionally no-op if SMTP not configured.
		return