from flask import Blueprint, request, jsonify, session
from models.database import get_db, login_required
import json

favorites_bp = Blueprint('favorites', __name__)

@favorites_bp.route('/favorites', methods=['GET'])
@login_required
def get_favorites():
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, item_type, item_name, item_data, created_at FROM favorites WHERE user_id=%s ORDER BY created_at DESC", (user_id,))
            rows = cur.fetchall()
        result = []
        for r in rows:
            item = {"id": r["id"], "item_type": r["item_type"], "item_name": r["item_name"], "created_at": r["created_at"].isoformat() if r["created_at"] else None}
            if r["item_data"]:
                try:
                    item["item_data"] = json.loads(r["item_data"])
                except:
                    item["item_data"] = {}
            result.append(item)
        return jsonify({"favorites": result})
    finally:
        conn.close()

@favorites_bp.route('/favorites', methods=['POST'])
@login_required
def add_favorite():
    data = request.json
    user_id = session['user_id']
    item_type = data.get('item_type', '')
    item_name = data.get('item_name', '')
    item_data = data.get('item_data', {})
    if not item_type or not item_name:
        return jsonify({"error": "missing params"}), 400
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO favorites (user_id, item_type, item_name, item_data) VALUES (%s,%s,%s,%s)", (user_id, item_type, item_name, json.dumps(item_data, ensure_ascii=False)))
            conn.commit()
        return jsonify({"success": True, "action": "added"})
    except Exception:
        return jsonify({"error": "already favorited"}), 409
    finally:
        conn.close()

@favorites_bp.route('/favorites/<int:fav_id>', methods=['DELETE'])
@login_required
def remove_favorite(fav_id):
    user_id = session['user_id']
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM favorites WHERE id=%s AND user_id=%s", (fav_id, user_id))
            conn.commit()
        return jsonify({"success": True, "action": "removed"})
    finally:
        conn.close()

@favorites_bp.route('/favorites/check', methods=['POST'])
@login_required
def check_favorite():
    data = request.json
    user_id = session['user_id']
    item_type = data.get('item_type', '')
    item_name = data.get('item_name', '')
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM favorites WHERE user_id=%s AND item_type=%s AND item_name=%s", (user_id, item_type, item_name))
            row = cur.fetchone()
        return jsonify({"favorited": bool(row), "fav_id": row["id"] if row else None})
    finally:
        conn.close()
