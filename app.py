import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from database import init_db, seed_db, get_db

app = Flask(__name__, static_folder=".")
CORS(app)

init_db()
seed_db()


def master_to_dict(row):
    d = dict(row)
    d["skills"] = d["skills"].split(",") if d.get("skills") else []
    d["online"] = bool(d["online"])
    return d


def shop_to_dict(row):
    d = dict(row)
    products = []
    raw = d.get("products") or ""
    for item in raw.split("|"):
        if "=" in item:
            parts = item.split("=", 1)
            emoji_name = parts[0].strip()
            price = parts[1].strip()
            # first char is emoji if it's wide
            emoji = emoji_name[0] if emoji_name else "📦"
            name = emoji_name[1:].strip() if len(emoji_name) > 1 else emoji_name
            products.append({"e": emoji, "n": name, "p": price})
    d["products"] = products
    return d


# ── Masters ────────────────────────────────────────────────────────────────

@app.route("/api/masters")
def get_masters():
    category = request.args.get("category", "")
    q = request.args.get("q", "").strip()
    conn = get_db()
    c = conn.cursor()
    sql = "SELECT * FROM masters WHERE active=1"
    params = []
    if category and category != "Все":
        sql += " AND category=?"
        params.append(category)
    if q:
        sql += " AND (name LIKE ? OR spec LIKE ? OR skills LIKE ?)"
        like = f"%{q}%"
        params += [like, like, like]
    sql += " ORDER BY CASE plan WHEN 'premium' THEN 1 WHEN 'pro' THEN 2 ELSE 3 END, rating DESC"
    rows = c.execute(sql, params).fetchall()
    conn.close()
    return jsonify([master_to_dict(r) for r in rows])


@app.route("/api/masters/<int:master_id>")
def get_master(master_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM masters WHERE id=? AND active=1", (master_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(master_to_dict(row))


@app.route("/api/masters/categories")
def get_categories():
    conn = get_db()
    rows = conn.execute("SELECT DISTINCT category FROM masters WHERE active=1 ORDER BY category").fetchall()
    conn.close()
    return jsonify([r["category"] for r in rows])


# ── Shops ──────────────────────────────────────────────────────────────────

@app.route("/api/shops")
def get_shops():
    category = request.args.get("category", "")
    q = request.args.get("q", "").strip()
    conn = get_db()
    sql = "SELECT * FROM shops WHERE active=1"
    params = []
    if category and category != "Все":
        sql += " AND category=?"
        params.append(category)
    if q:
        sql += " AND (name LIKE ? OR description LIKE ? OR category LIKE ?)"
        like = f"%{q}%"
        params += [like, like, like]
    sql += " ORDER BY CASE plan WHEN 'premium' THEN 1 WHEN 'pro' THEN 2 ELSE 3 END, name"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return jsonify([shop_to_dict(r) for r in rows])


@app.route("/api/shops/<int:shop_id>")
def get_shop(shop_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM shops WHERE id=? AND active=1", (shop_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(shop_to_dict(row))


@app.route("/api/shops/categories")
def get_shop_categories():
    conn = get_db()
    rows = conn.execute("SELECT DISTINCT category FROM shops WHERE active=1 ORDER BY category").fetchall()
    conn.close()
    return jsonify([r["category"] for r in rows])


# ── Requests ───────────────────────────────────────────────────────────────

@app.route("/api/requests", methods=["POST"])
def create_request():
    data = request.json or {}
    user_tg_id = data.get("user_tg_id")
    user_name = data.get("user_name", "").strip()
    user_phone = data.get("user_phone", "").strip()
    description = data.get("description", "").strip()
    master_id = data.get("master_id")
    shop_id = data.get("shop_id")
    request_type = data.get("request_type", "master")

    if not user_name or not user_phone:
        return jsonify({"error": "name and phone required"}), 400

    conn = get_db()
    conn.execute("""INSERT INTO requests
        (user_tg_id, user_name, user_phone, description, master_id, shop_id, request_type)
        VALUES (?,?,?,?,?,?,?)""",
        (user_tg_id, user_name, user_phone, description, master_id, shop_id, request_type))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "message": "Заявка принята"}), 201


@app.route("/api/requests")
def get_requests():
    tg_id = request.args.get("tg_id")
    if not tg_id:
        return jsonify({"error": "tg_id required"}), 400
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM requests WHERE user_tg_id=? ORDER BY created_at DESC",
        (tg_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ── Stats ──────────────────────────────────────────────────────────────────

@app.route("/api/stats")
def get_stats():
    conn = get_db()
    masters_count = conn.execute("SELECT COUNT(*) FROM masters WHERE active=1").fetchone()[0]
    shops_count = conn.execute("SELECT COUNT(*) FROM shops WHERE active=1").fetchone()[0]
    online_count = conn.execute("SELECT COUNT(*) FROM masters WHERE active=1 AND online=1").fetchone()[0]
    requests_count = conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
    conn.close()
    return jsonify({
        "masters": masters_count,
        "shops": shops_count,
        "online": online_count,
        "requests": requests_count,
    })


# ── Search ─────────────────────────────────────────────────────────────────

@app.route("/api/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"masters": [], "shops": []})
    like = f"%{q}%"
    conn = get_db()
    masters = conn.execute(
        "SELECT * FROM masters WHERE active=1 AND (name LIKE ? OR spec LIKE ? OR category LIKE ? OR skills LIKE ?) LIMIT 5",
        (like, like, like, like)
    ).fetchall()
    shops = conn.execute(
        "SELECT * FROM shops WHERE active=1 AND (name LIKE ? OR description LIKE ? OR category LIKE ?) LIMIT 5",
        (like, like, like)
    ).fetchall()
    conn.close()
    return jsonify({
        "masters": [master_to_dict(r) for r in masters],
        "shops": [shop_to_dict(r) for r in shops],
    })


# ── Static ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
