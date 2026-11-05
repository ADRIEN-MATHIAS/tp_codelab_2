from app import app


def test_accueil():
    assert app.test_client().get("/").status_code == 200


def test_ajouter_salle():
    with app.test_client() as client:
        client.post("/salles", data={"nom": "S3", "capacite": "30", "projecteur": "on"})
        with app.app_context():
            from base import ouvrir_base
            conn = ouvrir_base()
            salle = conn.execute("SELECT * FROM salles WHERE nom = ?", ["S3"]).fetchone()
            assert salle is not None
            assert salle["capacite"] == 30
            assert salle["projecteur"] == 1


def test_supprimer_salle_cascade():
    with app.test_client() as client:
        client.post("/salles/1/supprimer")
        resp = client.get("/")
        assert b"S1" not in resp.data
        with app.app_context():
            from base import ouvrir_base
            conn = ouvrir_base()
            reservation = conn.execute("SELECT * FROM reservations WHERE salle_id = ?", [1]).fetchone()
            assert reservation is None
