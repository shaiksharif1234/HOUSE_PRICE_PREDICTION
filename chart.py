import os
import sqlite3
import matplotlib.pyplot as plt

DB_NAME = "house.db"
OUTPUT_DIR = "static"
OUTPUT_FILE = "price_vs_area.png"

def generate_chart():
    # ---------------- CREATE STATIC FOLDER ----------------
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # ---------------- FETCH DATA ----------------
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT area, price, model
        FROM predictions
    """)
    data = cursor.fetchall()
    conn.close()

    if not data:
        print("No data available to generate chart.")
        return

    # ---------------- SPLIT DATA BY MODEL ----------------
    rf_area, rf_price = [], []
    gb_area, gb_price = [], []

    for area, price, model in data:
        if model == "Random Forest":
            rf_area.append(area)
            rf_price.append(price)
        else:
            gb_area.append(area)
            gb_price.append(price)

    # ---------------- PLOT ----------------
    plt.figure(figsize=(8, 5))

    if rf_area:
        plt.scatter(
            rf_area,
            rf_price,
            color="#667eea",
            alpha=0.7,
            label="Random Forest"
        )

    if gb_area:
        plt.scatter(
            gb_area,
            gb_price,
            color="#43cea2",
            alpha=0.7,
            label="Gradient Boosting"
        )

    plt.xlabel("Area (sq ft)")
    plt.ylabel("Price (₹)")
    plt.title("House Price Prediction: Area vs Price")
    plt.legend()
    plt.grid(alpha=0.3)

    # ---------------- SAVE ----------------
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    print(f"Chart saved at: {output_path}")
