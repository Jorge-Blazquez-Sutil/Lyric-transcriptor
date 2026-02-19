import requests

artist = "attack_gaye"
title = "1-attack-sateh-tiyo-ft-asidik"
# Test URLs
urls = [
    f"https://api.audiomack.com/v1/music/song/{artist}/{title}",
    f"https://api.audiomack.com/song/{artist}/{title}",
    f"https://api.audiomack.com/audio/{artist}/{title}",
    f"https://audiomack.com/api/music/url/song/{artist}/{title}",
    f"https://audiomack.com/api/music/song/{artist}/{title}"
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*'
}

for url in urls:
    try:
        response = requests.get(url, headers=headers)
        print(f"{url} -> {response.status_code}")
        if response.status_code == 200:
            print("Found API endpoint!")
            print(response.text[:200])
            break
    except Exception as e:
        print(f"{url} -> Error: {e}")
