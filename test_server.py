import urllib.request
import json
import time
import subprocess
import sys

proc = subprocess.Popen([sys.executable, r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\server.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(2)

try:
    req = urllib.request.Request('http://127.0.0.1:5000/api/status')
    with urllib.request.urlopen(req) as resp:
        status_data = json.loads(resp.read().decode('utf-8'))
        print('Status API Response:', status_data)

    payload = json.dumps({
        'channel_id': '1516697578107043850',
        'limit': 1000,
        'confession': 'Okay so I gotta say this yo\nRADIANT gotta be one of the biggest pick me 🫩\nBro js acts and simps around girls of the server and it is lowkey blatant icl 😭✌️'
    }).encode('utf-8')

    req = urllib.request.Request('http://127.0.0.1:5000/api/predict', data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as resp:
        predict_data = json.loads(resp.read().decode('utf-8'))
        print('Predict API Success:', predict_data.get('success'))
        top = predict_data['data']['top_rankings'][0]
        print(f"Top suspect: {top['display_name']} (@{top['username']}) - Confidence: {top['confidence_pct']}%")
        print(f"Marker breakdown: {top['marker_scores']}")
finally:
    proc.terminate()

