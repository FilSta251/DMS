# -*- coding: utf-8 -*-
"""
Kontrola oprávnění: role → role_permissions, uživatelské výjimky → user_permissions.
"""
from database_manager import db

def has_permission(user_id: int, module_id: str, action: str) -> bool:
    perm = db.fetch_one("SELECT id FROM permissions WHERE module_id=? AND action=?", (module_id, action))
    if not perm:
        return False
    pid = perm['id']

    # Uživatelská výjimka?
    up = db.fetch_one("SELECT allowed FROM user_permissions WHERE user_id=? AND permission_id=?", (user_id, pid))
    if up is not None:
        return bool(up['allowed'])

    # Z role
    u = db.fetch_one("SELECT role FROM users WHERE id=?", (user_id,))
    if not u or not u['role']:
        return False
    role = db.fetch_one("SELECT id FROM roles WHERE name=?", (u['role'],))
    if not role:
        return False
    rp = db.fetch_one("SELECT allowed FROM role_permissions WHERE role_id=? AND permission_id=?", (role['id'], pid))
    return bool(rp and rp['allowed'] == 1)
