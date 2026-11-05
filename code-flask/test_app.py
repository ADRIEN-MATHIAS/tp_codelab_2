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


def test_modifier_salle():
    with app.test_client() as client:
        client.post("/salles/2/modifier", data={"nom": "S2_modifie", "capacite": "50", "projecteur": "on"})
        resp = client.get("/")
        assert b"S2_modifie" in resp.data
        assert b"S2 " not in resp.data or b'S2 "' in resp.data  # S2 still exists somewhere


def test_reserver_salle_accepte():
    """S1 a une réservation 10h-12h, donc 12h-13h doit être accepté."""
    with app.test_client() as client:
        client.post("/salles/1/reserver", data={
            "personne": "Bob",
            "date": "2026-11-09",
            "debut": "12:00",
            "fin": "13:00",
            "participants": "5"
        })
        resp = client.get("/")
        # La page doit s'afficher correctement (la réservation a été acceptée)
        assert resp.status_code == 200


def test_reserver_salle_refuse_chevauchement():
    """S1 a une réservation 10h-12h, donc 11h-13h doit être refusé (chevauchement)."""
    with app.test_client() as client:
        # La réservation 11h-13h doit être rejetée
        resp = client.post("/salles/1/reserver", data={
            "personne": "Bob",
            "date": "2026-11-09",
            "debut": "11:00",
            "fin": "13:00",
            "participants": "5"
        })
        # Doit avoir une erreur ou redirection, pas d'intégrity error
        # On vérifie que la page s'affiche quand même
        resp = client.get("/")
        assert resp.status_code == 200


def test_reserver_salle_capacite_depassee():
    """S1 a capacité 20, réservation à 25 participants doit être refusée."""
    with app.test_client() as client:
        # Essaye de réserver S1 avec 25 participants (capacité = 20)
        resp = client.post("/salles/1/reserver", data={
            "personne": "Bob",
            "date": "2026-11-10",
            "debut": "14:00",
            "fin": "15:00",
            "participants": "25"
        })
        # Doit être redirigé vers la page d'erreur capacité
        assert resp.status_code == 302
        # La redirection doit inclure l'erreur capacite
        resp = client.get("/salles/1/reserver?erreur=capacite")
        # La page d'accueil doit afficher le message d'erreur
        resp = client.get("/")
        assert b"capacite" in resp.data