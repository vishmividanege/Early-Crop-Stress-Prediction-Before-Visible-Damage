import React, { useState } from "react";
import { MapContainer, TileLayer, FeatureGroup, LayersControl } from "react-leaflet";
import { EditControl } from "react-leaflet-draw";
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, ReferenceLine, Label, LineChart, Line, Legend } from 'recharts';
import "leaflet/dist/leaflet.css";
import "leaflet-draw/dist/leaflet.draw.css";

// --- CONFIGURATION ---
const OWM_API_KEY = import.meta.env.VITE_OWM_API_KEY; // Replace with your key for tile layers

export default function App() {
  const [boundary, setBoundary] = useState(null);
  const [crop, setCrop] = useState("Rice");
  const [plantingDate, setPlantingDate] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [locationName, setLocationName] = useState("");

  // When polygon is created
  const onCreated = async (e) => {
    const geojson = e.layer.toGeoJSON();
    setBoundary(geojson);

    // Get centroid for reverse geocoding
    const coords = geojson.geometry.coordinates[0];
    const lat = coords.reduce((sum, p) => sum + p[1], 0) / coords.length;
    const lon = coords.reduce((sum, p) => sum + p[0], 0) / coords.length;

    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`);
      const data = await res.json();
      if (data.display_name) {
        const parts = data.display_name.split(", ");
        // Pick village/city and country for a cleaner name
        const name = parts.length > 3 ? `${parts[0]}, ${parts[parts.length - 1]}` : data.display_name;
        setLocationName(name);
      }
    } catch (err) {
      console.error("Geocoding failed", err);
    }
  };

  // Call backend API
  const analyze = async () => {
    if (!boundary) {
      alert("Please draw your field boundary first!");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ boundary, crop, plantingDate }),
      });

      const data = await res.json();
      setResult(data);
    } catch (err) {
      alert("Analysis failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <header className="header">
        <h1>Early Crop Stress Predictor</h1>
        <p style={{ color: "var(--text-muted)", marginTop: 8 }}>
          Satellite-powered intelligence for early intervention
        </p>
      </header>

      <div className="grid">
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Field Configuration</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div className="input-group">
              <label>Crop Type</label>
              <select
                value={crop}
                onChange={(e) => setCrop(e.target.value)}
                className="select-input"
              >
                <option value="General">General/Mixed</option>
                <option value="Rice">Rice (Paddy)</option>
                <option value="Vegetables">Vegetables</option>
                <option value="Tea">Tea Estates</option>
                <option value="Maize">Maize</option>
              </select>
            </div>
            <div className="input-group">
              <label>Planting Date</label>
              <input
                type="date"
                value={plantingDate}
                onChange={(e) => setPlantingDate(e.target.value)}
              />
            </div>
            <button className="btn" onClick={analyze} disabled={loading || !boundary}>
              {loading ? "Analyzing Satellite Data..." : "🚀 Analyze Field"}
            </button>
            {boundary && (
              <div className="location-badge">
                📍 {locationName || "Boundary captured"}
              </div>
            )}
          </div>
        </div>

        <div className="card" style={{ padding: 0, position: "relative" }}>
          <div className="map-container">
            <MapContainer center={[7.8731, 80.7718]} zoom={8} style={{ height: "100%" }}>
              <LayersControl position="topright">
                <LayersControl.BaseLayer checked name="OpenStreetMap">
                  <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution="&copy; OpenStreetMap"
                  />
                </LayersControl.BaseLayer>

                {OWM_API_KEY && OWM_API_KEY !== "YOUR_OWM_API_KEY_HERE" && (
                  <>
                    <LayersControl.Overlay name="Rainfall (OWM)">
                      <TileLayer
                        url={`https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png?appid=${OWM_API_KEY}`}
                      />
                    </LayersControl.Overlay>
                    <LayersControl.Overlay name="Clouds (OWM)">
                      <TileLayer
                        url={`https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png?appid=${OWM_API_KEY}`}
                      />
                    </LayersControl.Overlay>
                  </>
                )}
              </LayersControl>

              <FeatureGroup>
                <EditControl
                  position="topright"
                  onCreated={onCreated}
                  draw={{
                    polygon: true,
                    rectangle: false,
                    circle: false,
                    circlemarker: false,
                    marker: false,
                    polyline: false,
                  }}
                />
              </FeatureGroup>
            </MapContainer>
          </div>
          <div style={{ padding: "8px 16px", fontSize: "0.75rem", color: "var(--text-muted)" }}>
            * Draw field boundary to begin
          </div>
        </div>
      </div>

      {result && (
        <div className="grid">
          <div className="card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
              <h3 style={{ marginTop: 0 }}>Stress Diagnosis</h3>
              <div className="ai-badge">AI Driven</div>
            </div>
            <div style={{ fontSize: "1.5rem", fontWeight: "bold" }} className={`risk-${result.risk_level.toLowerCase()}`}>
              {result.risk_level} Stress Detected
            </div>
            <p style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>
              Confidence Score: {(result.confidence * 100).toFixed(0)}%
            </p>

            {result.ai_metadata?.anomalies_detected?.length > 0 && (
              <div className="anomaly-box">
                <div style={{ fontWeight: "600", fontSize: "0.75rem", color: "#ef4444", marginBottom: 4 }}>
                  SPECTRAL ANOMALIES DETECTED:
                </div>
                {result.ai_metadata.anomalies_detected.map((an, i) => (
                  <span key={i} className="anomaly-tag">{an.replace(/_/g, " ")}</span>
                ))}
              </div>
            )}

            <div className="trend-section">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <h4 style={{ margin: 0 }}>7-Day Health Trend</h4>
                <div className={`trend-badge ${result.trend_status.toLowerCase()}`}>
                  {result.trend_status === "Improving" ? "📈" : result.trend_status === "Increasing" ? "📉" : "➡️"} {result.trend_status}
                </div>
              </div>

              <div style={{ height: 200, width: '100%', marginTop: 20 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={result.trend_data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorHealth" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.1} />
                        <stop offset="95%" stopColor="var(--primary)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={true} vertical={true} />
                    <XAxis
                      dataKey="day"
                      stroke="var(--text-muted)"
                      fontSize={11}
                      tickLine={true}
                      axisLine={true}
                    />
                    <YAxis
                      domain={[0, 1.2]}
                      stroke="var(--text-muted)"
                      fontSize={11}
                      tickCount={6}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: '8px' }}
                      itemStyle={{ color: 'var(--primary)' }}
                    />
                    <Legend verticalAlign="top" height={36} />

                    <ReferenceLine
                      y={result.health_average}
                      label={{ position: 'right', value: 'Avg', fill: '#f59e0b', fontSize: 10, fontWeight: 700 }}
                      stroke="#f59e0b"
                      strokeDasharray="3 3"
                      name="7-Day Average"
                    />

                    <Area
                      name="Health Index"
                      type="linear"
                      dataKey="score"
                      stroke="var(--primary)"
                      fillOpacity={1}
                      fill="url(#colorHealth)"
                      strokeWidth={2}
                      dot={{ r: 4, fill: 'var(--primary)', strokeWidth: 2, stroke: 'var(--card-bg)' }}
                      activeDot={{ r: 6, fill: 'var(--primary)' }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 8, textAlign: "center" }}>
                * Score 1.0 = Peak Vegetation Health
              </p>
            </div>

            <h4 style={{ marginBottom: 8, marginTop: 24 }}>Recommended Actions</h4>
            <div className="action-list">
              {result.recommended_actions.map((a, i) => (
                <div key={i} className="action-item">
                  <span style={{ color: "var(--primary)" }}>{a.startsWith("AI Analysis") ? "✨" : "✓"}</span>
                  <span style={{ fontWeight: a.startsWith("AI Analysis") ? "600" : "400" }}>{a}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h3 style={{ marginTop: 0 }}>Local Environment</h3>
            {result.weather ? (
              <>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <img
                    src={`https://openweathermap.org/img/wn/${result.weather.icon}@2x.png`}
                    alt="weather"
                    style={{ width: 48, height: 48 }}
                  />
                  <div style={{ fontSize: "1.25rem", fontWeight: "600", textTransform: "capitalize" }}>
                    {result.weather.description}
                  </div>
                </div>
                <div className="weather-grid">
                  <div className="weather-item">
                    <div>
                      <div className="weather-label">Temp</div>
                      <div className="weather-val">{result.weather.temp}°C</div>
                    </div>
                  </div>
                  <div className="weather-item">
                    <div>
                      <div className="weather-label">Humidity</div>
                      <div className="weather-val">{result.weather.humidity}%</div>
                    </div>
                  </div>
                  <div className="weather-item">
                    <div>
                      <div className="weather-label">Wind</div>
                      <div className="weather-val">{result.weather.wind_speed} m/s</div>
                    </div>
                  </div>
                  <div className="weather-item">
                    <div>
                      <div className="weather-label">NDVI (Mean)</div>
                      <div className="weather-val">Detected</div>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <p style={{ color: "var(--text-muted)" }}>
                Weather data unavailable. Please check API key.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
