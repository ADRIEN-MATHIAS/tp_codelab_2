from app import app
from base import ouvrir_base


def test_accueil():
    assert app.test_client().get("/").status_code == 200


def test_ajouter_salle():
    client = app.test_client()
    response = client.post("/salles", data={"nom": "S3", "capacite": 15, "projecteur": "1"})
    assert response.status_code == 302
    with ouvrir_base() as conn:
        salle = conn.execute("SELECT * FROM salles WHERE nom = ?", ["S3"]).fetchone()
        assert salle is not None
        assert salle["capacite"] == 15
        assert salle["projecteur"] == 1


def test_supprimer_salle():
    client = app.test_client()
    with ouvrir_base() as conn:
        conn.execute("INSERT INTO salles (nom, capacite, projecteur) VALUES (?, ?, ?)", ["S4", 10, 0])
        conn.execute("INSERT INTO reservations (salle_id, personne, date, debut, fin, participants) VALUES (?, ?, ?, ?, ?, ?)", 
                      [conn.execute("SELECT id FROM salles WHERE nom = ?", ["S4"]).fetchone()["id"], "Bob", "2026-11-09", "14:00", "16:00", 5])
    response = client.post("/salles/supprimer", data={"id": conn.execute("SELECT id FROM salles WHERE nom = ?", ["S4"]).fetchone()["id"]})
    assert response.status_code == 302
    with ouvrir_base() as conn:
        salle = conn.execute("SELECT * FROM salles WHERE nom = ?", ["S4"]).fetchone()
        assert salle is None
        reservation = conn.execute("SELECT * FROM reservations WHERE personne = ?", ["Bob"]).fetchone()
        assert reservation is None


def test_modifier_salle():
    client = app.test_client()
    with ouvrir_base() as conn:
        conn.execute("INSERT INTO salles (nom, capacite, projecteur) VALUES (?, ?, ?)", ["S5", 10, 0])
    response = client.post("/salles/modifier", data={"id": "1", "nom": "S5-modifie", "capacite": "20", "projecteur": "1"})
    assert response.status_code == 302
    with ouvrir_base() as conn:
        salle = conn.execute("SELECT * FROM salles WHERE id = 1").fetchone()
        assert salle["nom"] == "S5-modifie"
        assert salle["capacite"] == 20
        assert salle["projecteur"] == 1
