from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "kvnex_secret_key"

# --- BASE DE DATOS (Se crea sola al ejecutar) ---
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

# --- ESTILOS CSS COMPACTOS (ESTILO TABLA) ---
ESTILOS = """
<style>
    body { font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 10px; }
    .container { max-width: 850px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    h2 { color: #1e3c72; margin-top: 0; border-bottom: 2px solid #eee; padding-bottom: 8px; }
    .nav { margin-bottom: 15px; }
    .btn { padding: 8px 15px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; font-weight: bold; font-size: 13px; display: inline-block; }
    .btn-blue { background: #1e3c72; color: white; }
    .btn-green { background: #27ae60; color: white; width: 100%; font-size: 16px; margin-top: 15px; }
    .btn-add { background: #f39c12; color: white; margin-top: 10px; }
    
    .form-row { display: flex; gap: 15px; margin-bottom: 10px; }
    .form-group { flex: 1; }
    label { font-size: 11px; font-weight: bold; color: #666; display: block; text-transform: uppercase; }
    input[type="text"], input[type="number"], select { 
        width: 100%; padding: 7px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; font-size: 14px; 
    }

    table { width: 100%; border-collapse: collapse; margin-top: 10px; table-layout: fixed; }
    th { background: #f8f9fa; font-size: 11px; border: 1px solid #ddd; padding: 6px; }
    td { border: 1px solid #ddd; padding: 0; }
    
    .input-tabla { 
        width: 100%; border: none; padding: 10px; box-sizing: border-box; outline: none; font-size: 14px; 
    }
    .input-tabla:focus { background: #fffde7; border: 1px solid #1e3c72; }
    
    .col-item { width: 45px; text-align: center; background: #f9f9f9; font-weight: bold; }
    .col-cant { width: 90px; }
    
    .badge { padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    .bg-ok { background: #d4edda; color: #155724; }
    .bg-wait { background: #f8d7da; color: #721c24; }
</style>
"""

# --- PLANTILLA REGISTRO ---
REGISTRO_HTML = ESTILOS + """
<div class="container">
    <div class="nav"><a href="/buscar" class="btn btn-blue">🔍 BUSCAR VALE</a></div>
    <h2>Registro de Pedido de Materiales</h2>
    <form method="POST" action="/guardar_pedido">
        <div class="form-row">
            <div class="form-group">
                <label>Embarcación / Nave</label>
                <input type="text" name="embarcacion" required>
            </div>
            <div style="width: 150px;">
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
                    <th class="col-item">ITEM</th>
                    <th class="col-cant">CANT/UND</th>
                    <th>DESCRIPCIÓN</th>
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
        <button type="button" class="btn btn-add" onclick="agregarFila()">+ Agregar Fila</button>
        <button type="submit" class="btn btn-green">GRABAR Y GENERAR VALE</button>
    </form>
</div>

<script>
    let n = 5;
    function agregarFila() {
        n++;
        let tbody = document.getElementById('tabla-body');
        let fila = document.createElement('tr');
        fila.innerHTML = `
            <td class="col-item">${n}</td>
            <td><input type="text" name="cant_${n}" class="input-tabla"></td>
            <td><input type="text" name="desc_${n}" class="input-tabla"></td>
        `;
        tbody.appendChild(fila);
    }
</script>
"""

# --- PLANTILLA BUSQUEDA ---
BUSCAR_HTML = ESTILOS + """
<div class="container">
    <div class="nav"><a href="/" class="btn btn-blue">📝 NUEVO REGISTRO</a></div>
    <h2>Seguimiento de Vale</h2>
    <form method="GET" style="display: flex; gap: 10px; margin-bottom: 20px;">
        <input type="number" name="id" placeholder="Ingrese N° de Vale" style="flex: 1;" required>
        <button type="submit" class="btn btn-blue">BUSCAR</button>
    </form>

    {% if pedido %}
    <div style="border: 2px solid #1e3c72; padding: 15px; border-radius: 8px; position: relative;">
        <div onclick="loginAdm({{ pedido.id }})" style="position: absolute; right: 10px; top: 10px; cursor: pointer; color: #ccc; font-size: 11px;">ADM</div>
        <h3 style="margin-top: 0;">VALE #{{ pedido.id }}</h3>
        <p style="font-size: 13px; margin: 5px 0;"><b>FECHA:</b> {{ pedido.fecha }} | <b>NAVE:</b> {{ pedido.embarcacion }}</p>
        <p style="font-size: 13px; margin: 5px 0;"><b>SOLICITANTE:</b> {{ pedido.solicitado_por }} | <b>PRIORIDAD:</b> {{ pedido.prioridad }}</p>
        <hr>
        <p style="font-size: 13px;"><b>PEDIDO COMPRA:</b> {{ pedido.pedido_compra or '---' }}</p>
        <p style="font-size: 13px;"><b>SEDE:</b> {{ pedido.sede or '---' }}</p>
        
        <table>
            <thead>
                <tr>
                    <th style="width: 40px;">#</th>
                    <th style="width: 70px;">CANT</th>
                    <th>DESCRIPCIÓN</th>
                    <th style="width: 90px;">ESTADO</th>
                </tr>
            </thead>
            <tbody>
                {% for m in materiales %}
                <tr>
                    <td class="col-item">{{ m.item }}</td>
                    <td style="text-align: center;">{{ m.cantidad }}</td>
                    <td style="padding: 5px;">{{ m.descripcion }}</td>
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
    {% elif error %}
    <p style="color: red; font-weight: bold;">{{ error }}</p>
    {% endif %}
</div>
<script>
    function loginAdm(id) {
        let clave = prompt("Clave de Administrador:");
        if (clave === "Kvnex123") { window.location.href = "/admin/" + id; }
    }
</script>
"""

# --- PLANTILLA ADMIN ---
ADMIN_HTML = ESTILOS + """
<div class="container" style="background: #2c3e50; color: white;">
    <h2>Panel ADM - Vale #{{ pedido.id }}</h2>
    <form method="POST">
        <label style="color: white;">PEDIDOS DE COMPRA (Separados por coma)</label>
        <input type="text" name="pedido_compra" value="{{ pedido.pedido_compra or '' }}">
        <br><br>
        <label style="color: white;">SEDE / DESTINO</label>
        <input type="text" name="sede" value="{{ pedido.sede or '' }}">
        
        <table style="background: white; color: black; margin-top: 20px;">
            <thead>
                <tr>
                    <th style="width: 40px;">#</th>
                    <th>DESCRIPCIÓN</th>
                    <th style="width: 60px;">OK</th>
                </tr>
            </thead>
            <tbody>
                {% for m in materiales %}
                <tr>
                    <td class="col-item">{{ m.item }}</td>
                    <td style="padding-left: 10px;">{{ m.descripcion }}</td>
                    <td style="text-align: center;">
                        <input type="checkbox" name="mat_{{ m.id }}" style="transform: scale(1.3);" {{ 'checked' if m.entregado }}>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <button type="submit" class="btn btn-green">💾 GUARDAR CAMBIOS</button>
        <div style="text-align: center; margin-top: 10px;">
            <a href="/buscar?id={{ pedido.id }}" style="color: #ccc; text-decoration: none; font-size: 12px;">← Volver</a>
        </div>
    </form>
</div>
"""

# --- RUTAS DE FLASK ---

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

    # Recorremos los inputs dinámicos
    item_n = 1
    for key in f.keys():
        if key.startswith('desc_'):
            idx = key.split('_')[1]
            cant = f.get(f'cant_{idx}', '').strip()
            desc = f.get(f'desc_{idx}', '').strip()
            if desc: # Solo guardamos si hay descripción
                cursor.execute("INSERT INTO materiales (pedido_id, item, cantidad, descripcion) VALUES (?,?,?,?)",
                               (pedido_id, item_n, cant, desc))
                item_n += 1
    conn.commit()
    conn.close()
    return f"""<script>alert('Vale N° {pedido_id} generado correctamente'); window.location.href='/';</script>"""

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
    if pedido: return render_template_string(BUSCAR_HTML, pedido=pedido, materiales=materiales)
    return render_template_string(BUSCAR_HTML, error="Vale no encontrado.")

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
            st = 1 if request.form.get(f"mat_{m['id']}") else 0
            cursor.execute("UPDATE materiales SET entregado = ? WHERE id = ?", (st, m['id']))
        conn.commit()
        conn.close()
        return redirect(url_for('buscar', id=p_id))
    
    pedido = cursor.execute("SELECT * FROM pedidos WHERE id = ?", (p_id,)).fetchone()
    materiales = cursor.execute("SELECT * FROM materiales WHERE pedido_id = ? ORDER BY item", (p_id,)).fetchall()
    conn.close()
    return render_template_string(ADMIN_HTML, pedido=pedido, materiales=materiales)

if __name__ == "__main__":
    app.run(debug=True)
