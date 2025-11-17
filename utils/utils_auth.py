# -*- coding: utf-8 -*-
"""
Autentizace: správa aktuálního uživatele a hashování hesel (bcrypt).
"""
import bcrypt
from database_manager import db

# Jednoduchý "globální" stav aktuálního uživatele
_CURRENT_USER_ID = None
_CURRENT_USERNAME = None

def set_current_user(user_id: int, username: str):
    global _CURRENT_USER_ID, _CURRENT_USERNAME
    _CURRENT_USER_ID = user_id
    _CURRENT_USERNAME = username

def get_current_user_id():
    return _CURRENT_USER_ID

def get_current_username():
    return _CURRENT_USERNAME or ""

def is_bcrypt_hash(value: str) -> bool:
    return isinstance(value, str) and value.startswith("$2")

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, stored: str) -> bool:
    if not stored:
        return False
    if is_bcrypt_hash(stored):
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), stored.encode("utf-8"))
        except Exception:
            return False
    # fallback: porovnání s plaintextem (kvůli starým účtům)
    return plain == stored

def upgrade_password_to_bcrypt(user_id: int, plain: str, stored: str):
    """Pokud je v DB plaintext a ověření prošlo, přepiš na bcrypt hash."""
    if not is_bcrypt_hash(stored):
        new_hash = hash_password(plain)
        db.execute_query("UPDATE users SET password=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (new_hash, user_id))
