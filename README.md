# Smart & Secure Real-Time Traffic Signal Controller (Software)

A Streamlit-based dashboard that processes up to 9 video feeds to:
- Detect and count vehicles, adapt signal timing
- Heuristically detect incidents (accident, fire, flood)
- Notify authorities via SMS/Email when configured
- Secure login with Argon2 hashing and optional TOTP 2FA

## Requirements
- Python 3.10+
- VS Code or any IDE

## Setup
1. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```
3. Run the app:
```bash
streamlit run app/main.py
```

## Login Setup
On first run, you will be asked to create an admin account. Passwords are hashed with Argon2id. Optionally enable TOTP 2FA.

## Uploading Videos
Use the dashboard to upload up to 9 videos. Processing happens locally. No external services required.

## Notifications (Optional)
Set Twilio or SMTP variables in `.env` to enable SMS/Email alerts to the appropriate contacts.

## Notes
- This is a software-only demonstration. Preventing RF jamming is out of scope for pure software; the system uses retries and multiple channels for resilience.
- Incident detectors are heuristic and intended for demo; accuracy depends on video quality and scene setup.