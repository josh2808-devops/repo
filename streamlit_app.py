import os
import tempfile
from typing import List, Dict

import streamlit as st
import numpy as np
import cv2

from app.config import load_settings
from app.auth import AuthState, verify_password, verify_totp, register_failure, register_success
from app.pipeline import VideoWorker
from app.notifier import Notifier
from app.signals import compute_signal_plan
from app.utils import bgr_to_rgb


st.set_page_config(page_title="Smart & Secure Traffic Controller", layout="wide")
settings = load_settings()

if "auth_state" not in st.session_state:
	st.session_state.auth_state = AuthState()
if "authenticated" not in st.session_state:
	st.session_state.authenticated = False
if "workers" not in st.session_state:
	st.session_state.workers = {}
if "temp_paths" not in st.session_state:
	st.session_state.temp_paths = []


def login_form() -> None:
	st.title("Login")
	with st.form("login_form", clear_on_submit=False):
		username = st.text_input("Username")
		password = st.text_input("Password", type="password")
		totp = st.text_input("TOTP Code", help="From your authenticator app")
		submit = st.form_submit_button("Login")
		if submit:
			remaining = None
			if remaining := (register_lock := None) or None:
				pass
			# lockout check
			from app.auth import lockout_check
			rem = lockout_check(st.session_state.auth_state)
			if rem is not None:
				st.error(f"Account locked. Try again in {rem} seconds.")
				return
			if username != settings.admin_username:
				register_failure(st.session_state.auth_state)
				st.error("Invalid credentials.")
				return
			if not (settings.admin_password_hash and verify_password(password, settings.admin_password_hash)):
				register_failure(st.session_state.auth_state)
				st.error("Invalid credentials.")
				return
			if settings.admin_totp_secret:
				if not verify_totp(settings.admin_totp_secret, totp):
					register_failure(st.session_state.auth_state)
					st.error("Invalid TOTP code.")
					return
			register_success(st.session_state.auth_state)
			st.session_state.authenticated = True
			st.success("Logged in.")
			st.experimental_rerun()


def stop_all_workers() -> None:
	workers: Dict[int, VideoWorker] = st.session_state.workers
	for wid, w in list(workers.items()):
		w.stop()
		workers.pop(wid, None)


def app_main() -> None:
	notifier = Notifier(settings)
	st.title("SMART & SECURE Real-Time Traffic Signal Controller")
	st.caption("Upload up to 9 videos. Processing runs locally. Alerts are optional.")

	with st.sidebar:
		st.subheader("Controls")
		start = st.button("Start Processing")
		stop = st.button("Stop Processing")
		if stop:
			stop_all_workers()
		uploaded = st.file_uploader("Upload up to 9 videos", type=["mp4", "avi", "mov", "mkv"], accept_multiple_files=True)

	if stop:
		st.info("Stopped all streams.")

	if start and uploaded:
		stop_all_workers()
		st.session_state.temp_paths = []
		for idx, f in enumerate(uploaded[: settings.max_concurrent_streams]):
			# Save to temp file for OpenCV
			tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{idx}.mp4")
			tmp.write(f.read())
			tmp.flush()
			tmp.close()
			st.session_state.temp_paths.append(tmp.name)
			worker = VideoWorker(idx, tmp.name, settings.yolo_model_name, settings.detection_confidence)
			st.session_state.workers[idx] = worker
			worker.start()

	# Dashboard grid
	ncols = 3
	cols = st.columns(ncols)
	lane_vehicle_counts: Dict[int, int] = {}
	for idx in range(settings.max_concurrent_streams):
		col = cols[idx % ncols]
		with col:
			ph = st.empty()
			worker = st.session_state.workers.get(idx)
			if worker and worker.state.frame_bgr is not None:
				img = bgr_to_rgb(worker.state.frame_bgr)
				ph.image(img, caption=f"Stream {idx}")
				lane_vehicle_counts[idx] = worker.state.vehicle_count
				# Incident banners and notifications
				for inc, flag in worker.state.incidents.items():
					if flag:
						st.error(f"{inc.title()} detected on Stream {idx}")
						area = settings.site_location_label or f"Stream {idx}"
						notifier.notify_incident(inc, area)
			else:
				ph.write("Waiting for stream...")

	# Signal recommendation
	if lane_vehicle_counts:
		selected, durations = compute_signal_plan(lane_vehicle_counts)
		st.subheader("Adaptive Signal Recommendation")
		st.write(f"Give GREEN to lane {selected} now.")
		st.write({f"lane_{i}": d for i, d in enumerate(durations)})

	st.markdown("---")
	st.caption("Security: Argon2id + TOTP; session lockouts and optional alerts.")


if __name__ == "__main__":
	if not st.session_state.get("authenticated"):
		login_form()
	else:
		app_main()