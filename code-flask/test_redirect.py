from app import app
with app.test_client() as client:
    # Test with 7h30-9h (before 8h)
    resp = client.post('/salles/1/reserver', data={
        'personne': 'Bob',
        'date': '2026-11-10',
        'debut': '07:30',
        'fin': '09:00',
        'participants': '5'
    })
    print('Status:', resp.status_code)
    print('Location:', resp.location)
    resp2 = client.get('/')
    print('Homepage has plage:', b'plage' in resp2.data)
    print('Homepage has duree:', b'duree' in resp2.data)
    print('Homepage has capacite:', b'capacite' in resp2.data)