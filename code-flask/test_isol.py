import sqlite3
import os

# Reset database - use absolute path
BASE = r'C:\Users\adrip\OneDrive\Documents\GitHub\tp_codelab_2\code-flask\data.db'
conn = sqlite3.connect(BASE)
conn.execute('PRAGMA foreign_keys = ON')
conn.execute('DELETE FROM reservations')
conn.execute("INSERT INTO reservations (id, salle_id, personne, date, debut, fin, participants) VALUES (1, 1, 'Alice', '2026-11-09', '10:00', '12:00', 12)")
conn.commit()
conn.close()

from app import app
with app.test_client() as client:
    # Test plage
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
    print('Homepage has capacite:', b'capacite' in resp2.data)
    print('Homepage has duree:', b'duree' in resp2.data)