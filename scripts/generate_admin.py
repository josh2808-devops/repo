#!/usr/bin/env python3
import argparse
import os

import pyotp
import qrcode
from passlib.hash import argon2

ARGON2_PARAMS = {
	"time_cost": 3,
	"memory_cost": 102400,
	"parallelism": 8,
}


def main() -> None:
	parser = argparse.ArgumentParser(description="Generate admin credentials for .env")
	parser.add_argument("--username", required=True)
	parser.add_argument("--password", required=True)
	parser.add_argument("--issuer", default="SmartSecureTraffic")
	args = parser.parse_args()

	password_hash = argon2.using(**ARGON2_PARAMS).hash(args.password)
	totp_secret = pyotp.random_base32()
	uri = pyotp.TOTP(totp_secret).provisioning_uri(name=args.username, issuer_name=args.issuer)

	print("Add these lines to your .env:")
	print(f"ADMIN_USERNAME={args.username}")
	print(f"ADMIN_PASSWORD_HASH={password_hash}")
	print(f"ADMIN_TOTP_SECRET={totp_secret}")
	print("\nScan this TOTP URI with your authenticator app:")
	print(uri)
	try:
		img = qrcode.make(uri)
		path = os.path.abspath("admin_totp_qr.png")
		img.save(path)
		print(f"Saved QR to {path}")
	except Exception:
		pass


if __name__ == "__main__":
	main()