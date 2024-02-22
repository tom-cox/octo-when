from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime, timezone

app = Flask(__name__)

# Endpoint to get the cheapest slots
@app.route('/get-cheapest-slots', methods=['GET'])
def get_cheapest_slots():
    num_slots = request.args.get('num_slots', default=8, type=int)  # Get num_slots from query parameters, default to 8
    
    # API URL
    url = 'https://api.octopus.energy/v1/products/AGILE-23-12-06/electricity-tariffs/E-1R-AGILE-23-12-06-A/standard-unit-rates/'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if 'results' in data:
            time_slots = data['results']
            current_utc_time = datetime.now(timezone.utc)
            future_slots = [slot for slot in time_slots if datetime.fromisoformat(slot['valid_from'].rstrip('Z') + '+00:00') > current_utc_time]
            sorted_slots = sorted(future_slots, key=lambda x: x['valid_from'])
            
            # Find the cheapest consecutive slots
            cheapest_sequence, avg_rate = find_cheapest_consecutive_slots(sorted_slots, num_slots)
            
            if cheapest_sequence:
                return jsonify({
                    'start_time': cheapest_sequence[0]['valid_from'],
                    'end_time': cheapest_sequence[-1]['valid_to'],
                    'average_rate': avg_rate,
                    'num_slots': num_slots
                })
            else:
                return jsonify({'error': f"Couldn't find {num_slots} consecutive cheap slots."})
        else:
            return jsonify({'error': 'No data available from the API.'})
    else:
        return jsonify({'error': 'Failed to get data from API.'})

def find_cheapest_consecutive_slots(slots, num_slots):
    min_avg_rate = float('inf')
    cheapest_sequence = None

    for i in range(len(slots) - num_slots + 1):
        current_sequence = slots[i:i+num_slots]
        total_rate = sum(slot['value_inc_vat'] for slot in current_sequence)
        avg_rate = total_rate / num_slots

        if avg_rate < min_avg_rate:
            min_avg_rate = avg_rate
            cheapest_sequence = current_sequence

    return cheapest_sequence, min_avg_rate

if __name__ == '__main__':
    app.run(debug=True)
