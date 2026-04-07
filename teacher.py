import secrets
import string
from pathlib import Path

class TeacherKeyManager:
    def __init__(self, keys_dir: Path):
        self.keys_dir = Path(keys_dir)
        self.keys_dir.mkdir(parents=True, exist_ok=True)

    def generate_key(self, length: int = 8) -> str:
        """Generate a secure random teacher key and ensure no collisions."""
        alphabet = string.ascii_uppercase + string.digits
        while True:
            key = ''.join(secrets.choice(alphabet) for _ in range(length))
            if not self.key_exists(key):
                self.save_teacher_key(key)
                return key

    def save_teacher_key(self, key: str):
        """Save a generated key to a file to prevent future collisions."""
        key_file = self.keys_dir / f"teacher_{key}.txt"
        key_file.touch()

    def key_exists(self, key: str) -> bool:
        """Check if a teacher key already exists."""
        return (self.keys_dir / f"teacher_{key}.txt").exists()

    def validate_key(self, key: str) -> bool:
        """Validate if a teacher key is valid (8 chars and exists)."""
        if not key or len(key) != 8:
            return False
        # In a real production system, this would check a central DB.
        # For now, we check the local keys_dir.
        return self.key_exists(key)
