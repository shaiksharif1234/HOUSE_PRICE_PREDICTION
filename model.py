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
FEATURE_PATH = os.path.join(BASE_DIR, "features.pkl")
DATA_PATH = os.path.join(BASE_DIR, "data.csv")

best_model = None
best_name = "Random Forest"
feature_columns = None


# =====================================================
# TRAIN FUNCTION
# =====================================================
def train_and_save_model():
    global best_model, best_name, feature_columns

    print("🔄 Training Random Forest model...")

    data = pd.read_csv(DATA_PATH)

    # ================================
    # ✅ CLEAN STRING COLUMNS
    # ================================
    for col in data.columns:
        if data[col].dtype == "object":
            # extract numbers like "0-5" → 0, "10 years" → 10
            data[col] = data[col].astype(str).str.extract(r'(\d+)')
    
    # convert all to numeric
    data = data.apply(pd.to_numeric, errors="coerce")

    # fill missing values
    data.fillna(0, inplace=True)

    # ================================
    # ✅ ONE HOT ENCODING (CITY)
    # ================================
    if "City" in data.columns:
        data = pd.get_dummies(data, columns=["City"])

    # ================================
    # FEATURES
    # ================================
    feature_columns = list(data.columns)

    if "Price" not in feature_columns:
        raise Exception("❌ 'Price' column missing in dataset")

    feature_columns.remove("Price")

    X = data[feature_columns]
    y = data["Price"]

    # ================================
    # TRAIN
    # ================================
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    score = r2_score(y_test, model.predict(X_test))
    print(f"✅ R² Score: {score:.4f}")

    # ================================
    # SAVE
    # ================================
    joblib.dump(model, MODEL_PATH)
    joblib.dump("Random Forest", MODEL_NAME_PATH)
    joblib.dump(feature_columns, FEATURE_PATH)

    best_model = model
    best_name = "Random Forest"

    print("✅ Model trained & saved")


# =====================================================
# LOAD MODEL
# =====================================================
def load_model():
    global best_model, best_name, feature_columns

    if not os.path.exists(MODEL_PATH):
        train_and_save_model()

    best_model = joblib.load(MODEL_PATH)
    best_name = joblib.load(MODEL_NAME_PATH)
    feature_columns = joblib.load(FEATURE_PATH)


load_model()


# =====================================================
# PREDICT FUNCTION
# =====================================================
def predict_price(
    area, bedrooms, bathrooms,
    city,
    parking, gym, pool, lift, security,
    garden, play_area, club_house,
    power_backup, water_supply,
    wifi,
    fire_safety, cctv, intercom,
    property_type="apartment",
    quality="medium",
    carpet_area=0,
    parking_count=1,
    maintenance_cost=0
):

    # ================================
    # BUILD INPUT
    # ================================
    input_dict = {col: 0 for col in feature_columns}

    input_dict["Area"] = area
    input_dict["Carpet_Area"] = carpet_area
    input_dict["Bedrooms"] = bedrooms
    input_dict["Bathrooms"] = bathrooms
    input_dict["Parking_Count"] = parking_count
    input_dict["Maintenance_Cost"] = maintenance_cost

    # Amenities
    input_dict["Lift"] = lift
    input_dict["Power_Backup"] = power_backup
    input_dict["Water_Supply"] = water_supply
    input_dict["WiFi"] = wifi
    
    input_dict["Fire_Safety"] = fire_safety
    input_dict["CCTV"] = cctv
    input_dict["Intercom"] = intercom
    
    # Safe fallback (if column exists in model)
    if "Maintenance_Cost" in input_dict:
     input_dict["Maintenance_Cost"] = maintenance_cost

    # ================================
    # CITY HANDLING
    # ================================
    city_col = f"City_{city}"
    if city_col in input_dict:
        input_dict[city_col] = 1
    else:
     print("⚠ Unknown city:", city)

    # ================================
    # PREDICTION
    # ================================
    input_data = [[input_dict[col] for col in feature_columns]]

    ml_price = int(best_model.predict(input_data)[0])

    if ml_price < 500000:
        ml_price = 500000

    # ================================
    # AMENITY BONUS
    # ================================
    amenity_bonus = (
        parking * 150000 +
        gym * 200000 +
        pool * 350000 +
        lift * 100000 +
        security * 120000
    )

    final_price = ml_price + amenity_bonus

    breakdown = {
        "ml_price": ml_price,
        "amenity_bonus": amenity_bonus,
        "final_price": final_price,
        "model_used": best_name
    }

    return final_price, breakdown