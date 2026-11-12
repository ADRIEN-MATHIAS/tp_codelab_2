import sqlite3
import pytest
from app import app
from base import BASE, RACINE


@pytest.fixture(autouse=True)
def reinit_db():
    with sqlite3.connect(BASE) as conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("DROP TABLE IF EXISTS reservations")
        conn.execute("DROP TABLE IF EXISTS salles")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript((RACINE / "base.sql").read_text(encoding="utf-8"))


def test_accueil():
    assert app.test_client().get("/").status_code == 200


def test_ajouter_salle():
    with app.test_client() as client:
        client.post("/salles", data={"nom": "S3", "type": "TP", "capacite": "30", "projecteur": "on"})
        with app.app_context():
            from base import ouvrir_base
            conn = ouvrir_base()
            salle = conn.execute("SELECT * FROM salles WHERE nom = ?", ["S3"]).fetchone()
            assert salle is not None
            assert salle["type"] == "TP"
            assert salle["capacite"] == 30
            assert salle["projecteur"] == 1


def test_type_local():
    """B2 : Un local a un type, modifiable et visible."""
    with app.test_client() as client:
        resp = client.get("/")
        assert b"cours" in resp.data
        # Modifier le type de la salle 2
        client.post("/salles/2/modifier", data={"nom": "S2", "type": "laboratoire", "capacite": "8"})
        resp = client.get("/")
        assert b"laboratoire" in resp.data


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
        resp = client.post("/salles/1/reserver", data={
            "personne": "Bob",
            "date": "2026-11-09",
            "debut": "12:00",
            "fin": "13:00",
            "participants": "5"
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Erreur :" not in resp.data


def test_reserver_salle_refuse_chevauchement():
    """S1 a une réservation 10h-12h, donc 11h-13h doit être refusé (chevauchement)."""
    with app.test_client() as client:
        resp = client.post("/salles/1/reserver", data={
            "personne": "Bob",
            "date": "2026-11-09",
            "debut": "11:00",
            "fin": "13:00",
            "participants": "5"
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"chevauchement" in resp.data or b"Une r\xc3\xa9servation existe d\xc3\xa9j\xc3\xa0 \xc3\xa0 cette heure" in resp.data


def test_reserver_salle_capacite_depassee():
    """S1 a capacité 20, réservation à 25 participants doit être refusée."""
    with app.test_client() as client:
        resp = client.post("/salles/1/reserver", data={
            "personne": "Bob",
            "date": "2026-11-10",
            "debut": "14:00",
            "fin": "15:00",
            "participants": "25"
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"d\xc3\xa9passe la capacit\xc3\xa9" in resp.data or b"capacite" in resp.data


def test_reserver_salle_plage_interdite():
    """S1 : réservation 7h30-9h refusée (avant 8h)."""
    with app.test_client() as client:
        resp = client.post("/salles/1/reserver", data={
            "personne": "Bob",
            "date": "2026-11-10",
            "debut": "07:30",
            "fin": "09:00",
            "participants": "5"
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"plage" in resp.data or b"8h00 et 20h00" in resp.data


def test_reserver_salle_duree_trop_courte():
    """S1 : réservation 14h-14h20 refusée (moins de 30 min)."""
    with app.test_client() as client:
        resp = client.post("/salles/1/reserver", data={
            "personne": "Bob",
            "date": "2026-11-10",
            "debut": "14:00",
            "fin": "14:20",
            "participants": "5"
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"duree" in resp.data or b"30 minutes et 4 heures" in resp.data


def test_reserver_salle_duree_trop_longue():
    """S1 : réservation 8h-13h refusée (plus de 4h)."""
    with app.test_client() as client:
        resp = client.post("/salles/1/reserver", data={
            "personne": "Bob",
            "date": "2026-11-10",
            "debut": "08:00",
            "fin": "13:00",
            "participants": "5"
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"duree" in resp.data or b"30 minutes et 4 heures" in resp.data


def test_reserver_salle_refuse_chevauchement_personne():
    """B1 : Une personne ne peut pas avoir deux réservations qui se chevauchent."""
    with app.test_client() as client:
        # Alice a déjà une réservation pour S1 le 2026-11-09 de 10:00 à 12:00.
        # Alice essaie de réserver la salle S2 le même jour de 11:00 à 13:00 -> refusé
        resp = client.post("/salles/2/reserver", data={
            "personne": "Alice",
            "date": "2026-11-09",
            "debut": "11:00",
            "fin": "13:00",
            "participants": "5"
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"chevauchement_personne" in resp.data or b"Cette personne a d\xc3\xa9j\xc3\xa0 une r\xc3\xa9servation" in resp.data

        # Alice réserve la salle S2 de 12:00 à 13:00 (adjacent : autorisé)
        resp_ok = client.post("/salles/2/reserver", data={
            "personne": "Alice",
            "date": "2026-11-09",
            "debut": "12:00",
            "fin": "13:00",
            "participants": "5"
        }, follow_redirects=True)
        assert resp_ok.status_code == 200
        assert b"Erreur :" not in resp_ok.data


def test_planning_route():
    """Vérifier que la route /salles/1/planning répond bien."""
    with app.test_client() as client:
        resp = client.get("/salles/1/planning")
        assert resp.status_code == 200


def test_reserver_salle_repetition_hebdomadaire():
    """B3 : Réserver une salle de manière répétée chaque semaine."""
    with app.test_client() as client:
        # Réserver pour 3 semaines consécutives les mardis 10h-11h
        resp = client.post("/salles/1/reserver", data={
            "personne": "Charlie",
            "date": "2026-11-10",
            "debut": "10:00",
            "fin": "11:00",
            "participants": "4",
            "semaines": "3"
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Erreur :" not in resp.data

        with app.app_context():
            from base import ouvrir_base
            with ouvrir_base() as conn:
                resas = conn.execute(
                    "SELECT date FROM reservations WHERE personne = 'Charlie' ORDER BY date"
                ).fetchall()
                dates = [r["date"] for r in resas]
                assert dates == ["2026-11-10", "2026-11-17", "2026-11-24"]


def test_reserver_salle_repetition_conflit_bloque_tout():
    """B3 : Si une des semaines de répétition a un conflit, la série est refusée."""
    with app.test_client() as client:
        # Alice a déjà une réservation le 2026-11-09 de 10:00 à 12:00 sur S1.
        # Bob essaie de réserver S1 les lundis 11h-12h pour 2 semaines (le premier lundi 2026-11-09 est en conflit)
        resp = client.post("/salles/1/reserver", data={
            "personne": "Bob",
            "date": "2026-11-09",
            "debut": "11:00",
            "fin": "12:00",
            "participants": "4",
            "semaines": "2"
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Une r\xc3\xa9servation existe d\xc3\xa9j\xc3\xa0" in resp.data or b"chevauchement" in resp.data

        with app.app_context():
            from base import ouvrir_base
            with ouvrir_base() as conn:
                resas = conn.execute("SELECT * FROM reservations WHERE personne = 'Bob'").fetchall()
                assert len(resas) == 0
