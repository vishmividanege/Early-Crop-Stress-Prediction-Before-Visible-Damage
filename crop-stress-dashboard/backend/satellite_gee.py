import ee
import datetime

# Initialize EE once
try:
    ee.Initialize()
except Exception:
    ee.Authenticate()
    ee.Initialize()

def _geojson_to_polygon(boundary_geojson: dict) -> ee.Geometry:
    # Leaflet sends a GeoJSON Feature with geometry
    geom = boundary_geojson.get("geometry", boundary_geojson)
    if geom.get("type") != "Polygon":
        raise ValueError("Only Polygon supported")
    return ee.Geometry.Polygon(geom["coordinates"])

def fetch_features(boundary_geojson: dict, days: int = 30) -> dict:
    poly = _geojson_to_polygon(boundary_geojson)

    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)

    # Sentinel-2 NDVI (cloud filtered)
    s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
          .filterBounds(poly)
          .filterDate(str(start), str(end))
          .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30)))

    if s2.size().getInfo() == 0:
        # fallback: more clouds if needed
        s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
              .filterBounds(poly)
              .filterDate(str(start), str(end))
              .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 70)))

    s2_img = s2.median()
    ndvi = s2_img.normalizedDifference(["B8", "B4"]).rename("NDVI")

    ndvi_mean = ndvi.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=poly,
        scale=10,
        maxPixels=1e9
    ).get("NDVI").getInfo()

    # Sentinel-1 VV/VH
    s1 = (ee.ImageCollection("COPERNICUS/S1_GRD")
          .filterBounds(poly)
          .filterDate(str(start), str(end))
          .filter(ee.Filter.eq("instrumentMode", "IW"))
          .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
          .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
          .select(["VV", "VH"]))

    if s1.size().getInfo() == 0:
        raise RuntimeError("No Sentinel-1 images found for this field/time window")

    s1_img = s1.median()

    sar = s1_img.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=poly,
        scale=10,
        maxPixels=1e9
    ).getInfo()

    return {
        "ndvi_mean": ndvi_mean,
        "vv_mean": sar.get("VV"),
        "vh_mean": sar.get("VH"),
        "days": days
    }
