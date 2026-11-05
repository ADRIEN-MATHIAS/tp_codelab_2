from flask import Flask, redirect, render_template_string, request

from base import ouvrir_base

# Le HTML de la page.
PAGE = """
<style>
  .salles-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    width: 100%;
  }
  @media (min-width: 600px) {
    .salles-grid { grid-template-columns: repeat(4, 1fr); }
  }
  @media (min-width: 1200px) {
    .salles-grid { grid-template-columns: repeat(8, 1fr); }
  }
</style>
<h1>Réservation de salles</h1>

<h2>Salles</h2>
<div class="salles-grid">
  {% for salle in salles %}
    <div style="padding: 8px; background: #f5f5f5; display: flex; align-items: center; justify-content: space-between;">
      <span style="line-height: 24px;">{{ salle["nom"] }}</span>
      <form method="post" action="/salles/supprimer">
        <input type="hidden" name="id" value="{{ salle['id'] }}">
        <button type="submit" style="background-color: red; color: white; border: none; padding: 0 12px; border-radius: 4px; cursor: pointer; line-height: 24px;">Supprimer</button>
      </form>
    </div>
  {% endfor %}
</div>

<h2>Ajouter une salle</h2>
<form method="post" action="/salles" style="margin-top: 20px;">
  <input name="nom" placeholder="Nom" required style="padding: 8px; margin-right: 8px;">
  <input name="capacite" type="number" min="1" placeholder="Capacité" required style="padding: 8px; margin-right: 8px;">
  <label style="margin-right: 16px;"><input name="projecteur" type="checkbox" value="1"> Projecteur</label>
  <button style="padding: 8px 16px;">Ajouter</button>
</form>

<h2>Modifier une salle</h2>
<form method="post" action="/salles/modifier" style="margin-top: 20px;">
  <select name="id" required style="padding: 8px; margin-right: 8px;">
    {% for salle in salles %}
      <option value="{{ salle['id'] }}">{{ salle["nom"] }}</option>
    {% endfor %}
  </select>
  <input name="nom" placeholder="Nouveau nom" style="padding: 8px; margin-right: 8px;">
  <input name="capacite" type="number" min="1" placeholder="Nouvelle capacité" style="padding: 8px; margin-right: 8px;">
  <label style="margin-right: 16px;"><input name="projecteur" type="checkbox" value="1"> Projecteur</label>
  <button style="padding: 8px 16px;">Modifier</button>
</form>

<h2>Réserver une salle</h2>
<form method="post" action="/reservations" style="margin-top: 20px;">
  <select name="salle_id" required style="padding: 8px; margin-right: 8px;">
    {% for salle in salles %}
      <option value="{{ salle['id'] }}">{{ salle["nom"] }}</option>
    {% endfor %}
  </select>
  <input name="personne" placeholder="Nom" required style="padding: 8px; margin-right: 8px;">
  <input name="date" type="date" required style="padding: 8px; margin-right: 8px;">
  <input name="debut" type="time" required style="padding: 8px; margin-right: 8px;">
  <input name="fin" type="time" required style="padding: 8px; margin-right: 8px;">
  <input name="participants" type="number" min="1" placeholder="Participants" required style="padding: 8px; margin-right: 8px;">
  <button style="padding: 8px 16px;">Réserver</button>
</form>

<h2>Réservations</h2>
<div class="salles-grid" style="margin-top: 20px;">
  {% for reservation in reservations %}
    <div style="padding: 8px; background: #e3f2fd; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
      <span style="line-height: 24px;">{{ reservation["personne"] }} - {{ reservation["nom"] }} - {{ reservation["date"] }} {{ reservation["debut"] }}-{{ reservation["fin"] }} ({{ reservation["participants"] }} pers.)</span>
      <form method="post" action="/reservations/supprimer">
        <input type="hidden" name="id" value="{{ reservation['id'] }}">
        <button type="submit" style="background-color: red; color: white; border: none; padding: 0 12px; border-radius: 4px; cursor: pointer; line-height: 24px;">Annuler</button>
      </form>
    </div>
  {% endfor %}
</div>
"""

app = Flask(__name__)


# Page d'accueil : lit les salles et affiche PAGE.
@app.get("/")
def accueil():
    with ouvrir_base() as conn:
        salles = conn.execute("SELECT id, nom, capacite, projecteur FROM salles").fetchall()
        reservations = conn.execute(
            "SELECT r.id, r.personne, r.date, r.debut, r.fin, r.participants, s.nom FROM reservations r JOIN salles s ON r.salle_id = s.id"
        ).fetchall()
    return render_template_string(PAGE, salles=salles, reservations=reservations)


# Exemple : reçoit le formulaire et ajoute une salle.
@app.post("/salles")
def ajouter_salle():
    nom = request.form["nom"]
    capacite = int(request.form["capacite"])
    projecteur = int(request.form.get("projecteur", 0))
    with ouvrir_base() as conn:
        conn.execute("INSERT INTO salles (nom, capacite, projecteur) VALUES (?, ?, ?)", [nom, capacite, projecteur])
    return redirect("/")


# Supprime une salle et ses réservations.
@app.post("/salles/supprimer")
def supprimer_salle():
    salle_id = int(request.form["id"])
    with ouvrir_base() as conn:
        conn.execute("DELETE FROM salles WHERE id = ?", [salle_id])
    return redirect("/")


# Modifie une salle.
@app.post("/salles/modifier")
def modifier_salle():
    salle_id = int(request.form["id"])
    nom = request.form.get("nom", "")
    capacite = request.form.get("capacite", "")
    projecteur = int(request.form.get("projecteur", 0))
    with ouvrir_base() as conn:
        if nom:
            conn.execute("UPDATE salles SET nom = ? WHERE id = ?", [nom, salle_id])
        if capacite:
            conn.execute("UPDATE salles SET capacite = ? WHERE id = ?", [int(capacite), salle_id])
        conn.execute("UPDATE salles SET projecteur = ? WHERE id = ?", [projecteur, salle_id])
    return redirect("/")


def heure_en_minutes(heure):
    """Convertit une heure HH:MM en minutes depuis minuit."""
    h, m = map(int, heure.split(":"))
    return h * 60 + m


# Ajoute une réservation.
@app.post("/reservations")
def ajouter_reservation():
    salle_id = int(request.form["salle_id"])
    personne = request.form["personne"]
    date = request.form["date"]
    debut = request.form["debut"]
    fin = request.form["fin"]
    participants = int(request.form["participants"])
    
    # Vérifie les horaires
    debut_min = heure_en_minutes(debut)
    fin_min = heure_en_minutes(fin)
    
    if debut_min < 8 * 60 or fin_min > 20 * 60:
        return "Horaire en dehors de 8h-20h", 400
    
    duree_min = fin_min - debut_min
    if duree_min < 30 or duree_min > 4 * 60:
        return "Durée invalide", 400
    
    with ouvrir_base() as conn:
        # Vérifie la capacité de la salle
        salle = conn.execute("SELECT capacite FROM salles WHERE id = ?", [salle_id]).fetchone()
        if salle is None:
            return "Salle introuvable", 400
        if participants > salle["capacite"]:
            return "Trop de participants", 400
        
        count = conn.execute(
            "SELECT COUNT(*) FROM reservations WHERE salle_id = ? AND date = ? AND NOT (fin <= ? OR ? <= debut)",
            [salle_id, date, debut, fin]
        ).fetchone()[0]
        if count > 0:
            return "Chevauchement", 400
        conn.execute(
            "INSERT INTO reservations (salle_id, personne, date, debut, fin, participants) VALUES (?, ?, ?, ?, ?, ?)",
            [salle_id, personne, date, debut, fin, participants]
        )
    return redirect("/")


# Supprime une réservation.
@app.post("/reservations/supprimer")
def supprimer_reservation():
    reservation_id = int(request.form["id"])
    with ouvrir_base() as conn:
        conn.execute("DELETE FROM reservations WHERE id = ?", [reservation_id])
    return redirect("/")


# Ajoutez vos fonctions ici. Le HTML va dans PAGE.


if __name__ == "__main__":
    app.run(debug=True)
