from app import app
with app.test_client() as client:
    # D'abord la réservation qui provoque l'erreur plage
    resp = client.post('/salles/1/reserver', data={
        'personne': 'Bob',
        'date': '2026-11-10',
        'debut': '07:30',
        'fin': '09:00',
        'participants': '5'
    })
    print('Redirect status:', resp.status_code)
    print('Redirect location:', resp.location)
    
    # Ensuite la page d'accueil
    resp2 = client.get('/')
    print('Homepage status:', resp2.status_code)
    print('Homepage data length:', len(resp2.data))
    print('Has plage:', b'plage' in resp2.data)
    print('Has capacite:', b'capacite' in resp2.data)
    print('Has duree:', b'duree' in resp2.data)
    # Vérifier le contenu autour de la fin du body
    print('--- Fin de la page ---')
    print(resp2.data[-200:])