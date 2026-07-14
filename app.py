import os
import json
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from database import init_db, seed_db, seed_products, seed_owner_codes, seed_more_products, fix_broken_product_names, get_db

app = Flask(__name__, static_folder=".")
CORS(app)

init_db()
seed_db()
seed_products()
seed_owner_codes()
seed_more_products()
fix_broken_product_names()

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")


@app.route("/api/_debug/cleanup_smoketest2", methods=["POST"])
def _debug_cleanup_smoketest2():
    if request.headers.get("X-Debug-Token") != BOT_TOKEN:
        return jsonify({"error": "forbidden"}), 403
    conn = get_db()
    cur = conn.execute("DELETE FROM requests WHERE user_name='SmokeTest' AND user_phone='+70000000002'")
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "deleted": deleted})


def notify_telegram(chat_id, text):
    if not BOT_TOKEN or not chat_id:
        return False
    try:
        res = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
        return res.status_code == 200
    except requests.RequestException as e:
        app.logger.error("Telegram sendMessage error: %s", e)
        return False


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


@app.route("/api/shops/<int:shop_id>/question", methods=["POST"])
def shop_question(shop_id):
    data = request.json or {}
    user_tg_id = data.get("user_tg_id")
    user_name = (data.get("user_name") or "").strip()
    user_phone = (data.get("user_phone") or "").strip()
    question = (data.get("question") or "").strip()

    if not user_name or not user_phone or not question:
        return jsonify({"error": "user_name, user_phone and question required"}), 400

    conn = get_db()
    shop = conn.execute("SELECT name, owner_tg_id FROM shops WHERE id=?", (shop_id,)).fetchone()
    if not shop:
        conn.close()
        return jsonify({"error": "Shop not found"}), 404

    conn.execute("""INSERT INTO requests
        (user_tg_id, user_name, user_phone, description, shop_id, request_type)
        VALUES (?,?,?,?,?,?)""",
        (user_tg_id, user_name, user_phone, question, shop_id, "shop_question"))
    conn.commit()

    text = (
        f"❓ Вопрос о товаре — {shop['name']}\n\n"
        f"{question}\n\n"
        f"От: {user_name}, {user_phone}"
    )
    target_chat = shop["owner_tg_id"] or ADMIN_CHAT_ID
    notified = notify_telegram(target_chat, text)
    conn.close()
    return jsonify({"ok": True, "notified": notified}), 201


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


# ── Products / Cart / Orders ────────────────────────────────────────────────

@app.route("/api/products")
def get_products():
    shop_id = request.args.get("shop_id")
    conn = get_db()
    sql = "SELECT * FROM products WHERE active=1"
    params = []
    if shop_id:
        sql += " AND shop_id=?"
        params.append(shop_id)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/cart")
def get_cart():
    user_key = request.args.get("user_key", "")
    if not user_key:
        return jsonify({"error": "user_key required"}), 400
    conn = get_db()
    rows = conn.execute("""
        SELECT c.product_id, c.quantity, p.name, p.emoji, p.price, p.unit, p.shop_id, s.name AS shop_name
        FROM cart_items c
        JOIN products p ON p.id = c.product_id
        JOIN shops s ON s.id = p.shop_id
        WHERE c.user_key = ?
        ORDER BY p.shop_id, c.created_at
    """, (user_key,)).fetchall()
    conn.close()
    items = [dict(r) for r in rows]
    total = sum(i["price"] * i["quantity"] for i in items)
    return jsonify({"items": items, "total": total})


@app.route("/api/cart", methods=["POST"])
def update_cart():
    data = request.json or {}
    user_key = data.get("user_key")
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)
    if not user_key or not product_id:
        return jsonify({"error": "user_key and product_id required"}), 400

    conn = get_db()
    if quantity <= 0:
        conn.execute("DELETE FROM cart_items WHERE user_key=? AND product_id=?", (user_key, product_id))
    else:
        conn.execute("""
            INSERT INTO cart_items (user_key, product_id, quantity) VALUES (?,?,?)
            ON CONFLICT(user_key, product_id) DO UPDATE SET quantity = excluded.quantity
        """, (user_key, product_id, quantity))
    conn.commit()
    count = conn.execute(
        "SELECT COALESCE(SUM(quantity),0) FROM cart_items WHERE user_key=?", (user_key,)
    ).fetchone()[0]
    conn.close()
    return jsonify({"ok": True, "cart_count": count})


@app.route("/api/orders", methods=["POST"])
def create_order():
    data = request.json or {}
    user_key = data.get("user_key")
    customer_name = (data.get("customer_name") or "").strip()
    customer_phone = (data.get("customer_phone") or "").strip()
    customer_address = (data.get("customer_address") or "").strip()

    if not user_key or not customer_name or not customer_phone:
        return jsonify({"error": "user_key, customer_name and customer_phone required"}), 400

    conn = get_db()
    rows = conn.execute("""
        SELECT c.product_id, c.quantity, p.name, p.price, p.unit, p.shop_id, s.name AS shop_name, s.owner_tg_id
        FROM cart_items c
        JOIN products p ON p.id = c.product_id
        JOIN shops s ON s.id = p.shop_id
        WHERE c.user_key = ?
    """, (user_key,)).fetchall()

    if not rows:
        conn.close()
        return jsonify({"error": "Cart is empty"}), 400

    by_shop = {}
    for r in rows:
        by_shop.setdefault(r["shop_id"], []).append(r)

    order_ids = []
    for shop_id, items in by_shop.items():
        shop_name = items[0]["shop_name"]
        owner_tg_id = items[0]["owner_tg_id"]
        items_snapshot = [
            {"name": i["name"], "price": i["price"], "unit": i["unit"], "quantity": i["quantity"]}
            for i in items
        ]
        total = sum(i["price"] * i["quantity"] for i in items)

        cur = conn.execute("""
            INSERT INTO orders (user_key, customer_name, customer_phone, customer_address, shop_id, items_json, total)
            VALUES (?,?,?,?,?,?,?)
        """, (user_key, customer_name, customer_phone, customer_address, shop_id, json.dumps(items_snapshot, ensure_ascii=False), total))
        order_id = cur.lastrowid
        order_ids.append(order_id)

        lines = "\n".join(f"• {i['name']} x{i['quantity']} — {i['price']*i['quantity']}₽" for i in items)
        text = (
            f"🛒 ЗАКАЗ #{order_id} — {shop_name}\n\n"
            f"{lines}\n\nИтого: {total}₽\n\n"
            f"Покупатель: {customer_name}\nТелефон: {customer_phone}\n"
            f"Адрес: {customer_address or '—'}"
        )
        target_chat = owner_tg_id or ADMIN_CHAT_ID
        notified = notify_telegram(target_chat, text)
        conn.execute("UPDATE orders SET notified=? WHERE id=?", (1 if notified else 0, order_id))

    conn.execute("DELETE FROM cart_items WHERE user_key=?", (user_key,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "order_ids": order_ids}), 201


# ── Owner claim (магазины и мастера) ────────────────────────────────────────

@app.route("/api/owner/claim", methods=["POST"])
def owner_claim():
    data = request.json or {}
    telegram_id = data.get("telegram_id")
    code = (data.get("code") or "").strip().lower()
    if not telegram_id or not code:
        return jsonify({"error": "telegram_id and code required"}), 400

    conn = get_db()
    claimed = None
    for table in ("shops", "masters"):
        row = conn.execute(f"SELECT id, name, owner_tg_id FROM {table} WHERE owner_code=?", (code,)).fetchone()
        if row:
            if row["owner_tg_id"] and str(row["owner_tg_id"]) != str(telegram_id):
                conn.close()
                return jsonify({"error": "Код уже привязан к другому владельцу"}), 409
            conn.execute(f"UPDATE {table} SET owner_tg_id=? WHERE id=?", (telegram_id, row["id"]))
            claimed = {"type": "shop" if table == "shops" else "master", "id": row["id"], "name": row["name"]}
            break
    conn.commit()
    conn.close()

    if not claimed:
        return jsonify({"error": "Код не найден"}), 404
    return jsonify({"ok": True, "claimed": claimed})


@app.route("/api/owner/dashboard")
def owner_dashboard():
    telegram_id = request.args.get("telegram_id")
    if not telegram_id:
        return jsonify({"error": "telegram_id required"}), 400

    conn = get_db()
    shops = conn.execute("SELECT id, name FROM shops WHERE owner_tg_id=?", (telegram_id,)).fetchall()
    masters = conn.execute("SELECT id, name FROM masters WHERE owner_tg_id=?", (telegram_id,)).fetchall()

    shop_data = []
    for s in shops:
        orders = conn.execute(
            "SELECT * FROM orders WHERE shop_id=? ORDER BY created_at DESC LIMIT 50", (s["id"],)
        ).fetchall()
        shop_data.append({"id": s["id"], "name": s["name"], "orders": [dict(o) for o in orders]})

    master_data = []
    for m in masters:
        reqs = conn.execute(
            "SELECT * FROM requests WHERE master_id=? ORDER BY created_at DESC LIMIT 50", (m["id"],)
        ).fetchall()
        master_data.append({"id": m["id"], "name": m["name"], "requests": [dict(r) for r in reqs]})

    conn.close()
    return jsonify({"shops": shop_data, "masters": master_data})


# ── Static ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
