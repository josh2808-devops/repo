import os
import json
import base64
from typing import Optional

import streamlit as st
from passlib.hash import argon2
import pyotp

USERS_DB_FILE = "/workspace/app_data/users.json"


def _load_users() -> dict:
	if not os.path.exists(USERS_DB_FILE):
		return {}
	with open(USERS_DB_FILE, "r") as f:
		try:
			return json.load(f)
		except Exception:
			return {}


def _save_users(users: dict) -> None:
	os.makedirs(os.path.dirname(USERS_DB_FILE), exist_ok=True)
	with open(USERS_DB_FILE, "w") as f:
		json.dump(users, f)


def ensure_admin_bootstrap() -> None:
	users = _load_users()
	if users:
		return
	st.sidebar.header("Admin Setup")
	with st.sidebar.form("admin_setup"):
		st.write("Create an admin account (first run)")
		username = st.text_input("Admin Username", value="admin")
		password = st.text_input("Admin Password", type="password")
		confirm = st.text_input("Confirm Password", type="password")
		setup = st.form_submit_button("Create Admin")
		if setup:
			if not username or not password or password != confirm:
				st.error("Invalid input or passwords do not match")
				st.stop()
			users[username] = {
				"password_hash": argon2.hash(password),
				"totp_secret": "",
				"is_admin": True,
			}
			_save_users(users)
			st.success("Admin created. Please log in.")


def login_form():
	st.header("Login")
	users = _load_users()
	with st.form("login_form"):
		username = st.text_input("Username")
		password = st.text_input("Password", type="password")
		submit = st.form_submit_button("Login")
		if submit:
			user = users.get(username)
			if not user or not argon2.verify(password, user.get("password_hash", "")):
				st.error("Invalid username or password")
				st.stop()
			st.session_state["auth_user"] = username
			# 2FA step if required and user has secret
			require_2fa = os.getenv("REQUIRE_2FA", "true").lower() == "true"
			if require_2fa and user.get("totp_secret"):
				st.session_state["require_otp"] = True
				st.experimental_rerun()

	if st.session_state.get("require_otp"):
		st.subheader("Two-Factor Authentication")
		with st.form("totp_form"):
			otp = st.text_input("Enter 6-digit code")
			verify = st.form_submit_button("Verify")
			if verify:
				user = _load_users().get(st.session_state.get("auth_user"))
				if not user:
					st.error("Session expired")
					st.stop()
				totp = pyotp.TOTP(user.get("totp_secret")) if user.get("totp_secret") else None
				if totp and totp.verify(otp):
					st.session_state["authenticated"] = True
					st.session_state.pop("require_otp", None)
					st.experimental_rerun()
				else:
					st.error("Invalid code")

	# Offer TOTP enrollment for logged-in users
	if st.session_state.get("auth_user") and not st.session_state.get("require_otp"):
		users = _load_users()
		user = users.get(st.session_state.get("auth_user"))
		if user and not user.get("totp_secret"):
			st.info("Optional: Enable two-factor authentication")
			with st.form("enroll_totp"):
				secret = pyotp.random_base32()
				provisioning_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=st.session_state.get("auth_user"), issuer_name="SmartTraffic")
				st.write("Add to Authenticator app with this secret:")
				st.code(secret)
				enroll = st.form_submit_button("Enable 2FA")
				if enroll:
					user["totp_secret"] = secret
					users[st.session_state.get("auth_user")] = user
					_save_users(users)
					st.success("2FA enabled.")


def session_auth_guard() -> Optional[str]:
	if st.session_state.get("authenticated"):
		return st.session_state.get("auth_user")
	# If no 2FA required, authenticating after password is enough
	if st.session_state.get("auth_user") and not st.session_state.get("require_otp"):
		st.session_state["authenticated"] = True
		return st.session_state.get("auth_user")
	return None