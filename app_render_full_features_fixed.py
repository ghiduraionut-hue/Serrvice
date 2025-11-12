
from flask import Flask, render_template_string, request, redirect, url_for, send_file
import sqlite3
import pandas as pd
import os

app = Flask(__name__)
DB_NAME = 'service_auto_web.db'

# Inițializare DB
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS masini (id INTEGER PRIMARY KEY AUTOINCREMENT, numar TEXT, marca TEXT, model TEXT, vin TEXT, nume TEXT, motorizare TEXT, cod_motor TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS reparatii (id INTEGER PRIMARY KEY AUTOINCREMENT, masina_id INTEGER, tip TEXT, piesa TEXT, numar_km TEXT, data TEXT, cod TEXT, cost REAL, FOREIGN KEY(masina_id) REFERENCES masini(id))")
cursor.execute("CREATE TABLE IF NOT EXISTS programari (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, ora_start TEXT, ora_end TEXT, descriere TEXT)")
conn.commit()
conn.close()

layout_header = """
<!doctype html>
<html lang='ro'>
<head>
<meta charset='utf-8'>
<title>Service Auto</title>
<link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css'>
<link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/index.global.min.css'>
<script src='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/index.global.min.js'></script>
<style>#calendar { max-width: 600px; margin: 20px auto; }</style>
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
        cursor.execute("SELECT * FROM masini WHERE numar LIKE ? OR marca LIKE ? OR nume LIKE ?", (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        cursor.execute("SELECT * FROM masini")
    masini = cursor.fetchall()
    cursor.execute("SELECT * FROM programari")
    programari = cursor.fetchall()
    conn.close()
    content = """
    <h2>Calendar Programări</h2>
    <div id='calendar'></div>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        var calendarEl = document.getElementById('calendar');
        var calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            height: 'auto',
            dateClick: function(info) {
                window.location.href = '/adauga_programare?data=' + info.dateStr;
            },
            eventClick: function(info) {
                var id = info.event.id;
                window.location.href = '/editeaza_programare/' + id;
            },
            events: [
                {% for p in programari %}
                { id: '{{ p[0] }}', title: '{{ p[4] }} ({{ p[2] }}-{{ p[3] }})', start: '{{ p[1] }}' },
                {% endfor %}
            ]
        });
        calendar.render();
    });
    </script>
    <hr>
    <h2>Lista Mașini</h2>
    <form method='get' class='mb-3'>
    <input type='text' name='q' placeholder='Caută nume, număr sau marcă' class='form-control' value='{{ request.args.get("q","") }}'>
    </form>
    <table class='table table-bordered'>
    <tr><th>Nume</th><th>Număr</th><th>Marca</th><th>Model</th><th>Acțiuni</th></tr>
    {% for m in masini %}
    <tr>
    <td>{{ m[5] }}</td><td>{{ m[1] }}</td><td>{{ m[2] }}</td><td>{{ m[3] }}</td>
    <td>
    <a href='{{ url_for("detalii_masina", masina_id=m[0]) }}' class='btn btn-sm btn-secondary'>Detalii</a>
    <a href='{{ url_for("sterge_masina", masina_id=m[0]) }}' class='btn btn-sm btn-danger'>Șterge</a>
    </td>
    </tr>
    {% endfor %}
    </table>
    """
    return render_template_string(layout_header + content + layout_footer, masini=masini, programari=programari)

@app.route('/adauga', methods=['GET','POST'])
def adauga_masina():
    if request.method == 'POST':
        nume = request.form['nume']
        numar = request.form['numar']
        marca = request.form['marca']
        model = request.form['model']
        vin = request.form['vin']
        motorizare = request.form['motorizare']
        cod_motor = request.form['cod_motor']
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO masini (numar, marca, model, vin, nume, motorizare, cod_motor) VALUES (?,?,?,?,?,?,?)", (numar, marca, model, vin, nume, motorizare, cod_motor))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    content = """
    <h2>Adaugă Mașină</h2>
    <form method='post'>
    <input name='nume' placeholder='Nume' class='form-control mb-2'>
    <input name='numar' placeholder='Număr' class='form-control mb-2'>
    <input name='marca' placeholder='Marca' class='form-control mb-2'>
    <input name='model' placeholder='Model' class='form-control mb-2'>
    <input name='vin' placeholder='VIN' class='form-control mb-2'>
    <input name='motorizare' placeholder='Motorizare' class='form-control mb-2'>
    <input name='cod_motor' placeholder='Cod Motor' class='form-control mb-2'>
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
        numar_km = request.form['numar_km']
        data = request.form['data']
        cod = request.form['cod']
        cost = request.form['cost']
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reparatii (masina_id, tip, piesa, numar_km, data, cod, cost) VALUES (?,?,?,?,?,?,?)", (masina_id, tip, piesa, numar_km, data, cod, cost))
        conn.commit()
        conn.close()
        return redirect(url_for('detalii_masina', masina_id=masina_id))
    content = """
    <h2>Detalii Mașină</h2>
    <p><strong>{{ masina[5] }} | {{ masina[1] }} - {{ masina[2] }} {{ masina[3] }}</strong></p>
    <table class='table table-bordered'>
    <tr><th>Tip</th><th>Piesa</th><th>KM</th><th>Data</th><th>Cod</th><th>Cost</th><th>Acțiuni</th></tr>
    {% for r in reparatii %}
    <tr>
    <td>{{ r[2] }}</td><td>{{ r[3] }}</td><td>{{ r[4] }}</td><td>{{ r[5] }}</td><td>{{ r[6] }}</td><td>{{ r[7] }}</td>
    <td><a href='{{ url_for("sterge_reparatie", reparatie_id=r[0], masina_id=masina[0]) }}' class='btn btn-sm btn-danger'>Șterge</a></td>
    </tr>
    {% endfor %}
    </table>
    <h4>Adaugă Reparație</h4>
    <form method='post'>
    <input name='tip' placeholder='Tip reparație' class='form-control mb-2'>
    <input name='piesa' placeholder='Piesa' class='form-control mb-2'>
    <input name='numar_km' placeholder='Număr kilometri' class='form-control mb-2'>
    <input name='data' placeholder='Data (YYYY-MM-DD)' class='form-control mb-2'>
    <input name='cod' placeholder='Cod piesă' class='form-control mb-2'>
    <input name='cost' placeholder='Cost' class='form-control mb-2'>
    <button class='btn btn-primary'>Adaugă</button>
    </form>
    """
    return render_template_string(layout_header + content + layout_footer, masina=masina, reparatii=reparatii)

@app.route('/sterge_masina/<int:masina_id>')
def sterge_masina(masina_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reparatii WHERE masina_id=?", (masina_id,))
    cursor.execute("DELETE FROM masini WHERE id=?", (masina_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/sterge_reparatie/<int:reparatie_id>/<int:masina_id>')
def sterge_reparatie(reparatie_id, masina_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reparatii WHERE id=?", (reparatie_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('detalii_masina', masina_id=masina_id))

@app.route('/adauga_programare', methods=['GET','POST'])
def adauga_programare():
    data = request.args.get('data', '')
    if request.method == 'POST':
        ora_start = request.form['ora_start']
        ora_end = request.form['ora_end']
        descriere = request.form['descriere']
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO programari (data, ora_start, ora_end, descriere) VALUES (?,?,?,?)", (data, ora_start, ora_end, descriere))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    content = f"""
    <h2>Adaugă Programare pentru {data}</h2>
    <form method='post'>
    <input name='ora_start' placeholder='Ora început (HH:MM)' class='form-control mb-2'>
    <input name='ora_end' placeholder='Ora sfârșit (HH:MM)' class='form-control mb-2'>
    <input name='descriere' placeholder='Descriere programare' class='form-control mb-2'>
    <button class='btn btn-success'>Salvează</button>
    </form>
    """
    return render_template_string(layout_header + content + layout_footer)

@app.route('/editeaza_programare/<int:prog_id>', methods=['GET','POST'])
def editeaza_programare(prog_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM programari WHERE id=?", (prog_id,))
    prog = cursor.fetchone()
    if request.method == 'POST':
        data = request.form['data']
        ora_start = request.form['ora_start']
        ora_end = request.form['ora_end']
        descriere = request.form['descriere']
        cursor.execute("UPDATE programari SET data=?, ora_start=?, ora_end=?, descriere=? WHERE id=?", (data, ora_start, ora_end, descriere, prog_id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    conn.close()
    content = f"""
    <h2>Editare Programare</h2>
    <form method='post'>
    <input name='data' value='{prog[1]}' class='form-control mb-2'>
    <input name='ora_start' value='{prog[2]}' class='form-control mb-2'>
    <input name='ora_end' value='{prog[3]}' class='form-control mb-2'>
    <input name='descriere' value='{prog[4]}' class='form-control mb-2'>
    <button class='btn btn-primary'>Actualizează</button>
    </form>
    """
    return render_template_string(layout_header + content + layout_footer)

@app.route('/export')
def export_excel():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT m.nume, m.numar, m.marca, m.model, m.vin, m.motorizare, m.cod_motor, r.tip, r.piesa, r.numar_km, r.data, r.cod, r.cost FROM masini m LEFT JOIN reparatii r ON m.id=r.masina_id")
    rows = cursor.fetchall()
    conn.close()
    df = pd.DataFrame(rows, columns=["Nume", "Număr", "Marca", "Model", "VIN", "Motorizare", "Cod Motor", "Tip", "Piesa", "Număr KM", "Data", "Cod", "Cost"])
    file_name = "raport_service_web.xlsx"
    df.to_excel(file_name, index=False)
    return send_file(file_name, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
