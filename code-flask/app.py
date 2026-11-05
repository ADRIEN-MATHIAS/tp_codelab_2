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


# Ajoutez vos fonctions ici. Le HTML va dans PAGE.


if __name__ == "__main__":
    app.run(debug=True)
