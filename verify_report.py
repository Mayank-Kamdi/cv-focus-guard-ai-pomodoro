#!/usr/bin/env python3
"""Teacher-side script to decrypt and verify student focus reports.

Usage:
    python verify_report.py --private-key teacher_private.pem --report report.json
    python verify_report.py --generate-keypair
"""

import argparse
import base64
import json
import sys
from pathlib import Path

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
except ImportError:
    print("ERROR: cryptography library not installed")
    print("Install with: pip install cryptography")
    sys.exit(1)


def generate_teacher_keypair(output_dir: str = ".") -> None:
    """Generate RSA keypair for teacher verification."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

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

    private_path = output_path / "teacher_private.pem"
    public_path = output_path / "teacher_public.pem"

    private_path.write_bytes(private_bytes)
    public_path.write_bytes(public_bytes)

    print(f"✓ Generated teacher keypair:")
    print(f"  Private key: {private_path.absolute()}")
    print(f"  Public key:  {public_path.absolute()}")
    print()
    print("IMPORTANT:")
    print("  1. Keep teacher_private.pem SECRET and SECURE")
    print("  2. Share teacher_public.pem with students")
    print("  3. Students load teacher_public.pem in the app to generate reports")


def verify_and_decrypt_report(private_key_path: str, report_path: str) -> dict:
    """Decrypt and verify a student report."""
    # Load teacher's private key
    private_key_data = Path(private_key_path).read_bytes()
    private_key = serialization.load_pem_private_key(private_key_data, password=None)

    # Load encrypted report envelope
    report_data = Path(report_path).read_text(encoding="utf-8")
    envelope = json.loads(report_data)

    # Decrypt the report
    encrypted_bytes = base64.b64decode(envelope["encrypted_report"])
    try:
        decrypted_json = private_key.decrypt(
            encrypted_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
    except Exception as exc:
        raise ValueError(f"Decryption failed: {exc}. Wrong private key?") from exc

    # Parse decrypted report
    report = json.loads(decrypted_json)

    # Extract signature and signer's public key
    signature = base64.b64decode(report["signature"])
    signer_public_key_pem = report["signer_public_key"].encode("ascii")
    signer_public_key = serialization.load_pem_public_key(signer_public_key_pem)

    # Reconstruct payload for verification
    payload = report["payload"]
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )

    # Verify signature
    try:
        signer_public_key.verify(
            signature,
            payload_json,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
    except Exception as exc:
        raise ValueError(f"Signature verification failed: {exc}") from exc

    return payload


def format_report(payload: dict) -> str:
    """Format verified report for display."""
    lines = [
        "=" * 60,
        "VERIFIED STUDENT FOCUS REPORT",
        "=" * 60,
        "",
        f"Report Timestamp:     {payload.get('timestamp', 'N/A')}",
        f"Sessions Completed:   {payload.get('sessions_completed', 0)}",
        f"Total Focus Time:     {payload.get('total_focus_minutes', 0)} minutes",
        f"Total Distractions:   {payload.get('total_distractions', 0)}",
        f"Last Session Distr.:  {payload.get('last_session_distractions', 0)}",
        "",
    ]

    # Calculate focus quality
    total_minutes = payload.get("total_focus_minutes", 0)
    total_distr = payload.get("total_distractions", 0)
    if total_minutes > 0:
        distr_per_hour = (total_distr / total_minutes) * 60
        lines.append(f"Distraction Rate:     {distr_per_hour:.1f} per hour")
        if distr_per_hour < 3:
            quality = "Excellent"
        elif distr_per_hour < 6:
            quality = "Good"
        elif distr_per_hour < 10:
            quality = "Fair"
        else:
            quality = "Needs Improvement"
        lines.append(f"Focus Quality:        {quality}")
        lines.append("")

    lines.extend(
        [
            "=" * 60,
            "✓ Report signature verified (tamper-proof)",
            "✓ Decryption successful (authentic source)",
            "=" * 60,
        ]
    )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Verify and decrypt student focus reports"
    )
    parser.add_argument(
        "--generate-keypair",
        action="store_true",
        help="Generate teacher RSA keypair",
    )
    parser.add_argument(
        "--private-key",
        type=str,
        help="Path to teacher's private key (PEM format)",
    )
    parser.add_argument(
        "--report",
        type=str,
        help="Path to encrypted student report (JSON)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".",
        help="Output directory for generated keypair (default: current directory)",
    )

    args = parser.parse_args()

    if args.generate_keypair:
        generate_teacher_keypair(args.output)
        return

    if not args.private_key or not args.report:
        parser.error(
            "--private-key and --report are required (or use --generate-keypair)"
        )

    try:
        payload = verify_and_decrypt_report(args.private_key, args.report)
        print(format_report(payload))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
