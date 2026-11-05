from flask import Flask, redirect, render_template_string, request, url_for

from base import ouvrir_base

# Le HTML de la page avec le design Linear.app
PAGE = """
<link rel="stylesheet" href="/static/css/linear-theme.css">
<div class="main-content">
  <h1>Réservation de salles</h1>

  <div class="stack-xl">
    <section>
      <h2>Salles</h2>
      <div class="room-grid">
        {% for salle in salles %}
          <div class="room-card">
            <div class="flex" style="justify-content: space-between; width: 100%;">
              <span class="text-primary">{{ salle["nom"] }}</span>
              <form method="post" action="/salles/supprimer">
                <input type="hidden" name="id" value="{{ salle['id'] }}">
                <button type="submit" class="btn btn-danger btn-sm">Supprimer</button>
              </form>
            </div>
          </div>
        {% endfor %}
      </div>
    </section>

    <section class="mt-6">
      <h2>Ajouter une salle</h2>
      <form method="post" action="/salles" class="flex-col">
        <div class="flex">
          <input name="nom" placeholder="Nom" required class="input">
          <input name="capacite" type="number" min="1" placeholder="Capacité" required class="input">
          <label class="flex items-center gap-2"><input name="projecteur" type="checkbox" value="1" class="checkbox"> Projecteur</label>
          <button class="btn btn-primary">Ajouter</button>
        </div>
      </form>
    </section>

    <section class="mt-6">
      <h2>Modifier une salle</h2>
      <form method="post" action="/salles/modifier" class="flex-col">
        <div class="flex">
          <select name="id" required class="select">
            {% for salle in salles %}
              <option value="{{ salle['id'] }}">{{ salle["nom"] }}</option>
            {% endfor %}
          </select>
          <input name="nom" placeholder="Nouveau nom" class="input">
          <input name="capacite" type="number" min="1" placeholder="Nouvelle capacité" class="input">
          <label class="flex items-center gap-2"><input name="projecteur" type="checkbox" value="1" class="checkbox"> Projecteur</label>
          <button class="btn btn-primary">Modifier</button>
        </div>
      </form>
    </section>

    <section class="mt-6">
      <h2>Réserver une salle</h2>
      <form method="post" action="/reservations" class="flex-col">
        <div class="flex flex-wrap">
          <select name="salle_id" required class="select">
            {% for salle in salles %}
              <option value="{{ salle['id'] }}">{{ salle["nom"] }}</option>
            {% endfor %}
          </select>
          <input name="personne" placeholder="Nom" required class="input">
          <input name="date" type="date" required class="input">
          <input name="debut" type="time" required class="input">
          <input name="fin" type="time" required class="input">
          <input name="participants" type="number" min="1" placeholder="Participants" required class="input">
          <button class="btn btn-primary">Réserver</button>
        </div>
      </form>
    </section>

    <section class="mt-6">
      <h2>Réservations</h2>
      <div class="reservation-list">
        {% for reservation in reservations %}
          <div class="reservation confirmed">
            <div class="flex" style="justify-content: space-between; width: 100%; flex-wrap: wrap;">
              <span>{{ reservation["personne"] }} - {{ reservation["nom"] }} - {{ reservation["date"] }} {{ reservation["debut"] }}-{{ reservation["fin"] }} ({{ reservation["participants"] }} pers.)</span>
              <form method="post" action="/reservations/supprimer">
                <input type="hidden" name="id" value="{{ reservation['id'] }}">
                <button type="submit" class="btn btn-danger btn-sm">Annuler</button>
              </form>
            </div>
          </div>
        {% endfor %}
      </div>
    </section>

    <section class="mt-6">
      <h2>Planning d'une salle</h2>
      <form method="get" action="/planning" class="flex-col">
        <div class="flex">
          <select name="salle_id" required class="select">
            {% for salle in salles %}
              <option value="{{ salle['id'] }}">{{ salle["nom"] }}</option>
            {% endfor %}
          </select>
          <input name="date" type="date" required class="input">
          <button class="btn btn-primary">Voir planning</button>
        </div>
      </form>
    </section>
  </div>
</div>

<style>
  .room-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--spacing-md);
    width: 100%;
  }
  @media (min-width: 600px) {
    .room-grid { grid-template-columns: repeat(4, 1fr); }
  }
  @media (min-width: 1200px) {
    .room-grid { grid-template-columns: repeat(8, 1fr); }
  }
  .flex-wrap { flex-wrap: wrap; }
  .items-center { align-items: center; }
  .gap-2 { gap: var(--spacing-xs); }
  .flex-col { flex-direction: column; }
  .stack-xl { display: flex; flex-direction: column; gap: var(--spacing-xl); }
  .mt-6 { margin-top: var(--spacing-xl); }
  section { padding-bottom: var(--spacing-lg); }
</style>
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
        conn.execute("DELETE FROM reservations WHERE salle_id = ?", [salle_id])
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


# Affiche le planning d'une salle pour une semaine.
@app.get("/planning")
def planning():
    salle_id = int(request.args.get("salle_id", 1))
    date_lundi = request.args.get("date", "2026-11-09")
    
    with ouvrir_base() as conn:
        salle = conn.execute("SELECT nom FROM salles WHERE id = ?", [salle_id]).fetchone()
        date_dimanche = conn.execute("SELECT date(?, '+6 days')", [date_lundi]).fetchone()[0]
        reservations = conn.execute(
            "SELECT id, personne, date, debut, fin, participants FROM reservations WHERE salle_id = ? AND date >= ? AND date <= ? ORDER BY date, debut",
            [salle_id, date_lundi, date_dimanche]
        ).fetchall()
    
    PLANNING_PAGE = """
    <link rel="stylesheet" href="/static/css/linear-theme.css">
    <div class="main-content">
      <div class="flex" style="justify-content: space-between; align-items: center; margin-bottom: var(--spacing-xl);">
        <h1>Planning de {{ salle_nom }}</h1>
        <a href="/" class="btn btn-secondary">Retour</a>
      </div>
      <p class="text-muted mb-4">Du {{ date_lundi }} au {{ date_dimanche }}</p>
      <div class="reservation-list mt-4">
        {% for r in reservations %}
          <div class="reservation confirmed mb-2">
            <span><strong>{{ r["date"] }}</strong> {{ r["debut"] }}-{{ r["fin"] }} : {{ r["personne"] }} ({{ r["participants"] }} pers.)</span>
          </div>
        {% endfor %}
      </div>
    </div>
    <style>
      .mb-2 { margin-bottom: var(--spacing-sm); }
      .mb-4 { margin-bottom: var(--spacing-lg); }
      .mt-4 { margin-top: var(--spacing-lg); }
    </style>
    """
    return render_template_string(PLANNING_PAGE, salle_nom=salle["nom"], reservations=reservations, date_lundi=date_lundi, date_dimanche=date_dimanche)


# Ajoutez vos fonctions ici. Le HTML va dans PAGE.


if __name__ == "__main__":
    app.run(debug=True)
