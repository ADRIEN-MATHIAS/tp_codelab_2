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
