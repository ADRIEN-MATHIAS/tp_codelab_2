from flask import Flask, redirect, render_template_string, request

from base import ouvrir_base

# Le HTML de la page.
PAGE = """
<h1>Réservation de salles</h1>

<h2>Salles</h2>
<ul>
  {% for salle in salles %}
    <li>{{ salle["nom"] }} 
      <form method="post" action="/salles/{{ salle["id"] }}/supprimer">
        <button>Supprimer</button>
      </form>
      <form method="post" action="/salles/{{ salle["id"] }}/modifier">
        <input name="nom" value="{{ salle["nom"] }}" placeholder="Nom" required>
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
        <button>Réserver</button>
      </form>
    </li>
  {% endfor %}
</ul>

<form method="post" action="/salles">
  <input name="nom" placeholder="Nom" required>
  <input name="capacite" type="number" min="1" placeholder="Capacité" required>
  projecteur: <input name="projecteur" type="checkbox" value="1">
  <button>Ajouter</button>
</form>
"""

app = Flask(__name__)


# Page d'accueil : lit les salles et affiche PAGE.
@app.get("/")
def accueil():
    with ouvrir_base() as conn:
        salles = conn.execute("SELECT id, nom FROM salles").fetchall()
    return render_template_string(PAGE, salles=salles)


# Exemple : reçoit le formulaire et ajoute une salle.
@app.post("/salles")
def ajouter_salle():
    nom = request.form["nom"]
    capacite = int(request.form["capacite"])
    projecteur = 1 if request.form.get("projecteur") else 0
    with ouvrir_base() as conn:
        conn.execute("INSERT INTO salles (nom, capacite, projecteur) VALUES (?, ?, ?)", [nom, capacite, projecteur])
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
    capacite = int(request.form["capacite"])
    projecteur = 1 if request.form.get("projecteur") else 0
    with ouvrir_base() as conn:
        conn.execute("UPDATE salles SET nom = ?, capacite = ?, projecteur = ? WHERE id = ?", [nom, capacite, projecteur, salle_id])
    return redirect("/")


# Réserver une salle
@app.post("/salles/<int:salle_id>/reserver")
def reserver_salle(salle_id):
    personne = request.form["personne"]
    date = request.form["date"]
    debut = request.form["debut"]
    fin = request.form["fin"]
    participants = int(request.form["participants"])
    
    with ouvrir_base() as conn:
        # Vérifier les chevauchements avec les réservations existantes
        reservations_existantes = conn.execute(
            "SELECT debut, fin FROM reservations WHERE salle_id = ?", [salle_id]
        ).fetchall()
        
        chevauche = False
        for res in reservations_existantes:
            exist_debut = res["debut"]
            exist_fin = res["fin"]
            # Deux intervalles [debut, fin] et [exist_debut, exist_fin] se chevauchent si :
            # debut < exist_fin ET fin > exist_debut
            # On autorise finishing à 12h et commençant à 12h (pas de chevauchement)
            if debut < exist_fin and fin > exist_debut:
                chevauche = True
                break
        
        if not chevauche:
            conn.execute(
                "INSERT INTO reservations (salle_id, personne, date, debut, fin, participants) VALUES (?, ?, ?, ?, ?, ?)",
                [salle_id, personne, date, debut, fin, participants]
            )
    return redirect("/")


# Ajoutez vos fonctions ici. Le HTML va dans PAGE.


if __name__ == "__main__":
    app.run(debug=True)
