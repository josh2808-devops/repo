# SMART & SECURE Real-Time Traffic Signal Controller (Software-Only)

A Streamlit-based system that:
- Detects vehicles and incidents (accident, fire, flood) from up to 9 video feeds
- Adapts signal timing dynamically based on live vehicle counts
- Secures access with Argon2id password hashing + TOTP (2FA) and lockouts
- Sends alerts (SMS/email) to appropriate contacts (police, fire, hospitals)
- Runs locally in VS Code on Linux (software-only)

## Features
- Upload and run up to 9 videos in a 3x3 dashboard
- YOLO-based detection with heuristic fallbacks
- Incident alerts with de-duplication and cooldown
- Strong authentication, session lockout, and rate-limit per user session

## Quick Start
1) Install system dependencies (Python 3.10+ recommended):
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

2) Configure environment
- Copy `.env.example` to `.env` and update values
- Generate admin credentials (Argon2 hash + TOTP):
```bash
python scripts/generate_admin.py --username admin --password YOUR_STRONG_PASSWORD
```
Copy the printed `ADMIN_PASSWORD_HASH` and `ADMIN_TOTP_SECRET` values into `.env`. Scan the TOTP URL (or QR) in Google Authenticator.

3) Run the app
```bash
streamlit run streamlit_app.py
```
Open the provided local URL in your browser, login with your admin account, upload up to 9 videos, and press Start.

## Security Notes
- Uses Argon2id with strong parameters (memory, iterations, parallelism)
- Enforces lockout after repeated failures per session
- TOTP (time-based one-time password) using RFC 6238 via `pyotp`
- Secrets must be set via environment variables; do not commit `.env`
- Network jamming prevention is outside software scope; we implement message signing and authentication where possible

## Alerts
- SMS via Twilio (set TWILIO_ env vars)
- Email via SMTP if configured
- Contacts can be set per incident type using `ALERT_CONTACTS_JSON`

## Notes on Models
- The app downloads a small YOLO model on first run (ultralytics). If offline, the app falls back to motion/color heuristics with reduced accuracy.

## Project Structure
```
.
├── streamlit_app.py
├── app/
│   ├── auth.py
│   ├── config.py
│   ├── detectors.py
│   ├── notifier.py
│   ├── pipeline.py
│   ├── signals.py
│   └── utils.py
├── scripts/
│   └── generate_admin.py
├── requirements.txt
├── .env.example
└── README.md
```

## Troubleshooting
- If video doesn’t render: ensure `opencv-python-headless` is installed and codecs supported
- For GPU acceleration, install CUDA-enabled PyTorch and `ultralytics`
- For SMS/email, verify credentials and reachable network
- Use smaller videos for testing to reduce CPU load