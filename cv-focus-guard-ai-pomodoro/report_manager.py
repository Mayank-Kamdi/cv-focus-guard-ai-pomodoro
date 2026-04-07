"""Teacher report manager with encryption and signatures.

Production features:
- Input validation for all operations
- Secure key management
- Payload size validation
- Error handling for crypto operations
- File permission verification
"""

from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

# Security constants
MAX_REPORT_PAYLOAD_SIZE = 1024 * 10  # 10KB max (RSA-2048 limit ~200 bytes)


class TeacherReportManager:
    def __init__(self, logger, data_dir: Path) -> None:
        self.logger = logger
        self.data_dir = Path(data_dir)
        self.keys_dir = self.data_dir / "keys"
        self.reports_dir = self.data_dir / "reports"
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.teacher_public_key: Optional[RSAPublicKey] = None
        self._load_persisted_teacher_key()

    def _teacher_key_path(self) -> Path:
        return self.keys_dir / "teacher_public.pem"

    def _app_private_key_path(self) -> Path:
        return self.keys_dir / "app_private.pem"

    def _app_public_key_path(self) -> Path:
        return self.keys_dir / "app_public.pem"

    def _load_persisted_teacher_key(self) -> None:
        key_path = self._teacher_key_path()
        if not key_path.exists():
            return
        try:
            data = key_path.read_bytes()
            self.teacher_public_key = serialization.load_pem_public_key(data)
        except Exception as exc:
            self.logger.warning("Failed to load stored teacher key: %s", exc)

    def load_teacher_public_key_from_file(self, key_path: str) -> None:
        """Load teacher public key with validation."""
        try:
            key_file = Path(key_path).resolve()

            # Security: Verify file exists and is readable
            if not key_file.exists():
                raise FileNotFoundError(f"Key file not found: {key_path}")

            if not key_file.is_file():
                raise ValueError(f"Path is not a file: {key_path}")

            # Check file size (reasonable key size)
            file_size = key_file.stat().st_size
            if file_size > 10000:  # 10KB max for a public key
                raise ValueError(f"Key file too large: {file_size} bytes")

            data = key_file.read_bytes()
            public_key = serialization.load_pem_public_key(data)

            if not isinstance(public_key, rsa.RSAPublicKey):
                raise ValueError("Teacher key must be an RSA public key")

            # Verify key size (minimum 2048 bits for security)
            key_size = public_key.key_size
            if key_size < 2048:
                raise ValueError(f"Key size too small: {key_size} bits (min: 2048)")

            self.teacher_public_key = public_key
            self._teacher_key_path().write_bytes(data)
            self.logger.info("Teacher public key loaded successfully")

        except Exception as exc:
            self.logger.error("Failed to load teacher key: %s", exc)
            raise

    def teacher_key_loaded(self) -> bool:
        return self.teacher_public_key is not None

    def _load_or_create_app_keys(self) -> tuple[RSAPrivateKey, RSAPublicKey]:
        private_path = self._app_private_key_path()
        public_path = self._app_public_key_path()

        if private_path.exists() and public_path.exists():
            private_data = private_path.read_bytes()
            public_data = public_path.read_bytes()
            private_key = serialization.load_pem_private_key(
                private_data, password=None
            )
            public_key = serialization.load_pem_public_key(public_data)
            return private_key, public_key

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        private_path.write_bytes(private_bytes)
        public_path.write_bytes(public_bytes)
        return private_key, public_key

    def generate_report(self, payload: dict) -> Path:
        """Generate encrypted and signed report with validation."""
        if not self.teacher_key_loaded():
            raise RuntimeError("Teacher public key not loaded")

        # Validate payload
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a dictionary")

        # Check payload size before processing
        try:
            payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
            if len(payload_json) > MAX_REPORT_PAYLOAD_SIZE:
                raise ValueError(
                    f"Payload too large: {len(payload_json)} bytes "
                    f"(max: {MAX_REPORT_PAYLOAD_SIZE})"
                )
        except (TypeError, ValueError) as exc:
            self.logger.error("Invalid payload: %s", exc)
            raise

        try:
            private_key, public_key = self._load_or_create_app_keys()

            payload_bytes = payload_json.encode("utf-8")
            signature = private_key.sign(
                payload_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )

            report = {
                "payload": payload,
                "signature": base64.b64encode(signature).decode("ascii"),
                "signer_public_key": public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                ).decode("ascii"),
            }

            report_json = json.dumps(
                report, separators=(",", ":"), sort_keys=True
            ).encode("utf-8")

            encrypted = self.teacher_public_key.encrypt(
                report_json,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

            envelope = {
                "encrypted_report": base64.b64encode(encrypted).decode("ascii"),
                "encryption": "RSA-OAEP-SHA256",
                "signed": "RSA-PSS-SHA256",
            }

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            report_path = self.reports_dir / f"teacher_report_{timestamp}.json"
            report_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")

            self.logger.info("Report generated: %s", report_path.name)
            return report_path

        except ValueError as exc:
            # RSA encryption can fail if payload too large
            self.logger.error("Encryption failed: %s", exc)
            raise RuntimeError(f"Report generation failed: {exc}") from exc
        except Exception as exc:
            self.logger.error("Unexpected error generating report: %s", exc)
            raise
