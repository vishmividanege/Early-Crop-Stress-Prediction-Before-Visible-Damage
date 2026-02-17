import React, { useState } from "react";
import { MapContainer, TileLayer, FeatureGroup } from "react-leaflet";
import { EditControl } from "react-leaflet-draw";
import "leaflet/dist/leaflet.css";
import "leaflet-draw/dist/leaflet.draw.css";

export default function App() {
  const [boundary, setBoundary] = useState(null);
  const [crop, setCrop] = useState("Rice");
  const [plantingDate, setPlantingDate] = useState("");
  const [result, setResult] = useState(null);

  // When polygon is created
  const onCreated = (e) => {
    const geojson = e.layer.toGeoJSON();
    setBoundary(geojson);
  };

  // Call backend API
  const analyze = async () => {
    if (!boundary) {
      alert("Please draw your field boundary first!");
      return;
    }

    const res = await fetch("http://localhost:8000/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ boundary, crop, plantingDate }),
    });

    const data = await res.json();
    setResult(data);
  };

  return (
    <div style={{ maxWidth: 1000, margin: "20px auto", padding: 16 }}>
      <h2>Early Crop Stress Prediction</h2>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <input
          value={crop}
          onChange={(e) => setCrop(e.target.value)}
          placeholder="Crop type (e.g., Rice)"
          style={{ padding: 10 }}
        />
        <input
          value={plantingDate}
          onChange={(e) => setPlantingDate(e.target.value)}
          placeholder="Planting date (optional)"
          style={{ padding: 10 }}
        />
      </div>

      <p style={{ marginTop: 12 }}>
        <b>Draw your field boundary:</b> Click around your field and finish the polygon.
      </p>

      <div style={{ height: 420, borderRadius: 12, overflow: "hidden", border: "1px solid #ddd" }}>
        <MapContainer center={[7.8731, 80.7718]} zoom={8} style={{ height: "100%" }}>
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution="&copy; OpenStreetMap contributors"
          />

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

      <button
        onClick={analyze}
        style={{ marginTop: 12, padding: "10px 14px", cursor: "pointer" }}
      >
        Analyze Field
      </button>

      {/* Show boundary debug */}
      {boundary && (
        <div style={{ marginTop: 10, fontSize: 12, color: "#555" }}>
          ✅ Field boundary captured!
        </div>
      )}

      {/* Show result */}
      {result && (
        <div style={{ marginTop: 16, padding: 16, border: "1px solid #ddd", borderRadius: 12 }}>
          <h3>Result</h3>
          <p><b>Risk Level:</b> {result.risk_level}</p>
          <p><b>Confidence:</b> {(result.confidence * 100).toFixed(0)}%</p>

          <h4>Recommended Actions</h4>
          <ul>
            {result.recommended_actions.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
