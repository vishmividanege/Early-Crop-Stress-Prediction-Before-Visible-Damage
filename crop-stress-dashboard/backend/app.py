from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import datetime
import ee




import requests
import json
import os
from predictor import predictor, prob_to_risk

# --- CONFIGURATION ---
PROJECT_ID = "just-student-485912-k1"
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")

try:
    ee.Initialize(project=PROJECT_ID)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def geojson_to_ee_polygon(boundary_geojson: dict) -> ee.Geometry:
    geom = boundary_geojson["geometry"] if "geometry" in boundary_geojson else boundary_geojson
    if geom.get("type") != "Polygon":
        raise ValueError("Only Polygon is supported")
    return ee.Geometry.Polygon(geom["coordinates"])

def get_centroid(boundary_geojson: dict):
    """Calculate the centroid of a GeoJSON polygon."""
    geom = boundary_geojson["geometry"] if "geometry" in boundary_geojson else boundary_geojson
    coords = geom["coordinates"][0]
    lat = sum(p[1] for p in coords) / len(coords)
    lon = sum(p[0] for p in coords) / len(coords)
    return lat, lon

def fetch_weather(lat, lon):
    """Fetch current weather from OpenWeatherMap."""
    if OPENWEATHERMAP_API_KEY == "YOUR_OWM_API_KEY_HERE":
        return None
    
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return {
                "temp": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "description": data["weather"][0]["description"],
                "wind_speed": data["wind"]["speed"],
                "icon": data["weather"][0]["icon"]
            }
    except Exception as e:
        print(f"Weather fetch failed: {e}")
    return None

def fetch_satellite_features(boundary_geojson: dict, days: int = 30):
    poly = geojson_to_ee_polygon(boundary_geojson)
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)

    # ---------- Sentinel-2 NDVI ----------
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(poly)
        .filterDate(str(start), str(end))
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
    )

    if s2.size().getInfo() == 0:
        s2 = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(poly)
            .filterDate(str(start), str(end))
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))
        )

    s2_med = s2.median()
    ndvi = s2_med.normalizedDifference(["B8", "B4"]).rename("NDVI")

    ndvi_info = ndvi.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=poly,
        scale=10,
        maxPixels=1e9
    ).get("NDVI").getInfo()

    # ---------- Sentinel-1 VV/VH ----------
    s1 = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(poly)
        .filterDate(str(start), str(end))
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .select(["VV", "VH"])
    )

    if s1.size().getInfo() == 0:
        return {
            "ndvi_mean": ndvi_info,
            "vv_mean": -12, # dummy fallback
            "vh_mean": -18,
            "time_window_days": days
        }

    s1_med = s1.median()
    sar_stats = s1_med.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=poly,
        scale=10,
        maxPixels=1e9
    ).getInfo()

    return {
        "ndvi_mean": ndvi_info,
        "vv_mean": sar_stats.get("VV"),
        "vh_mean": sar_stats.get("VH"),
        "time_window_days": days
    }

@app.post("/predict")
def predict(payload: dict):
    boundary = payload.get("boundary")
    crop_type = payload.get("crop_type", "general")
    if not boundary:
        raise HTTPException(status_code=400, detail="Missing 'boundary'")

    lat, lon = get_centroid(boundary)
    weather = fetch_weather(lat, lon)

    try:
        # 1. Fetch Daily Data for the last 7 days (Batched)
        from satellite_gee import fetch_daily_timeseries
        batch_res = fetch_daily_timeseries(boundary, days=7)
        
        if batch_res.get("status") == "error":
            raise Exception(f"Satellite batch fetch failed: {batch_res.get('message')}")
            
        data = batch_res["data"]
        trend_data = []
        last_patch = None
        
        # d0=Today, d1=Yesterday...
        for i in range(7, -1, -1):
            target_date = (datetime.date.today() - datetime.timedelta(days=i))
            
            # Reconstruct the patch dictionary for this day
            day_patch = {
                "B2": data.get(f"d{i}_B"),
                "B3": data.get(f"d{i}_G"),
                "B4": data.get(f"d{i}_R"),
                "NDVI": data.get(f"d{i}_NDVI"),
                "VV": data.get(f"d{i}_VV"),
                "VH": data.get(f"d{i}_VH")
            }
            
            # Run inference
            if day_patch["B2"] is not None:
                x_day = predictor.preprocess(day_patch)
                prob = predictor.predict_stress_prob(x_day)
                health_score = round(1 - prob, 2)
                if i == 0:
                    last_patch = day_patch
            else:
                health_score = 0.5
            
            trend_data.append({
                "day": target_date.strftime("%b %d"),
                "score": health_score
            })

        if last_patch is None:
            raise Exception("No valid satellite data found for Today.")

        # Today's specific data
        stress_prob = 1 - trend_data[-1]["score"]
        
        # Risk Determination
        risk = prob_to_risk(stress_prob)
        
        # Trend Analysis
        avg_health = round(sum([d["score"] for d in trend_data]) / len(trend_data), 2)
        diff = trend_data[-1]["score"] - trend_data[0]["score"]
        if diff > 0.05: trend_status = "Improving"
        elif diff < -0.05: trend_status = "Increasing"
        else: trend_status = "Stable"

        # AI Recommendation Engine
        anomalies = predictor.get_anomalies(last_patch)
        actions = predictor.get_ai_recommendations(risk, anomalies, crop_type=crop_type)

        # Add trend specific recommendation
        if trend_status == "Increasing":
            actions.append("AI Analysis: Stress is trending UPward compared to last week. Immediate inspection required.")
        elif trend_status == "Improving":
            actions.append("AI Analysis: Health is IMPROVING. Previous interventions seem effective.")

        return {
            "risk_level": risk,
            "confidence": round(stress_prob if stress_prob > 0.5 else 1 - stress_prob, 2),
            "recommended_actions": actions,
            "location": {"lat": lat, "lon": lon},
            "weather": weather,
            "trend_data": trend_data,
            "trend_status": trend_status,
            "health_average": avg_health,
            "ai_metadata": {
                "anomalies_detected": anomalies,
                "crop_type": crop_type
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")
