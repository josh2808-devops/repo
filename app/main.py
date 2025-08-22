import os
import time
import io
from typing import List, Dict, Optional

import streamlit as st
import numpy as np
from dotenv import load_dotenv

from utils.auth import ensure_admin_bootstrap, login_form, session_auth_guard
from utils.notifications import Notifier, AlertType
from video.pipeline import process_frame_batch, IncidentEvent
from traffic.scheduler import AdaptiveScheduler

load_dotenv()

st.set_page_config(page_title="Smart & Secure Traffic Controller", layout="wide")

if "notifier" not in st.session_state:
	notifier = Notifier()
	st.session_state["notifier"] = notifier

# Bootstrap admin on first run
ensure_admin_bootstrap()

# Auth gate
user = session_auth_guard()
if user is None:
	login_form()
	st.stop()

# Sidebar configuration
with st.sidebar:
	st.header("Configuration")
	location_text = st.text_input("Area/Location", os.getenv("DEFAULT_LOCATION_TEXT", "City Center"))
	require_2fa = os.getenv("REQUIRE_2FA", "true").lower() == "true"
	st.caption(f"2FA required: {'Yes' if require_2fa else 'No'}")

st.title("Smart & Secure Real-Time Traffic Signal Controller")

st.markdown("Upload up to 9 videos. Processing is local. For demo purposes, incident detection uses heuristics.")

NUM_FEEDS = 9

if "uploaded_videos" not in st.session_state:
	st.session_state["uploaded_videos"] = [None] * NUM_FEEDS
if "schedulers" not in st.session_state:
	st.session_state["schedulers"] = [AdaptiveScheduler() for _ in range(NUM_FEEDS)]
if "latest_incidents" not in st.session_state:
	st.session_state["latest_incidents"] = [[] for _ in range(NUM_FEEDS)]
if "vehicle_counts" not in st.session_state:
	st.session_state["vehicle_counts"] = [0] * NUM_FEEDS

cols = st.columns(3)

uploaded_files = [None] * NUM_FEEDS

for i in range(NUM_FEEDS):
	with cols[i % 3]:
		st.subheader(f"Feed {i+1}")
		uploaded_file = st.file_uploader(f"Upload video {i+1}", type=["mp4","avi","mov","mkv"], key=f"upload_{i}")
		if uploaded_file is not None:
			st.session_state["uploaded_videos"][i] = uploaded_file.read()
			st.success("Uploaded")

run = st.button("Start Processing")

placeholders = [cols[i % 3].empty() for i in range(NUM_FEEDS)]
status_placeholders = [cols[i % 3].empty() for i in range(NUM_FEEDS)]

if run:
	progress_bar = st.progress(0, text="Processing feeds...")
	frames_per_batch = 16
	for step in range(50):
		for i in range(NUM_FEEDS):
			video_bytes = st.session_state["uploaded_videos"][i]
			if not video_bytes:
				continue
			frames, vehicle_count, incidents = process_frame_batch(video_bytes, frames_per_batch=frames_per_batch)
			st.session_state["vehicle_counts"][i] = vehicle_count
			st.session_state["latest_incidents"][i] = incidents

			# Update scheduler
			scheduler: AdaptiveScheduler = st.session_state["schedulers"][i]
			current_signal = scheduler.update_and_get_signal(vehicle_count)

			# Render
			placeholders[i].image(frames, channels="BGR", caption=f"Feed {i+1} - Vehicles: {vehicle_count} - Signal: {current_signal}")
			if incidents:
				incident_texts = [f"{ev.type.value} at {location_text} (confidence {ev.confidence:.2f})" for ev in incidents]
				status_placeholders[i].warning(" | ".join(incident_texts))

				# Notify (debounced)
				notifier: Notifier = st.session_state["notifier"]
				for ev in incidents:
					notifier.notify_incident(ev, location_text)
			else:
				status_placeholders[i].info(f"Signal: {st.session_state['schedulers'][i].last_signal}")

		progress_bar.progress(int((step+1)/50*100))
		time.sleep(0.05)

	st.success("Processing complete (demo loop)")

st.divider()

st.subheader("Recent Alerts")
for i in range(NUM_FEEDS):
	incidents = st.session_state["latest_incidents"][i]
	if incidents:
		with st.expander(f"Feed {i+1} incidents"):
			for ev in incidents:
				st.write(f"{ev.type.value} at {location_text} | confidence {ev.confidence:.2f}")