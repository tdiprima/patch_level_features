import csv
import json


def convert_json_to_csv(json_file, csv_file):
    """Convert feature results from JSON to CSV format."""
    with open(json_file, 'r') as jf:
        feature_results = json.load(jf)

    # Open the CSV file for writing
    with open(csv_file, 'w', newline='') as cf:
        csv_writer = csv.writer(cf)

        # Write the header row
        csv_writer.writerow(["Tile", "Feature_ID", "Feature_Coordinates"])

        # Write the feature data
        for entry in feature_results:
            tile = entry["tile"]
            for feature in entry["features"]:
                feature_id = feature["id"]
                feature_coords = feature["coordinates"]
                csv_writer.writerow([tile, feature_id, feature_coords])


if __name__ == "__main__":
    json_file = "feature_results.json"  # Input JSON file
    csv_file = "feature_results.csv"  # Output CSV file

    convert_json_to_csv(json_file, csv_file)
    print(f"Converted {json_file} to {csv_file} successfully.")
