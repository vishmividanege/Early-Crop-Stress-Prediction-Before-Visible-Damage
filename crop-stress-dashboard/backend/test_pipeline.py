import sys
import os

# Add the current directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from satellite_gee import fetch_patch_as_array
    from predictor import predictor, prob_to_risk
    import torch
    import numpy as np
    print("Success: Imports successful.")
except ImportError as e:
    print(f"Error: Import failed: {e}")
    sys.exit(1)

def test_full_pipeline():
    # Test cases: [Name, CenterCoords]
    test_cases = [
        ["Lush Rice Field (Sri Lanka) - EXPECT HEALTHY", [80.7718, 7.8731]],
        ["Amazon Rainforest (Brazil) - EXPECT HEALTHY", [-60.0, -3.0]],
        ["Vineyards (France) - EXPECT HEALTHY", [4.5, 47.0]],
        ["Sahara Desert (Egypt) - EXPECT STRESSED", [30.0, 25.0]],
        ["Death Valley (USA) - EXPECT STRESSED", [-116.8, 36.4]],
        ["Australian Outback - EXPECT STRESSED", [130.0, -25.0]]
    ]

    summary = []

    for name, coords in test_cases:
        print(f"\n{'='*20}")
        print(f"Testing: {name}")
        print(f"{'='*20}")
        
        sample_boundary = {
            "type": "Polygon",
            "coordinates": [[
                [coords[0], coords[1]],
                [coords[0]+0.001, coords[1]],
                [coords[0]+0.001, coords[1]+0.001],
                [coords[0], coords[1]+0.001],
                [coords[0], coords[1]]
            ]]
        }

        print("1. Fetching imagery from GEE...")
        res = fetch_patch_as_array(sample_boundary)
        
        if res.get("status") == "error":
            print(f"Error: GEE Fetch Failed: {res.get('message')}")
            summary.append([name, "FETCH ERROR", 0.0])
            continue

        print("Success: GEE Fetch Success.")
        
        print("2. Running ML Inference...")
        try:
            x = predictor.preprocess(res["patch_data"])
            stress_prob = predictor.predict_stress_prob(x)
            risk = prob_to_risk(stress_prob)
            print(f"Success: Inference Success.")
            print(f"--- Results ---")
            print(f"Risk Level: {risk}")
            print(f"Stress Probability: {stress_prob:.6f}")
            print(f"----------------")
            summary.append([name, risk, stress_prob])
        except Exception as e:
            print(f"Error: Inference Failed: {e}")
            summary.append([name, "INFERENCE ERROR", 0.0])

    print("\n\n" + "="*50)
    print("FINAL SUMMARY REPORT")
    print("="*50)
    print(f"{'Location':<45} | {'Risk':<10} | {'Prob':<8}")
    print("-" * 70)
    for name, risk, prob in summary:
        short_name = name.split(" - ")[0]
        suffix = " (Match)" if (("EXPECT HEALTHY" in name and risk=="Healthy") or ("EXPECT STRESSED" in name and risk=="High")) else " (MISMATCH)"
        print(f"{short_name:<45} | {risk:<10} | {prob:.4f}{suffix}")
    print("="*50)

if __name__ == "__main__":
    test_full_pipeline()

if __name__ == "__main__":
    test_full_pipeline()
