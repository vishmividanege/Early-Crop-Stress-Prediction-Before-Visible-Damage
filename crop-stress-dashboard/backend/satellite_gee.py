import ee
import datetime

# Initialize EE once
# IMPORTANT: Modern Earth Engine requires a Google Cloud Project ID.
# If you get a 'no project found' error, replace None with your project string: 'your-project-id'
GEE_PROJECT = 'just-student-485912-k1'

try:
    if GEE_PROJECT:
        ee.Initialize(project=GEE_PROJECT)
    else:
        ee.Initialize()
except Exception as e:
    print(f"GEE Initialization failed: {e}")
    print("Please ensure you have a Cloud Project. See: https://developers.google.com/earth-engine/guides/projects")

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

def fetch_patch_as_array(boundary_geojson: dict, size: int = 224) -> dict:
    """
    Fetches a 6-channel image patch (R, G, B, NDVI, VV, VH) centered on the polygon.
    Returns a numpy-ready array (or URL to download it).
    """
    poly = _geojson_to_polygon(boundary_geojson)
    center = poly.centroid(10)
    
    end = datetime.date.today()
    start = end - datetime.timedelta(days=180) # Much larger window for tropical cloud-free imagery

    # S2 RGB + NDVI
    s2_col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
          .filterBounds(center)
          .filterDate(str(start), str(end))
          .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30)))
    
    if s2_col.size().getInfo() == 0:
        # Fallback to allow more clouds
        s2_col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
              .filterBounds(center)
              .filterDate(str(start), str(end))
              .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 80)))

    if s2_col.size().getInfo() == 0:
        return {"status": "error", "message": "No Sentinel-2 imagery found in this area/time."}

    s2 = s2_col.median()
    rgb = s2.select(["B4", "B3", "B2"])
    ndvi = s2.normalizedDifference(["B8", "B4"]).rename("NDVI")
    
    # S1 VV/VH
    s1_col = (ee.ImageCollection("COPERNICUS/S1_GRD")
          .filterBounds(center)
          .filterDate(str(start), str(end))
          .filter(ee.Filter.eq("instrumentMode", "IW")))
    
    if s1_col.size().getInfo() == 0:
        return {"status": "error", "message": "No Sentinel-1 (Radar) data found."}

    s1 = s1_col.median().select(["VV", "VH"])
    
    # Combined 6-channel image
    combined = ee.Image.cat([rgb, ndvi, s1])
    
    # Get a fixed-size patch (roughly)
    # Note: getRegion or sampleRectangle are usually used, but for API simplicity 
    # we use getThumbURL or similar if it was a small PNG. 
    # For raw data, we'll use computePixels or sampleRectangle.
    
    # radius=112 gives 225 pixels. We want at least 224. 
    # The preprocessor in predictor.py will crop it to exactly 224.
    patch = combined.neighborhoodToArray(ee.Kernel.square(radius=112, units='pixels'))
    
    try:
        data = patch.sample(center, 10).first().toDictionary().getInfo()
        # This returns a dict of arrays. We need to reconstruct the HxWx6 block.
        # However, GEE's python API usually handles 'getInfo' on small arrays well.
        return {
            "patch_data": data,
            "channels": ["R", "G", "B", "NDVI", "VV", "VH"],
            "status": "success"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
