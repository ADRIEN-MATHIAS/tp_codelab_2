from datetime import datetime, timedelta
from flask import Flask, redirect, render_template_string, request

from base import ouvrir_base

# Le HTML de la page.
PAGE = """
<h1>Réservation de salles</h1>

<h2>Salles</h2>
<ul>
  {% for salle in salles %}
    <li>{{ salle["nom"] }} ({{ salle["type"] }})
      <form method="post" action="/salles/{{ salle["id"] }}/supprimer">
        <button>Supprimer</button>
      </form>
      <form method="post" action="/salles/{{ salle["id"] }}/modifier">
        <input name="nom" value="{{ salle["nom"] }}" placeholder="Nom" required>
        <input name="type" value="{{ salle["type"] }}" placeholder="Type" required>
        <input name="capacite" type="number" min="1" value="{{ salle["capacite"] }}" placeholder="Capacité" required>
        projecteur: <input name="projecteur" type="checkbox" value="1" {% if salle["projecteur"] == 1 %}checked{% endif %}>
        <button>Modifier</button>
      </form>
      <form method="post" action="/salles/{{ salle["id"] }}/reserver">
        <input name="personne" placeholder="Personne" required>
        <input name="date" type="date" required>
        <input name="debut" type="time" required>
        <input name="fin" type="time" required>
        <input name="participants" type="number" min="1" placeholder="Participants" required>
        <input name="semaines" type="number" min="1" value="1" placeholder="Semaines">
        <button>Réserver</button>
      </form>
      <a href="/salles/{{ salle["id"] }}/planning">Planning</a>
    </li>
  {% endfor %}
</ul>

<form method="post" action="/salles">
  <input name="nom" placeholder="Nom" required>
  <input name="type" placeholder="Type" value="cours" required>
  <input name="capacite" type="number" min="1" placeholder="Capacité" required>
  projecteur: <input name="projecteur" type="checkbox" value="1">
  <button>Ajouter</button>
</form>

{% if erreur == "capacite" %}
<p style="color:red">Erreur : Le nombre de participants dépasse la capacité de la salle.</p>
{% elif erreur == "plage" %}
<p style="color:red">Erreur : La réservation doit être comprise entre 8h00 et 20h00.</p>
{% elif erreur == "duree" %}
<p style="color:red">Erreur : La durée doit être comprise entre 30 minutes et 4 heures.</p>
{% elif erreur == "chevauchement" %}
<p style="color:red">Erreur : Une réservation existe déjà à cette heure.</p>
{% elif erreur == "chevauchement_personne" %}
<p style="color:red">Erreur : Cette personne a déjà une réservation qui se chevauche sur ce créneau.</p>
{% endif %}
"""

app = Flask(__name__)


# Page d'accueil : lit les salles et affiche PAGE.
@app.get("/")
def accueil():
    erreur = request.args.get('erreur')
    with ouvrir_base() as conn:
        salles = conn.execute("SELECT id, nom, capacite, projecteur, type FROM salles").fetchall()
    return render_template_string(PAGE, salles=salles, erreur=erreur)


# Exemple : reçoit le formulaire et ajoute une salle.
@app.post("/salles")
def ajouter_salle():
    nom = request.form["nom"]
    type_local = request.form.get("type", "cours")
    capacite = int(request.form["capacite"])
    projecteur = 1 if request.form.get("projecteur") else 0
    with ouvrir_base() as conn:
        conn.execute("INSERT INTO salles (nom, capacite, projecteur, type) VALUES (?, ?, ?, ?)", [nom, capacite, projecteur, type_local])
    return redirect("/")


# Supprimer une salle (et ses réservations en cascade)
@app.post("/salles/<int:salle_id>/supprimer")
def supprimer_salle(salle_id):
    with ouvrir_base() as conn:
        conn.execute("DELETE FROM salles WHERE id = ?", [salle_id])
    return redirect("/")


# Modifier une salle existante
@app.post("/salles/<int:salle_id>/modifier")
def modifier_salle(salle_id):
    nom = request.form["nom"]
    type_local = request.form.get("type", "cours")
    capacite = int(request.form["capacite"])
    projecteur = 1 if request.form.get("projecteur") else 0
    with ouvrir_base() as conn:
        conn.execute("UPDATE salles SET nom = ?, capacite = ?, projecteur = ?, type = ? WHERE id = ?", [nom, capacite, projecteur, type_local, salle_id])
    return redirect("/")


# Réserver une salle
@app.post("/salles/<int:salle_id>/reserver")
def reserver_salle(salle_id):
    personne = request.form["personne"]
    date = request.form["date"]
    debut = request.form["debut"]
    fin = request.form["fin"]
    participants = int(request.form["participants"])
    semaines = int(request.form.get("semaines") or 1)
    
    with ouvrir_base() as conn:
        # Récupérer la capacité de la salle
        salle = conn.execute("SELECT capacite FROM salles WHERE id = ?", [salle_id]).fetchone()
        capacite_salle = salle["capacite"] if salle else 0
        
        # Vérifier que le nombre de participants ne dépasse pas la capacité
        if participants > capacite_salle:
            return redirect("/?erreur=capacite")
        
        # Vérifier que la réservation a lieu entre 8h00 et 20h00
        debut_min = int(debut.split(":")[0]) * 60 + int(debut.split(":")[1])
        fin_min = int(fin.split(":")[0]) * 60 + int(fin.split(":")[1])
        if debut_min < 8 * 60 or fin_min > 20 * 60:
            return redirect("/?erreur=plage")
        
        # Vérifier la durée de la réservation (entre 30 min et 4h)
        duree_min = fin_min - debut_min
        if duree_min < 30 or duree_min > 4 * 60:
            return redirect("/?erreur=duree")
        
        # Calculer toutes les dates de la réservation répétée chaque semaine (B3)
        date_depart = datetime.strptime(date, "%Y-%m-%d")
        dates = [(date_depart + timedelta(weeks=i)).strftime("%Y-%m-%d") for i in range(semaines)]
        
        # Vérifier les chevauchements pour chaque occurrence
        for d in dates:
            # Vérifier que la personne n'a pas déjà une réservation qui se chevauche (B1)
            reservations_personne = conn.execute(
                "SELECT debut, fin FROM reservations WHERE personne = ? AND date = ?", [personne, d]
            ).fetchall()
            for res in reservations_personne:
                if debut < res["fin"] and fin > res["debut"]:
                    return redirect("/?erreur=chevauchement_personne")

            # Vérifier les chevauchements avec les réservations existantes pour la même salle
            reservations_existantes = conn.execute(
                "SELECT debut, fin FROM reservations WHERE salle_id = ? AND date = ?", [salle_id, d]
            ).fetchall()
            for res in reservations_existantes:
                if debut < res["fin"] and fin > res["debut"]:
                    return redirect("/?erreur=chevauchement")
        
        # Si aucun conflit sur toute la période, insérer les réservations
        for d in dates:
            conn.execute(
                "INSERT INTO reservations (salle_id, personne, date, debut, fin, participants) VALUES (?, ?, ?, ?, ?, ?)",
                [salle_id, personne, d, debut, fin, participants]
            )
    return redirect("/")


# Planning d'une salle sur une semaine
@app.get("/salles/<int:salle_id>/planning")
def planning_salle(salle_id):
    with ouvrir_base() as conn:
        # Récupérer toutes les réservations pour cette salle
        reservations = conn.execute(
            "SELECT date, debut, fin, personne FROM reservations WHERE salle_id = ? ORDER BY date, debut", [salle_id]
        ).fetchall()
        # Récupérer le nom de la salle
        salle = conn.execute("SELECT nom FROM salles WHERE id = ?", [salle_id]).fetchone()
        salle_nom = salle["nom"] if salle else "Salle inconnue"
    
    # Days of the week in French
    jours_semaine = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    
    # Organiser les réservations par jour
    planning = {i: [] for i in range(7)}
    from datetime import datetime
    for res in reservations:
        # Calculer le jour de la semaine (lundi = 0, dimanche = 6)
        date_obj = datetime.strptime(res["date"], "%Y-%m-%d")
        jour_semaine_idx = (date_obj.weekday() + 1) % 7  # lundi=0, dimanche=6
        planning[jour_semaine_idx].append({
            "personne": res["personne"],
            "debut": res["debut"],
            "fin": res["fin"],
            "date": res["date"]
        })
    
    return render_template_string("""
    <h1>Planning de {{ salle_nom }}</h1>
    <p><a href="/">Retour à l'accueil</a></p>
    <div class="planning">
    {% for i in range(7) %}
      <h2>{{ jours_semaine[i] }}</h2>
      <div class="day">
      {% set has_reservations = planning[i] | length > 0 %}
      {% if has_reservations %}
      {% for reservation in planning[i] %}
        <div class="reservation">
          <strong>{{ reservation.personne }}</strong> {{ reservation.debut }} - {{ reservation.fin }} <br>
          {{ reservation.date }}
        </div>
      {% endfor %}
      {% else %}
        <p>Aucune réservation</p>
      {% endif %}
      </div>
    {% endfor %}
    </div>
    """, salle_nom=salle_nom, planning=planning, jours_semaine=jours_semaine)


# Ajoutez vos fonctions ici. Le HTML va dans PAGE.


if __name__ == "__main__":
    app.run(debug=True)