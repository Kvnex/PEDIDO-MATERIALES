from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "kvnex_secret_key"

# --- BASE DE DATOS ---
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

# --- TEMPLATES HTML ---
LAYOUT_ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #eef2f3; margin: 0; padding: 20px; }
    .container { max-width: 900px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); }
    h2 { color: #1e3c72; border-bottom: 3px solid #1e3c72; padding-bottom: 10px; }
    .nav { margin-bottom: 25px; }
    .btn { padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; font-weight: bold; display: inline-block; }
    .btn-blue { background: #1e3c72; color: white; }
    .btn-green { background: #27ae60; color: white; }
    .btn-add { background: #f39c12; color: white; margin-top: 10px; }
    .form-group { margin-bottom: 15px; }
    label { font-weight: bold; display: block; margin-bottom: 5px; }
    input[type="text"], select { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { border: 1px solid #ddd; padding: 10px; text-align: center; }
    th { background: #f8f9fa; }
    .check-entregado { transform: scale(1.5); }
    .status-badge { padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }
    .bg-success { background: #d4edda; color: #155724; }
    .bg-danger { background: #f8d7da; color: #721c24; }
</style>
"""

REGISTRO_HTML = LAYOUT_ESTILOS + """
<div class="container">
    <div class="nav"><a href="/buscar" class="btn btn-blue">🔍 Ir a Buscar Vale</a></div>
    <h2>📝 Registrar Nuevo Pedido</h2>
    <form method="POST" action="/guardar_pedido">
        <div style="display: flex; gap: 20px;">
            <div class="form-group" style="flex: 1;">
                <label>Embarcación:</label>
                <input type="text" name="embarcacion" required>
            </div>
            <div class="form-group" style="width: 200px;">
                <label>Prioridad:</label>
                <select name="prioridad">
                    <option value="NORMAL">NORMAL</option>
                    <option value="URGENTE">URGENTE</option>
                </select>
            </div>
        </div>
        <div class="form-group">
            <label>Solicitado por:</label>
            <input type="text" name="solicitado" required>
        </div>

        <h3>Materiales</h3>
        <table id="tabla-materiales">
            <thead>
                <tr>
                    <th style="width: 50px;">ITEM</th>
                    <th style="width: 100px;">CANT / UND</th>
                    <th>DESCRIPCIÓN</th>
                </tr>
            </thead>
            <tbody>
                {% for i in range(1, 11) %}
                <tr>
                    <td>{{ i }}</td>
                    <td><input type="text" name="cant_{{ i }}"></td>
                    <td><input type="text" name="desc_{{ i }}"></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <button type="button" class="btn btn-add" onclick="agregarFila()">+ Agregar más filas</button>
        <br><br>
        <button type="submit" class="btn btn-green" style="width: 100%; font-size: 1.2em;">🚀 Grabar Pedido</button>
    </form>
</div>

<script>
    let contadorFilas = 10;
    function agregarFila() {
        contadorFilas++;
        const tabla = document.getElementById('tabla-materiales').getElementsByTagName('tbody')[0];
        const nuevaFila = tabla.insertRow();
        nuevaFila.innerHTML = `
            <td>${contadorFilas}</td>
            <td><input type="text" name="cant_${contadorFilas}"></td>
            <td><input type="text" name="desc_${contadorFilas}"></td>
        `;
    }
</script>
"""

BUSCAR_HTML = LAYOUT_ESTILOS + """
<div class="container">
    <div class="nav"><a href="/" class="btn btn-blue">📝 Volver al Registro</a></div>
    <h2>🔍 Buscar Seguimiento de Vale</h2>
    <form method="GET" style="display: flex; gap: 10px; margin-bottom: 20px;">
        <input type="number" name="id" placeholder="N° de Vale" style="flex: 1;" required>
        <button type="submit" class="btn btn-blue">Buscar</button>
    </form>

    {% if pedido %}
    <div style="background: #f9f9f9; padding: 20px; border-radius: 8px; position: relative;">
        <button onclick="loginAdm({{ pedido.id }})" style="position: absolute; right: 10px; top: 10px; cursor:pointer;">🔐 ADM</button>
        <h3>VALE #{{ pedido.id }}</h3>
        <p><b>Fecha:</b> {{ pedido.fecha }} | <b>Embarcación:</b> {{ pedido.embarcacion }}</p>
        <p><b>Prioridad:</b> {{ pedido.prioridad }} | <b>Solicitado:</b> {{ pedido.solicitado_por }}</p>
        <p><b>Pedido de Compra:</b> {{ pedido.pedido_compra or '---' }}</p>
        <p><b>Sede:</b> {{ pedido.sede or '---' }}</p>
        
        <table>
            <thead>
                <tr>
                    <th>ITEM</th>
                    <th>CANT</th>
                    <th>DESCRIPCIÓN</th>
                    <th>ESTADO</th>
                </tr>
            </thead>
            <tbody>
                {% for m in materiales %}
                <tr>
                    <td>{{ m.item }}</td>
                    <td>{{ m.cantidad }}</td>
                    <td style="text-align: left;">{{ m.descripcion }}</td>
                    <td>
                        <span class="status-badge {{ 'bg-success' if m.entregado else 'bg-danger' }}">
                            {{ 'ENTREGADO' if m.entregado else 'PENDIENTE' }}
                        </span>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% elif error %}
    <p style="color:red; font-weight:bold;">{{ error }}</p>
    {% endif %}
</div>
<script>
    function loginAdm(id) {
        if (prompt("Clave de Administrador:") === "Kvnex123") {
            window.location.href = "/admin/" + id;
        } else { alert("Acceso Denegado"); }
    }
</script>
"""

ADMIN_HTML = LAYOUT_ESTILOS + """
<div class="container" style="background: #2c3e50; color: white;">
    <h2>ADMINISTRACIÓN - VALE #{{ pedido.id }}</h2>
    <form method="POST">
        <div class="form-group">
            <label style="color: white;">PEDIDOS DE COMPRA (Separar por comas):</label>
            <input type="text" name="pedido_compra" value="{{ pedido.pedido_compra or '' }}">
        </div>
        <div class="form-group">
            <label style="color: white;">SEDE / DESTINO:</label>
            <input type="text" name="sede" value="{{ pedido.sede or '' }}">
        </div>
        
        <table style="color: black; background: white;">
            <thead>
                <tr>
                    <th>ITEM</th>
                    <th>DESCRIPCIÓN</th>
                    <th>ENTREGADO?</th>
                </tr>
            </thead>
            <tbody>
                {% for m in materiales %}
                <tr>
                    <td>{{ m.item }}</td>
                    <td>{{ m.descripcion }}</td>
                    <td><input type="checkbox" name="mat_{{ m.id }}" class="check-entregado" {{ 'checked' if m.entregado }}></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <br>
        <button type="submit" class="btn btn-green" style="width: 100%;">💾 GUARDAR CAMBIOS</button>
        <br><br>
        <a href="/buscar?id={{ pedido.id }}" style="color: white;">❌ Cancelar</a>
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
    pedido_id = cursor.lastrowid

    # Procesar materiales dinámicamente
    item_idx = 1
    for key in f.keys():
        if key.startswith('desc_'):
            idx = key.split('_')[1]
            cantidad = f.get(f'cant_{idx}', '').strip()
            descripcion = f.get(f'desc_{idx}', '').strip()
            
            if descripcion: # Solo guardar si tiene descripción
                cursor.execute("INSERT INTO materiales (pedido_id, item, cantidad, descripcion) VALUES (?,?,?,?)",
                               (pedido_id, item_idx, cantidad, descripcion))
                item_idx += 1
    
    conn.commit()
    conn.close()
    return f"""<script>alert('Registrado con éxito. VALE N°: {pedido_id}'); window.location.href='/';</script>"""

@app.route("/buscar")
def buscar():
    p_id = request.args.get('id')
    if not p_id: return render_template_string(BUSCAR_HTML)
    
    conn = sqlite3.connect('pedidos.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    pedido = cursor.execute("SELECT * FROM pedidos WHERE id = ?", (p_id,)).fetchone()
    materiales = cursor.execute("SELECT * FROM materiales WHERE pedido_id = ? ORDER BY item", (p_id,)).fetchall()
    conn.close()
    
    if pedido:
        return render_template_string(BUSCAR_HTML, pedido=pedido, materiales=materiales)
    return render_template_string(BUSCAR_HTML, error="El número de vale no existe.")

@app.route("/admin/<int:p_id>", methods=["GET", "POST"])
def admin_panel(p_id):
    conn = sqlite3.connect('pedidos.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == "POST":
        cursor.execute("UPDATE pedidos SET pedido_compra = ?, sede = ? WHERE id = ?", 
                       (request.form['pedido_compra'], request.form['sede'], p_id))
        
        mats = cursor.execute("SELECT id FROM materiales WHERE pedido_id = ?", (p_id,)).fetchall()
        for m in mats:
            check = 1 if request.form.get(f"mat_{m['id']}") else 0
            cursor.execute("UPDATE materiales SET entregado = ? WHERE id = ?", (check, m['id']))
        
        conn.commit()
        conn.close()
        return redirect(url_for('buscar', id=p_id))

    pedido = cursor.execute("SELECT * FROM pedidos WHERE id = ?", (p_id,)).fetchone()
    materiales = cursor.execute("SELECT * FROM materiales WHERE pedido_id = ? ORDER BY item", (p_id,)).fetchall()
    conn.close()
    return render_template_string(ADMIN_HTML, pedido=pedido, materiales=materiales)

if __name__ == "__main__":
    app.run(debug=True)
