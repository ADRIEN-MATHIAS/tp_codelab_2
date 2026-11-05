import sqlite3
from pathlib import Path

# Réinitialiser la base de données
RACINE = Path('code-flask')
BASE = RACINE / 'data.db'
conn = sqlite3.connect(BASE)
conn.execute('PRAGMA foreign_keys = ON')
conn.execute('DELETE FROM reservations')
conn.execute("INSERT INTO reservations (id, salle_id, personne, date, debut, fin, participants) VALUES (1, 1, 'Alice', '2026-11-09', '10:00', '12:00', 12)")
conn.commit()
conn.close()
print("Base réinitialisée")