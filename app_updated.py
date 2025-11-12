
"""
Instrucțiuni pentru rulare:
1. pip install flask pandas openpyxl
2. python app.py
3. Accesează http://127.0.0.1:5000
"""

from flask import Flask, render_template_string, request, redirect, url_for, send_file
import sqlite3
import pandas as pd

app = Flask(__name__)
DB_NAME = 'service_auto_web.db'

# Inițializare DB cu câmp suplimentar "nume"
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS masini (id INTEGER PRIMARY KEY AUTOINCREMENT, numar TEXT, marca TEXT, model TEXT, vin TEXT, nume TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS reparatii (id INTEGER PRIMARY KEY AUTOINCREMENT, masina_id INTEGER, tip TEXT, piesa TEXT, cod TEXT, cost REAL, FOREIGN KEY(masina_id) REFERENCES masini(id))")
conn.commit()
conn.close()

layout_header = """
<!doctype html>
<html lang='ro'>
<head>
<meta charset='utf-8'>
<title>Service Auto</title>
<link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css'>
</head>
<body class='p-4'>
<div class='container'>
<h1 class='mb-4'>Service Auto</h1>
<a href='{{ url_for("index") }}' class='btn btn-primary'>Acasă</a>
<a href='{{ url_for("adauga_masina") }}' class='btn btn-success'>Adaugă Mașină</a>
<a href='{{ url_for("export_excel") }}' class='btn btn-info'>Export Excel</a>
<hr>
"""
layout_footer = """
</div>
</body>
</html>
"""

@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    q = request.args.get('q', '')
    if q:
        cursor.execute("SELECT * FROM masini WHERE numar LIKE ? OR vin LIKE ? OR nume LIKE ?", (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        cursor.execute("SELECT * FROM masini")
    masini = cursor.fetchall()
    conn.close()
    content = """
    <h2>Lista Mașini</h2>
    <form method='get' class='mb-3'>
        <input type='text' name='q' placeholder='Caută număr, VIN sau nume' class='form-control' value='{{ request.args.get("q","") }}'>
    </form>
    <table class='table table-bordered'>
        <tr><th>Nume Persoană</th><th>Număr</th><th>Marca</th><th>Model</th><th>VIN</th><th>Detalii</th></tr>
        {% for m in masini %}
        <tr>
            <td>{{ m[5] }}</td><td>{{ m[1] }}</td><td>{{ m[2] }}</td><td>{{ m[3] }}</td><td>{{ m[4] }}</td>
            <td><a href='{{ url_for("detalii_masina", masina_id=m[0]) }}' class='btn btn-sm btn-secondary'>Vezi</a></td>
        </tr>
        {% endfor %}
    </table>
    """
    return render_template_string(layout_header + content + layout_footer, masini=masini)

@app.route('/adauga', methods=['GET','POST'])
def adauga_masina():
    if request.method == 'POST':
        nume = request.form['nume']
        numar = request.form['numar']
        marca = request.form['marca']
        model = request.form['model']
        vin = request.form['vin']
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO masini (numar, marca, model, vin, nume) VALUES (?,?,?,?,?)", (numar, marca, model, vin, nume))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    content = """
    <h2>Adaugă Mașină</h2>
    <form method='post'>
        <input name='nume' placeholder='Nume persoană' class='form-control mb-2'>
        <input name='numar' placeholder='Număr' class='form-control mb-2'>
        <input name='marca' placeholder='Marca' class='form-control mb-2'>
        <input name='model' placeholder='Model' class='form-control mb-2'>
        <input name='vin' placeholder='VIN' class='form-control mb-2'>
        <button class='btn btn-success'>Salvează</button>
    </form>
    """
    return render_template_string(layout_header + content + layout_footer)

@app.route('/detalii/<int:masina_id>', methods=['GET','POST'])
def detalii_masina(masina_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM masini WHERE id=?", (masina_id,))
    masina = cursor.fetchone()
    cursor.execute("SELECT * FROM reparatii WHERE masina_id=?", (masina_id,))
    reparatii = cursor.fetchall()
    conn.close()
    if request.method == 'POST':
        tip = request.form['tip']
        piesa = request.form['piesa']
        cod = request.form['cod']
        cost = request.form['cost']
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reparatii (masina_id, tip, piesa, cod, cost) VALUES (?,?,?,?,?)", (masina_id, tip, piesa, cod, cost))
        conn.commit()
        conn.close()
        return redirect(url_for('detalii_masina', masina_id=masina_id))
    content = """
    <h2>Detalii Mașină</h2>
    <p><strong>{{ masina[5] }} | {{ masina[1] }} - {{ masina[2] }} {{ masina[3] }} (VIN: {{ masina[4] }})</strong></p>
    <h3>Reparații</h3>
    <table class='table table-bordered'>
        <tr><th>Tip</th><th>Piesa</th><th>Cod</th><th>Cost</th></tr>
        {% for r in reparatii %}
        <tr><td>{{ r[2] }}</td><td>{{ r[3] }}</td><td>{{ r[4] }}</td><td>{{ r[5] }}</td></tr>
        {% endfor %}
    </table>
    <h4>Adaugă Reparație</h4>
    <form method='post'>
        <input name='tip' placeholder='Tip reparație' class='form-control mb-2'>
        <input name='piesa' placeholder='Piesa' class='form-control mb-2'>
        <input name='cod' placeholder='Cod piesă' class='form-control mb-2'>
        <input name='cost' placeholder='Cost' class='form-control mb-2'>
        <button class='btn btn-primary'>Adaugă</button>
    </form>
    """
    return render_template_string(layout_header + content + layout_footer, masina=masina, reparatii=reparatii)

@app.route('/export')
def export_excel():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT m.nume, m.numar, m.marca, m.model, m.vin, r.tip, r.piesa, r.cod, r.cost FROM masini m LEFT JOIN reparatii r ON m.id=r.masina_id")
    rows = cursor.fetchall()
    conn.close()
    df = pd.DataFrame(rows, columns=["Nume", "Număr", "Marca", "Model", "VIN", "Tip", "Piesa", "Cod", "Cost"])
    file_name = "raport_service_web.xlsx"
    df.to_excel(file_name, index=False)
    return send_file(file_name, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)


# Ruta pentru editare masina
@app.route('/edit/<int:masina_id>', methods=['POST'])
def edit_masina(masina_id):
    nume = request.form['nume']
    numar = request.form['numar']
    marca = request.form['marca']
    model = request.form['model']
    vin = request.form['vin']
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE masini SET nume=?, numar=?, marca=?, model=?, vin=? WHERE id=?", (nume, numar, marca, model, vin, masina_id))
    conn.commit()
    cursor.execute("SELECT * FROM masini WHERE id=?", (masina_id,))
    masina = cursor.fetchone()
    cursor.execute("SELECT * FROM reparatii WHERE masina_id=?", (masina_id,))
    reparatii = cursor.fetchall()
    conn.close()
    content = """
    <h2>Detalii Mașină (Actualizat)</h2>
    <p><strong>{{ masina[5] }} | {{ masina[1] }} - {{ masina[2] }} {{ masina[3] }} (VIN: {{ masina[4] }})</strong></p>
    <h3>Editare Detalii</h3>
    <form method='post' action='{{ url_for("edit_masina", masina_id=masina[0]) }}'>
    <input name='nume' value='{{ masina[5] }}' class='form-control mb-2'>
    <input name='numar' value='{{ masina[1] }}' class='form-control mb-2'>
    <input name='marca' value='{{ masina[2] }}' class='form-control mb-2'>
    <input name='model' value='{{ masina[3] }}' class='form-control mb-2'>
    <input name='vin' value='{{ masina[4] }}' class='form-control mb-2'>
    <button class='btn btn-primary'>Salvează</button>
    </form>
    <h3>Reparații</h3>
    <table class='table table-bordered'>
    <tr><th>Tip</th><th>Piesa</th><th>Cod</th><th>Cost</th></tr>
    {% for r in reparatii %}
    <tr><td>{{ r[2] }}</td><td>{{ r[3] }}</td><td>{{ r[4] }}</td><td>{{ r[5] }}</td></tr>
    {% endfor %}
    </table>
    """
    return render_template_string(layout_header + content + layout_footer, masina=masina, reparatii=reparatii)

# Ruta pentru stergere masina
@app.route('/delete/<int:masina_id>')
def delete_masina(masina_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM masini WHERE id=?", (masina_id,))
    cursor.execute("DELETE FROM reparatii WHERE masina_id=?", (masina_id,))
    conn.commit()
    cursor.execute("SELECT * FROM masini")
    masini = cursor.fetchall()
    conn.close()
    content = """
    <h2>Lista Mașini (După Ștergere)</h2>
    <table class='table table-bordered'>
    <tr><th>Nume Persoană</th><th>Număr</th><th>Marca</th><th>Model</th><th>VIN</th><th>Acțiuni</th></tr>
    {% for m in masini %}
    <tr>
    <td>{{ m[5] }}</td><td>{{ m[1] }}</td><td>{{ m[2] }}</td><td>{{ m[3] }}</td><td>{{ m[4] }}</td>
    <td>
    <a href='{{ url_for("detalii_masina", masina_id=m[0]) }}' class='btn btn-sm btn-secondary'>Vezi</a>
    <a href='{{ url_for("delete_masina", masina_id=m[0]) }}' class='btn btn-sm btn-danger'>Șterge</a>
    </td>
    </tr>
    {% endfor %}
    </table>
    """
    return render_template_string(layout_header + content + layout_footer, masini=masini)
