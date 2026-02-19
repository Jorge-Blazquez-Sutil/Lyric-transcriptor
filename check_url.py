import requests

url = "https://audiomack.com/attack_gaye/song/1-attack-sateh-tiyo-ft-asidik"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

try:
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        html = response.text
        
        # Extract __NEXT_DATA__
        import re
        import json
        
        # Look for script tag with id "__NEXT_DATA__"
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
        if match:
            json_str = match.group(1)
            data = json.loads(json_str)
            
            with open("audiomack_data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print("Extracted __NEXT_DATA__ to audiomack_data.json")
        else:
            print("__NEXT_DATA__ not found via regex")
            
    else:
        print("Page detection failed.")
except Exception as e:
    print(f"Error: {e}")
