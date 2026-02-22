import sys
import os
import torch
import numpy as np

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from satellite_gee import fetch_patch_as_array
from predictor import predictor, prob_to_risk

def run_silent_test():
    test_cases = [
        ["Lush Rice Field (Sri Lanka) - EXPECT HEALTHY", [80.7718, 7.8731]],
        ["Amazon Rainforest (Brazil) - EXPECT HEALTHY", [-60.0, -3.0]],
        ["Vineyards (France) - EXPECT HEALTHY", [4.5, 47.0]],
        ["Sahara Desert (Egypt) - EXPECT STRESSED", [30.0, 25.0]],
        ["Death Valley (USA) - EXPECT STRESSED", [-116.8, 36.4]],
        ["Australian Outback - EXPECT STRESSED", [130.0, -25.0]]
    ]

    print(f"{'Location':<45} | {'Risk':<10} | {'Prob':<8}")
    print("-" * 70)

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
            short_name = name.split(" - ")[0]
            print(f"{short_name:<45} | {r:<10} | {p:.4f}")
        else:
            print(f"{name:<45} | ERROR      | 0.0000")

if __name__ == "__main__":
    run_silent_test()
