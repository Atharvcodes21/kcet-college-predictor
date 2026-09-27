import requests, json

payload = {
    'rank': 5000,
    'category': 'GM',
    'courses': ['COMPUTER SCIENCE AND ENGINEERING'],
    'is_hk_region': False,
    'is_rural': False,
    'is_kannada': False
}

r = requests.post('http://localhost:8000/predict', json=payload)
data = r.json()
print(f'Total results: {len(data)}')
print()
for d in data[:20]:
    pr = d['priority_rank']
    tier = d.get('tier', '')[:40]
    college = d['college'][:50]
    cutoff = d['cutoff']
    status = 'YES' if d['can_get'] else 'NO'
    print(f"  #{pr:3d} | {tier:40s} | {college:50s} | cutoff={cutoff:6d} | {status}")
