import csv
import io
from datetime import datetime

from flask import Flask, render_template, request, redirect, session, send_file
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash

from model import predict_price
from database import create_table, get_db, create_user_table

# ---------------- INIT ----------------
create_table()
create_user_table()


# ----------------------------------

app = Flask(__name__)
app.secret_key = "secret123"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

@app.context_processor
def inject_user():
    return {
        "is_admin": session.get("admin"),
        "is_user": session.get("user"),
        "user_name": session.get("user")
    }
# ---------------- ADMIN CREDENTIALS ----------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# ---------------- REALTIME NOTIFICATIONS ----------------

def send_notification(message, link="/user/history"):

    print("SENDING NOTIFICATION:", message)

    socketio.emit(
        "new_notification",
        {
            "message": message,
            "time": datetime.now().strftime("%H:%M"),
            "link": link
        }
    )
@socketio.on("connect")
def handle_connect():
    print("Client connected")
    
 
# ---------------- HOME ----------------
@app.route("/")
def home():
    try:
        conn = get_db()

        rows = conn.execute("""
            SELECT price, time
            FROM predictions
            ORDER BY id DESC
            LIMIT 5
        """).fetchall()

        count = len(rows)
        conn.close()

    except Exception as e:
        print("HOME ERROR:", e)
        rows = []
        count = 0

    return render_template(
        "index.html",
        notif_count=count,
        notifications=rows
    )
# ---------------- PREDICT ----------------
@app.route("/predict", methods=["GET", "POST"])
def predict():
    if request.method == "GET":
        return redirect("/")

    # ⭐ ADD THIS BLOCK
    required_fields = [
        "area",
        "bedrooms",
        "bathrooms",
        "location",
        "city",
        "house_age",
        "furnishing"
    ]

    for field in required_fields:
        value = request.form.get(field)

        if value is None or value.strip() == "":
            return render_template(
    "index.html",
    error="Please fill all required fields",
    form=request.form
)

    # -------- SAFE INTEGER CONVERTER --------
    def to_int(name, default=0):
        value = request.form.get(name)
        if value is None or value.strip() == "":
            return default
        try:
            return int(value)
        except ValueError:
            return default


    # -------- REQUIRED INPUTS (⭐ Mandatory) --------
    area = to_int("area")
    bedrooms = to_int("bedrooms")
    bathrooms = to_int("bathrooms")

    # -------- OPTIONAL NUMERIC INPUTS --------
    balcony = to_int("balcony")
    floor_no = to_int("floor_no")
    total_floors = to_int("total_floors")
    facing = to_int("facing")

    carpet_area = to_int("carpet_area", area)
    parking_count = to_int("parking_count", 1)
    maintenance_cost = to_int("maintenance_cost", 0)

    # -------- FURNISHING (STRING → NUMBER SAFE) --------
    furnishing_map = {
        "full": 2,
        "semi": 1,
        "unfurnished": 0
    }

    raw_furnishing = request.form.get("furnishing", "unfurnished")
    furnishing = furnishing_map.get(raw_furnishing, 0)

    # -------- AMENITIES SAFE --------
    def yes(name):
        return 1 if request.form.get(name) == "on" else 0

    amenities = {
        "parking": yes("parking"),
        "gym": yes("gym"),
        "pool": yes("pool"),
        "lift": yes("lift"),
        "security": yes("security"),
        "garden": yes("garden"),
        "play_area": yes("play_area"),
        "club_house": yes("club_house"),
        "power_backup": yes("power_backup"),
        "water_supply": yes("water_supply"),
        "wifi": yes("wifi"),
        "maintenance": yes("maintenance"),
        "fire_safety": yes("fire_safety"),
        "cctv": yes("cctv"),
        "intercom": yes("intercom"),
        "rainwater": yes("rainwater"),
        "visitor_parking": yes("visitor_parking"),
    }

    

    
    # 🚨 Prevent bad inputs
    if area <= 0 or bedrooms <= 0 or bathrooms <= 0:
     return render_template("index.html", error="Invalid property details")



    # -------- PREDICTION --------
    final_price, breakdown = predict_price(
    area=area,
    bedrooms=bedrooms,
    bathrooms=bathrooms,

    parking=amenities["parking"],
    gym=amenities["gym"],
    pool=amenities["pool"],
    lift=amenities["lift"],
    security=amenities["security"],
    garden=amenities["garden"],
    play_area=amenities["play_area"],
    club_house=amenities["club_house"],
    power_backup=amenities["power_backup"],
    water_supply=amenities["water_supply"],
    wifi=amenities["wifi"],
    maintenance=amenities["maintenance"],
    fire_safety=amenities["fire_safety"],
    cctv=amenities["cctv"],
    intercom=amenities["intercom"],
    rainwater=amenities["rainwater"],
    visitor_parking=amenities["visitor_parking"],

    property_type=request.form.get("property_type", "apartment"),
    quality=request.form.get("quality", "medium"),
    carpet_area=carpet_area,
    parking_count=parking_count,
    maintenance_cost=maintenance_cost
)

    # Get model name safely
    model_name = breakdown.get("model_used", "Best Model")


    # -------- SAVE TO DATABASE --------
    conn = get_db()
    user_email = session.get("user_email", "guest")

    conn.execute("""
    INSERT INTO predictions
    (area, bedrooms, bathrooms, model, price, time, user_email)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    area,
    bedrooms,
    bathrooms,
    model_name,
    final_price,
    datetime.now().strftime("%d %b %H:%M"),
    user_email
))
    conn.commit()

# Keep only latest 20 predictions
    conn.execute("""
DELETE FROM predictions
WHERE id NOT IN (
    SELECT id FROM predictions
    ORDER BY id DESC
    LIMIT 20
)
""")

    conn.commit()
    conn.close()

             # 🔔 SEND REALTIME NOTIFICATION
    send_notification(
    f"Prediction saved ₹{final_price:,}",
    "/user/history"
)

    return render_template(
    "result.html",
    price=final_price,
    breakdown=breakdown,
    model_used=model_name
)




# ---------------- ADMIN LOGIN ----------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin/dashboard")

        return render_template(
            "admin_login.html",
            error="Invalid admin credentials"
        )

    return render_template("admin_login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )
            conn.commit()
        except Exception as e:
            return render_template("signup.html", error="Email already exists")
        finally:
            conn.close()

        return redirect("/login_user")

    return render_template("signup.html")


   
@app.route("/login_user", methods=["GET", "POST"])
def login_user():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user"] = user["name"]
            session["user_email"] = user["email"]
            return redirect("/user_dashboard")

        return render_template("login_user.html", error="Invalid credentials")

    return render_template("login_user.html")
# ---------------- DASHBOARD ----------------
@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/admin/login")

    conn = get_db()
    rows = conn.execute("""
        SELECT id, area, bedrooms, bathrooms, model, price, time
        FROM predictions
        ORDER BY id DESC
    """).fetchall()
    conn.close()

    total_predictions = len(rows)
    models_used = set(r["model"] for r in rows)
    total_models = len(models_used)

    avg_price = (
        int(sum(r["price"] for r in rows) / total_predictions)
        if total_predictions else 0
    )

    chart_data = [{
        "x": r["area"],
        "y": r["price"],
        "model": r["model"],
        "time": r["time"]
    } for r in rows]

    return render_template(
        "admin_dashboard.html",
        predictions=rows,
        chart_data=chart_data,
        total_predictions=total_predictions,
        total_models=total_models,
        market_insight=avg_price
    )
    
@app.route("/user_dashboard")
def user_dashboard():
    if not session.get("user"):
        return redirect("/login_user")

    conn = get_db()
    rows = conn.execute("""
        SELECT price, time
        FROM predictions
        WHERE user_email = ?
        ORDER BY time ASC
    """, (session.get("user_email"),)).fetchall()
    conn.close()

    total_predictions = len(rows)
    prices = [r["price"] for r in rows]

    avg_price = int(sum(prices) / total_predictions) if prices else 0
    highest_price = max(prices) if prices else 0
    last_price = prices[-1] if prices else 0

    return render_template(
        "user_dashboard.html",
        user=session["user"],
        total_predictions=total_predictions,
        avg_price=avg_price,
        highest_price=highest_price,
        last_price=last_price
    )
@app.route("/user/history")
def user_history():
    if not session.get("user_email"):
        return redirect("/login_user")

    conn = get_db()
    rows = conn.execute("""
        SELECT id, area, bedrooms, bathrooms, model, price, time
        FROM predictions
        WHERE user_email = ?
        ORDER BY id DESC
    """, (session["user_email"],)).fetchall()
    conn.close()

    return render_template(
        "user_history.html",
        predictions=rows,
        user=session.get("user")
    )  
    
@app.route("/user/analytics")
def user_analytics():
    if not session.get("user_email"):
        return redirect("/login_user")

    conn = get_db()
    rows = conn.execute("""
        SELECT area, price
        FROM predictions
        WHERE user_email = ?
        ORDER BY id ASC
    """, (session["user_email"],)).fetchall()
    conn.close()

    areas = [r["area"] for r in rows]
    prices = [r["price"] for r in rows]

    return render_template(
        "user_analytics.html",
        areas=areas,
        prices=prices
    )
    
@app.route("/user/profile")
def user_profile():
    if not session.get("user_email"):
        return redirect("/login_user")

    conn = get_db()
    total = conn.execute(
        "SELECT COUNT(*) FROM predictions WHERE user_email = ?",
        (session["user_email"],)
    ).fetchone()[0]

    avg_price = conn.execute(
        "SELECT AVG(price) FROM predictions WHERE user_email = ?",
        (session["user_email"],)
    ).fetchone()[0]

    conn.close()

    return render_template(
        "user_profile.html",
        name=session["user"],
        email=session["user_email"],
        total=total,
        avg_price=int(avg_price) if avg_price else 0
    )
    

@app.route("/user/chart")
def user_chart():
    if not session.get("user"):
        return redirect("/login_user")

    conn = get_db()
    rows = conn.execute("""
        SELECT 
            substr(time,1,7) AS month,
            AVG(price) AS avg_price
        FROM predictions
        WHERE user_email = ?
        GROUP BY month
        ORDER BY month
    """, (session.get("user_email"),)).fetchall()
    conn.close()

    labels = [r["month"] for r in rows]
    prices = [int(r["avg_price"]) for r in rows]

    return render_template(
        "user_chart.html",
        labels=labels,
        prices=prices
    )
    
@app.route("/user/download")
def user_download():
    if not session.get("user"):
        return redirect("/login_user")

    conn = get_db()
    rows = conn.execute("""
        SELECT area, bedrooms, bathrooms, price, time
        FROM predictions
        WHERE user_email = ?
    """, (session.get("user_email"),)).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Area","Bedrooms","Bathrooms","Price","Date"])

    for r in rows:
        writer.writerow([r["area"], r["bedrooms"], r["bathrooms"], r["price"], r["time"]])

    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode()),
        as_attachment=True,
        download_name="my_predictions.csv",
        mimetype="text/csv"
    )
    
@app.route("/user/bar")
def user_bar():
    if not session.get("user"):
        return redirect("/login_user")

    conn = get_db()
    rows = conn.execute("""
        SELECT area, price
        FROM predictions
        WHERE user_email = ?
        ORDER BY time ASC
    """, (session.get("user_email"),)).fetchall()
    conn.close()

    areas = [r["area"] for r in rows]
    prices = [r["price"] for r in rows]

    return render_template(
        "user_bar.html",
        areas=areas,
        prices=prices
    )
    
@app.route("/user/multi")
def user_multi():
    if not session.get("user"):
        return redirect("/login_user")

    conn = get_db()
    rows = conn.execute("""
        SELECT area, AVG(price) avg_price
        FROM predictions
        WHERE user_email = ?
        GROUP BY area
    """, (session.get("user_email"),)).fetchall()
    conn.close()

    areas = [str(r["area"]) for r in rows]
    prices = [int(r["avg_price"]) for r in rows]

    return render_template(
        "user_multi.html",
        areas=areas,
        prices=prices
    )
# ---------------- DELETE PREDICTION ----------------
@app.route("/delete/<int:id>")
def delete_prediction(id):
    if not session.get("admin"):
        return redirect("/admin/login")

    conn = get_db()
    conn.execute("DELETE FROM predictions WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin/dashboard")

@app.route("/user/delete/<int:id>")
def user_delete_prediction(id):
    # User must be logged in
    if not session.get("user_email"):
        return redirect("/login_user")

    conn = get_db()

    # Delete ONLY user's own prediction
    conn.execute("""
        DELETE FROM predictions
        WHERE id = ? AND user_email = ?
    """, (id, session["user_email"]))

    conn.commit()
    conn.close()

    return redirect("/user/history")

@app.route("/market_insights")
def market_insights():

    market_data = {
        "Hyderabad": 6500,
        "Bangalore": 8200,
        "Chennai": 5900,
        "Mumbai": 10500,
        "Delhi": 9000
    }

    return render_template("market_insights.html", data=market_data)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():

    # 👉 GET request (page open)
    if request.method == "GET":
        return render_template("contact.html")

    # 👉 POST request (form submit)
    name = request.form.get("name")
    email = request.form.get("email")
    message = request.form.get("message")

    print("Name:", name)
    print("Email:", email)
    print("Message:", message)

    return "Message Received Successfully!"
# ---------------- DOWNLOAD CSV ----------------
@app.route("/download")
def download_csv():
    if not session.get("admin"):
        return redirect("/admin/login")

    conn = get_db()
    rows = conn.execute("""
        SELECT area, bedrooms, bathrooms, model, price, time
        FROM predictions
    """).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Area", "Bedrooms", "Bathrooms", "Model", "Price", "Date"])
    for r in rows:
        writer.writerow([
            r["area"], r["bedrooms"], r["bathrooms"],
            r["model"], r["price"], r["time"]
        ])

    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="house_price_predictions.csv"
    )

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/user/logout")
def logout_user():
    session.pop("user", None)
    session.pop("user_email", None)
    return redirect("/")
# ---------------- RUN ----------------

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)