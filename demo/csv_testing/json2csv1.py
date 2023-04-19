import json
import csv

# Load JSON data
with open('data.json', 'r') as json_file:
    data = json.load(json_file)

# Open CSV file for writing
with open('data.csv', 'w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)

    # If the data is a list of dictionaries, write headers and rows
    if isinstance(data, list) and all(isinstance(item, dict) for item in data):
        # Write headers
        csv_writer.writerow(data[0].keys())

        # Write data rows
        for item in data:
            csv_writer.writerow(item.values())
    else:
        print("Unsupported JSON structure for CSV conversion.")
