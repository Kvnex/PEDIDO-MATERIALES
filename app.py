from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "kvnex_marine_key"

# --- BASE DE DATOS (Persistencia local) ---
def init_db():
    conn = sqlite3.connect('pedidos.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        embarcacion TEXT,
        prioridad TEXT,
        solicitado_por TEXT,
        pedido_compra TEXT,
        sede TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS materiales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        item INTEGER,
        cantidad TEXT,
        descripcion TEXT,
        entregado INTEGER DEFAULT 0,
        FOREIGN KEY(pedido_id) REFERENCES pedidos(id)
    )''')
    conn.commit()
    conn.close()

init_db()

# --- ESTILOS VISUALES (Marítimo Dinámico) ---
ESTILOS = """
<style>
    body { 
        font-family: 'Segoe UI', Tahoma, sans-serif; 
        margin: 0; padding: 20px; min-height: 100vh;
        background: linear-gradient(-45deg, #1e3c72, #2a5298, #2193b0, #6dd5ed);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        display: flex; justify-content: center;
    }
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .container { 
        max-width: 850px; width: 100%;
        background: rgba(255, 255, 255, 0.95); 
        padding: 25px; border-radius: 15px; 
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        backdrop-filter: blur(5px);
    }
    h2 { color: #1e3c72; border-bottom: 3px solid #1e3c72; padding-bottom: 10px; margin-top: 0; }
    .nav { margin-bottom: 20px; text-align: right; }
    .btn { padding: 10px 18px; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; font-weight: bold; font-size: 13px; transition: 0.3s; }
    .btn-blue { background: #1e3c72; color: white; }
    .btn-green { background: #27ae60; color: white; width: 100%; font-size: 16px; margin-top: 20px; padding: 12px; }
    .btn-add { background: #f39c12; color: white; margin-top: 10px; }
    
    .form-row { display: flex; gap: 15px; margin-bottom: 15px; }
    .form-group { flex: 1; }
    label { font-size: 11px; font-weight: bold; color: #444; display: block; text-transform: uppercase; margin-bottom: 4px; }
    input[type="text"], input[type="number"], select { 
        width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 14px; 
    }
    table { width: 100%; border-collapse: collapse; margin-top: 15px; table-layout: fixed; background: white; }
    th { background: #f2f2f2; font-size: 11px; border: 1px solid #ddd; padding: 8px; color: #333; }
    td { border: 1px solid #ddd; padding: 0; }
    .input-tabla { width: 100%; border: none; padding: 10px; box-sizing: border-box; outline: none; font-size: 14px; background: transparent; }
    .input-tabla:focus { background: #e3f2fd; }
    .col-item { width: 45px; text-align: center; background: #f9f9f9; font-weight: bold; color: #1e3c72; }
    .col-cant { width: 90px; }
    .badge { padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; }
    .bg-ok { background: #d4edda; color: #155724; }
    .bg-wait { background: #f8d7da; color: #721c24; }
</style>
"""

# --- VISTA REGISTRO ---
REGISTRO_HTML = ESTILOS + """
<div class="container">
    <div class="nav"><a href="/buscar" class="btn btn-blue">🔍 BUSCAR VALE</a></div>
    <h2>Registro de Pedido</h2>
    <form method="POST" action="/guardar_pedido">
        <div class="form-row">
            <div class="form-group">
                <label>Embarcación / Nave</label>
                <input type="text" name="embarcacion" required>
            </div>
            <div style="width: 160px;">
                <label>Prioridad</label>
                <select name="prioridad">
                    <option value="NORMAL">NORMAL</option>
                    <option value="URGENTE">URGENTE</option>
                </select>
            </div>
        </div>
        <div class="form-group">
            <label>Solicitado por</label>
            <input type="text" name="solicitado" required>
        </div>

        <table>
            <thead>
                <tr>
                    <th class="col-item">#</th>
                    <th class="col-cant">CANT/UND</th>
                    <th>DESCRIPCIÓN DEL MATERIAL</th>
                </tr>
            </thead>
            <tbody id="tabla-body">
                {% for i in range(1, 6) %}
                <tr>
                    <td class="col-item">{{ i }}</td>
                    <td><input type="text" name="cant_{{ i }}" class="input-tabla"></td>
                    <td><input type="text" name="desc_{{ i }}" class="input-tabla"></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <button type="button" class="btn btn-add" onclick="agregarFila()">+ Fila</button>
        <button type="submit" class="btn btn-green">GRABAR PEDIDO</button>
    </form>
</div>
<script>
    let n = 5;
    function agregarFila() {
        n++;
        let tbody = document.getElementById('tabla-body');
        let fila = document.createElement('tr');
        fila.innerHTML = `<td class="col-item">${n}</td>
                          <td><input type="text" name="cant_${n}" class="input-tabla"></td>
                          <td><input type="text" name="desc_${n}" class="input-tabla"></td>`;
        tbody.appendChild(fila);
    }
</script>
"""

# --- VISTA BÚSQUEDA ---
BUSCAR_HTML = ESTILOS + """
<div class="container">
    <div class="nav"><a href="/" class="btn btn-blue">📝 NUEVO REGISTRO</a></div>
    <h2>Seguimiento de Vale</h2>
    <form method="GET" style="display: flex; gap: 10px; margin-bottom: 20px;">
        <input type="number" name="id" placeholder="N° de Vale" style="flex: 1;" required>
        <button type="submit" class="btn btn-blue">BUSCAR</button>
    </form>

    {% if pedido %}
    <div style="border: 2px solid #1e3c72; padding: 15px; border-radius: 10px; position: relative;">
        <div onclick="loginAdm({{ pedido.id }})" style="position: absolute; right: 10px; top: 10px; cursor: pointer; color: #bbb; font-size: 10px;">[ ADM ]</div>
        <h3>VALE #{{ pedido.id }}</h3>
        <p style="font-size: 13px; margin: 5px 0;"><b>FECHA:</b> {{ pedido.fecha }} | <b>NAVE:</b> {{ pedido.embarcacion }}</p>
        <p style="font-size: 13px; margin: 5px 0;"><b>PEDIDO COMPRA:</b> {{ pedido.pedido_compra or '---' }}</p>
        <p style="font-size: 13px; margin: 5px 0;"><b>SEDE:</b> {{ pedido.sede or '---' }}</p>
        
        <table>
            <thead>
                <tr>
                    <th style="width: 40px;">#</th>
                    <th style="width: 70px;">CANT</th>
                    <th>DESCRIPCIÓN</th>
                    <th style="width: 100px;">ESTADO</th>
                </tr>
            </thead>
            <tbody>
                {% for m in materiales %}
                <tr>
                    <td class="col-item">{{ m.item }}</td>
                    <td style="text-align: center; font-size: 13px;">{{ m.cantidad }}</td>
                    <td style="padding: 8px; font-size: 13px;">{{ m.descripcion }}</td>
                    <td style="text-align: center;">
                        <span class="badge {{ 'bg-ok' if m.entregado else 'bg-wait' }}">
                            {{ 'ENTREGADO' if m.entregado else 'PENDIENTE' }}
                        </span>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% elif error %}<p style="color: red; font-weight: bold;">{{ error }}</p>{% endif %}
</div>
<script>
    function loginAdm(id) {
        if (prompt("Clave ADM:") === "Kvnex123") { window.location.href = "/admin/" + id; }
    }
</script>
"""

# --- VISTA ADMIN ---
ADMIN_HTML = ESTILOS + """
<div class="container" style="background: #2c3e50; color: white;">
    <h3>Gestión ADM - Vale #{{ pedido.id }}</h3>
    <form method="POST">
        <label style="color: white;">PEDIDOS DE COMPRA:</label>
        <input type="text" name="pedido_compra" value="{{ pedido.pedido_compra or '' }}">
        <br><br>
        <label style="color: white;">SEDE:</label>
        <input type="text" name="sede" value="{{ pedido.sede or '' }}">
        
        <table style="background: white; color: black; margin-top: 15px;">
            <thead>
                <tr><th style="width: 40px;">#</th><th>MATERIAL</th><th style="width: 60px;">OK</th></tr>
            </thead>
            <tbody>
                {% for m in materiales %}
                <tr>
                    <td class="col-item">{{ m.item }}</td>
                    <td style="padding-left: 10px; font-size: 13px;">{{ m.descripcion }}</td>
                    <td style="text-align: center;">
                        <input type="checkbox" name="mat_{{ m.id }}" style="transform: scale(1.3);" {{ 'checked' if m.entregado }}>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <button type="submit" class="btn btn-green">GUARDAR CAMBIOS</button>
        <div style="text-align: center; margin-top: 15px;"><a href="/buscar?id={{ pedido.id }}" style="color: #ccc; font-size: 12px;">← Cancelar</a></div>
    </form>
</div>
"""

# --- RUTAS ---
@app.route("/")
def index():
    return render_template_string(REGISTRO_HTML)

@app.route("/guardar_pedido", methods=["POST"])
def guardar_pedido():
    f = request.form
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    conn = sqlite3.connect('pedidos.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO pedidos (fecha, embarcacion, prioridad, solicitado_por) VALUES (?,?,?,?)",
                   (fecha, f['embarcacion'], f['prioridad'], f['solicitado']))
    p_id = cursor.lastrowid
    item_n = 1
    for key in f.keys():
        if key.startswith('desc_'):
            idx = key.split('_')[1]
            c, d = f.get(f'cant_{idx}', '').strip(), f.get(f'desc_{idx}', '').strip()
            if d:
                cursor.execute("INSERT INTO materiales (pedido_id, item, cantidad, descripcion) VALUES (?,?,?,?)", (p_id, item_n, c, d))
                item_n += 1
    conn.commit()
    conn.close()
    return f"<script>alert('Vale N° {p_id} registrado'); window.location.href='/';</script>"

@app.route("/buscar")
def buscar():
    p_id = request.args.get('id')
    if not p_id: return render_template_string(BUSCAR_HTML)
    conn = sqlite3.connect('pedidos.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    p = cursor.execute("SELECT * FROM pedidos WHERE id = ?", (p_id,)).fetchone()
    m = cursor.execute("SELECT * FROM materiales WHERE pedido_id = ? ORDER BY item", (p_id,)).fetchall()
    conn.close()
    if p: return render_template_string(BUSCAR_HTML, pedido=p, materiales=m)
    return render_template_string(BUSCAR_HTML, error="Vale no encontrado.")

@app.route("/admin/<int:p_id>", methods=["GET", "POST"])
def admin_panel(p_id):
    conn = sqlite3.connect('pedidos.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if request.method == "POST":
        cursor.execute("UPDATE pedidos SET pedido_compra = ?, sede = ? WHERE id = ?", (request.form['pedido_compra'], request.form['sede'], p_id))
        mats = cursor.execute("SELECT id FROM materiales WHERE pedido_id = ?", (p_id,)).fetchall()
        for m in mats:
            st = 1 if request.form.get(f"mat_{m['id']}") else 0
            cursor.execute("UPDATE materiales SET entregado = ? WHERE id = ?", (st, m['id']))
        conn.commit()
        conn.close()
        return redirect(url_for('buscar', id=p_id))
    p = cursor.execute("SELECT * FROM pedidos WHERE id = ?", (p_id,)).fetchone()
    m = cursor.execute("SELECT * FROM materiales WHERE pedido_id = ? ORDER BY item", (p_id,)).fetchall()
    conn.close()
    return render_template_string(ADMIN_HTML, pedido=p, materiales=m)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
