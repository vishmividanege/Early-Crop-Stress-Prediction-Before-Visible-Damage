import sys
import os
import torch
import numpy as np

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from satellite_gee import fetch_patch_as_array
from predictor import predictor, prob_to_risk

def run_sl_test():
    # Coordinates for Sri Lanka
    test_cases = [
        ["Anuradhapura (Dry Zone - Paddy)", [80.4131, 8.3122]],
        ["Polonnaruwa (Dry Zone - Paddy)", [81.0188, 7.9403]],
        ["Nuwara Eliya (Tea Estates - Wet Zone)", [80.7891, 6.9497]],
        ["Jaffna (Arid Zone - Cultivation)", [80.0255, 9.6615]],
        ["Hambantota (Dry Zone - Arid)", [81.1246, 6.1246]],
        ["Ratnapura (Wet Zone - Rubber/Tea)", [80.3847, 6.6828]]
    ]

    print(f"{'SL Location':<40} | {'Risk':<10} | {'Prob':<8}")
    print("-" * 65)

    for name, coords in test_cases:
        boundary = {
            "type": "Polygon",
            "coordinates": [[
                [coords[0], coords[1]],
                [coords[0]+0.001, coords[1]],
                [coords[0]+0.001, coords[1]+0.001],
                [coords[0], coords[1]+0.001],
                [coords[0], coords[1]]
            ]]
        }
        res = fetch_patch_as_array(boundary)
        if res.get("status") == "success":
            x = predictor.preprocess(res["patch_data"])
            p = predictor.predict_stress_prob(x)
            r = prob_to_risk(p)
            print(f"{name:<40} | {r:<10} | {p:.4f}")
        else:
            print(f"{name:<40} | ERROR      | 0.0000")

if __name__ == "__main__":
    run_sl_test()
