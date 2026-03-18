import pandas as pd
import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

# =====================================================
# PATHS
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "best_model.pkl")
MODEL_NAME_PATH = os.path.join(BASE_DIR, "best_model_name.pkl")
DATA_PATH = os.path.join(BASE_DIR, "data.csv")

best_model = None
best_name = "Random Forest"

# =====================================================
# TRAIN FUNCTION
# =====================================================
def train_and_save_model():
    global best_model, best_name

    print("🔄 Training Random Forest model...")

    data = pd.read_csv(DATA_PATH)

    # ✅ USE DATASET FEATURES
    feature_cols = [
        "Area", "Carpet_Area",
        "Bedrooms", "Bathrooms", "Balcony",
        "Floor_No", "Total_Floors",
        "Parking_Count", "Maintenance_Cost",
        "Lift", "Power_Backup", "Water_Supply",
        "WiFi", "Maintenance", "Fire_Safety",
        "CCTV", "Intercom", "Rainwater",
        "Visitor_Parking"
    ]

    X = data[feature_cols]
    y = data["Price"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=500,
        max_depth=14,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    score = r2_score(y_test, model.predict(X_test))
    print(f"✅ R² Score: {score:.4f}")

    joblib.dump(model, MODEL_PATH)
    joblib.dump("Random Forest", MODEL_NAME_PATH)

    best_model = model
    best_name = "Random Forest"

    print("✅ Model trained & saved")

# =====================================================
# LOAD MODEL
# =====================================================
def load_model():
    global best_model, best_name

    if not os.path.exists(MODEL_PATH):
        train_and_save_model()

    best_model = joblib.load(MODEL_PATH)
    best_name = joblib.load(MODEL_NAME_PATH)

load_model()

# =====================================================
# PREDICT FUNCTION (FIXED)
# =====================================================
def predict_price(
    area, bedrooms, bathrooms,
    parking, gym, pool, lift, security,
    garden, play_area, club_house,
    power_backup, water_supply,
    wifi, maintenance, fire_safety,
    cctv, intercom, rainwater, visitor_parking,
    property_type="apartment",
    quality="medium",
    carpet_area=0,
    parking_count=1,
    maintenance_cost=0
):

    # ---------- ML INPUT ----------
    input_data = [[
        area,
        carpet_area,
        bedrooms,
        bathrooms,
        0,              # Balcony
        1,              # Floor_No
        10,             # Total_Floors
        parking_count,
        maintenance_cost,
        lift,
        power_backup,
        water_supply,
        wifi,
        maintenance,
        fire_safety,
        cctv,
        intercom,
        rainwater,
        visitor_parking
    ]]

    ml_price = int(best_model.predict(input_data)[0])

    if ml_price < 500000:
        ml_price = 500000

    # ---------- AMENITY BONUS ----------
    amenity_details = {}

    if parking:
     amenity_details["Parking"] = 150000
    if gym:
     amenity_details["Gym"] = 200000
    if pool:
     amenity_details["Swimming Pool"] = 350000
    if lift:
     amenity_details["Lift"] = 100000
    if security:
     amenity_details["Security"] = 120000
    if power_backup:
     amenity_details["Power Backup"] = 160000
    if water_supply:
     amenity_details["Water Supply"] = 140000
    if wifi:
     amenity_details["WiFi"] = 90000
    if maintenance:
     amenity_details["Maintenance Service"] = 110000
    if fire_safety:
     amenity_details["Fire Safety"] = 125000
    if cctv:
     amenity_details["CCTV"] = 95000
    if intercom:
     amenity_details["Intercom"] = 85000
    if rainwater:
     amenity_details["Rainwater Harvesting"] = 105000
    if visitor_parking:
     amenity_details["Visitor Parking"] = 120000

    amenity_bonus = sum(amenity_details.values())

    
   # ---------- EXTRA BONUS (SMART & DYNAMIC) ----------
    amenity_count = len(amenity_details)

    extra_bonus = 0
    if amenity_count >= 5:
     extra_bonus += 30000
    if amenity_count >= 8:
     extra_bonus += 50000
    if amenity_count >= 12:
     extra_bonus += 80000
    
    final_price = ml_price + amenity_bonus + extra_bonus
    breakdown = {
    "ml_price": ml_price,
    "amenity_bonus": amenity_bonus,
    "amenity_details": amenity_details,
    "extra_bonus": extra_bonus,
    "final_price": final_price,
    "model_used": best_name
     }
    return final_price, breakdown
