import json
import time
from typing import List

from .config import AppSettings

try:
	from twilio.rest import Client  # type: ignore
	_TWILIO_AVAILABLE = True
except Exception:
	_TWILIO_AVAILABLE = False

import smtplib
from email.mime.text import MIMEText


class Notifier:
	def __init__(self, settings: AppSettings) -> None:
		self.settings = settings
		self._last_sent_ts = {}

	def _cooldown_ok(self, key: str) -> bool:
		cooldown = self.settings.incident_alert_cooldown_seconds
		now = time.time()
		last = self._last_sent_ts.get(key, 0)
		if now - last >= cooldown:
			self._last_sent_ts[key] = now
			return True
		return False

	def send_sms(self, to_number: str, message: str) -> None:
		if not (_TWILIO_AVAILABLE and self.settings.twilio_account_sid and self.settings.twilio_auth_token and self.settings.twilio_from_number):
			return
		client = Client(self.settings.twilio_account_sid, self.settings.twilio_auth_token)
		client.messages.create(to=to_number, from_=self.settings.twilio_from_number, body=message)

	def send_email(self, to_email: str, subject: str, message: str) -> None:
		if not self.settings.smtp_host or not self.settings.smtp_username or not self.settings.smtp_password:
			return
		msg = MIMEText(message)
		msg["Subject"] = subject
		msg["From"] = self.settings.alert_email_from
		msg["To"] = to_email
		server = smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port)
		if self.settings.smtp_use_tls:
			server.starttls()
		server.login(self.settings.smtp_username, self.settings.smtp_password)
		server.sendmail(self.settings.alert_email_from, [to_email], msg.as_string())
		server.quit()

	def notify_incident(self, incident_type: str, area_label: str, extra: str = "") -> None:
		key = f"{incident_type}:{area_label}"
		if not self._cooldown_ok(key):
			return
		contacts = getattr(self.settings.alert_contacts, incident_type, [])
		if not contacts:
			return
		subject = f"{incident_type.title()} detected at {area_label}"
		message = f"{incident_type.title()} detected at {area_label}. {extra}".strip()
		for contact in contacts:
			if contact.startswith("+"):
				self.send_sms(contact, message)
			elif "@" in contact:
				self.send_email(contact, subject, message)