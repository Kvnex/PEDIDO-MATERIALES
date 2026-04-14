from flask import Flask, render_template_string, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret_key_pro"

# --- CONFIGURACIÓN DE BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('pedidos.db')
    cursor = conn.cursor()
    # Tabla de Pedidos
    cursor.execute('''CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        embarcacion TEXT,
        prioridad TEXT,
        solicitado_por TEXT,
        pedido_compra TEXT,
        sede TEXT
    )''')
    # Tabla de Materiales
    cursor.execute('''CREATE TABLE IF NOT EXISTS materiales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        nombre TEXT,
        entregado INTEGER DEFAULT 0,
        FOREIGN KEY(pedido_id) REFERENCES pedidos(id)
    )''')
    conn.commit()
    conn.close()

init_db()

# --- PLANTILLA HTML (TODO EN UNO PARA TU COMODIDAD) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Sistema de Pedidos Kvnex</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f4f7f6; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h2 { color: #2a5298; border-bottom: 2px solid #2a5298; padding-bottom: 10px; }
        .nav { margin-bottom: 20px; display: flex; gap: 10px; }
        .btn { padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; font-weight: bold; }
        .btn-blue { background: #2a5298; color: white; }
        .btn-green { background: #28a745; color: white; }
        .btn-adm { background: #6c757d; color: white; font-size: 0.8em; }
        input, select, textarea { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        .material-row { display: flex; gap: 10px; margin-bottom: 5px; }
        .card { border: 1px solid #ddd; padding: 15px; border-radius: 8px; margin-top: 15px; background: #fafafa; }
        .status-badge { padding: 5px 10px; border-radius: 4px; font-size: 0.9em; }
        .entregado { background: #d4edda; color: #155724; }
        .pendiente { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="/" class="btn btn-blue">📝 Registrar Pedido</a>
            <a href="/buscar" class="btn btn-blue">🔍 Buscar Vale</a>
        </div>

        {% if section == 'registro' %}
        <h2>Registrar Nuevo Pedido</h2>
        <form method="POST" action="/guardar_pedido">
            <label>Embarcación:</label>
            <input type="text" name="embarcacion" required>
            <label>Prioridad:</label>
            <select name="prioridad">
                <option value="NORMAL">NORMAL</option>
                <option value="URGENTE">URGENTE</option>
            </select>
            <label>Solicitado por:</label>
            <input type="text" name="solicitado" required>
            
            <label>Materiales (escriba uno por línea):</label>
            <textarea name="materiales" rows="5" placeholder="Ejemplo:&#10;Pintura Azul&#10;Rodillos 9pulg&#10;Solvente" required></textarea>
            
            <button type="submit" class="btn btn-green">🚀 Enviar Pedido</button>
        </form>

        {% elif section == 'exito' %}
        <div style="text-align:center; padding: 40px;">
            <h1 style="color: #28a745;">✅ ¡Registrado!</h1>
            <p>El número de vale generado es: <strong>#{{ id_generado }}</strong></p>
            <a href="/" class="btn btn-blue">Registrar otro pedido</a>
        </div>

        {% elif section == 'buscar' %}
        <h2>Buscar Pedido</h2>
        <form method="GET">
            <input type="number" name="id" placeholder="Ingrese N° de Vale" required>
            <button type="submit" class="btn btn-blue">Buscar</button>
        </form>

        {% if pedido %}
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3>Vale #{{ pedido.id }}</h3>
                <button onclick="loginAdm({{ pedido.id }})" class="btn btn-adm">ADM</button>
            </div>
            <p><b>Fecha:</b> {{ pedido.fecha }}</p>
            <p><b>Embarcación:</b> {{ pedido.embarcacion }}</p>
            <p><b>Prioridad:</b> {{ pedido.prioridad }}</p>
            <p><b>Solicitado por:</b> {{ pedido.solicitado_por }}</p>
            <p><b>Pedido de Compra:</b> {{ pedido.pedido_compra or 'Pendiente' }}</p>
            <p><b>Sede:</b> {{ pedido.sede or 'Pendiente' }}</p>
            <hr>
            <h4>Materiales:</h4>
            <ul>
                {% for m in materiales %}
                <li>
                    {{ m.nombre }} 
                    <span class="status-badge {{ 'entregado' if m.entregado else 'pendiente' }}">
                        {{ 'ENTREGADO' if m.entregado else 'PENDIENTE' }}
                    </span>
                </li>
                {% endfor %}
            </ul>
        </div>
        {% elif error %}
        <p style="color:red;">{{ error }}</p>
        {% endif %}
        {% endif %}
    </div>

    <script>
        function loginAdm(id) {
            let pass = prompt("Ingrese clave de administrador:");
            if (pass === "Kvnex123") {
                window.location.href = "/admin/" + id;
            } else if (pass != null) {
                alert("Clave incorrecta");
            }
        }
    </script>
</body>
</html>
"""

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Panel ADM - Pedido #{{ pedido.id }}</title>
    <style>
        body { font-family: sans-serif; padding: 20px; background: #2c3e50; color: white; }
        .box { max-width: 600px; margin: auto; background: white; color: #333; padding: 20px; border-radius: 10px; }
        .btn-save { background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%; font-size: 1.1em; }
    </style>
</head>
<body>
    <div class="box">
        <h2>Administrar Pedido #{{ pedido.id }}</h2>
        <form method="POST">
            <label><b>Pedido de Compra (Historial/Números):</b></label>
            <textarea name="pedido_compra" placeholder="Ej: PC-001, PC-045...">{{ pedido.pedido_compra }}</textarea>
            
            <label><b>Sede (Historial/Destinos):</b></label>
            <textarea name="sede" placeholder="Ej: Chimbote, Callao...">{{ pedido.sede }}</textarea>
            
            <h4>Checklist de Entrega:</h4>
            {% for m in materiales %}
            <div style="margin-bottom: 10px;">
                <input type="checkbox" name="mat_{{ m.id }}" style="width: auto;" {{ 'checked' if m.entregado }}>
                {{ m.nombre }}
            </div>
            {% endfor %}
            
            <button type="submit" class="btn-save">Grabar Cambios</button>
        </form>
        <br>
        <a href="/buscar?id={{ pedido.id }}">Volver atrás</a>
    </div>
</body>
</html>
"""

# --- RUTAS ---

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, section='registro')

@app.route("/guardar_pedido", methods=["POST"])
def guardar_pedido():
    embarcacion = request.form['embarcacion']
    prioridad = request.form['prioridad']
    solicitado = request.form['solicitado']
    materiales_texto = request.form['materiales'].split('\n')
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = sqlite3.connect('pedidos.db')
    cursor = conn.cursor()
    
    # Insertar Pedido
    cursor.execute("INSERT INTO pedidos (fecha, embarcacion, prioridad, solicitado_por) VALUES (?,?,?,?)",
                   (fecha_actual, embarcacion, prioridad, solicitado))
    pedido_id = cursor.lastrowid

    # Insertar Materiales
    for mat in materiales_texto:
        if mat.strip():
            cursor.execute("INSERT INTO materiales (pedido_id, nombre) VALUES (?,?)", (pedido_id, mat.strip()))
    
    conn.commit()
    conn.close()
    return render_template_string(HTML_TEMPLATE, section='exito', id_generado=pedido_id)

@app.route("/buscar")
def buscar():
    pedido_id = request.args.get('id')
    if not pedido_id:
        return render_template_string(HTML_TEMPLATE, section='buscar')
    
    conn = sqlite3.connect('pedidos.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    pedido = cursor.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    materiales = cursor.execute("SELECT * FROM materiales WHERE pedido_id = ?", (pedido_id,)).fetchall()
    conn.close()

    if pedido:
        return render_template_string(HTML_TEMPLATE, section='buscar', pedido=pedido, materiales=materiales)
    else:
        return render_template_string(HTML_TEMPLATE, section='buscar', error="Pedido no encontrado")

@app.route("/admin/<int:pedido_id>", methods=["GET", "POST"])
def admin_panel(pedido_id):
    conn = sqlite3.connect('pedidos.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == "POST":
        # Actualizar Pedido de Compra y Sede
        pc = request.form.get('pedido_compra')
        sede = request.form.get('sede')
        cursor.execute("UPDATE pedidos SET pedido_compra = ?, sede = ? WHERE id = ?", (pc, sede, pedido_id))
        
        # Actualizar Checks de Materiales
        materiales = cursor.execute("SELECT id FROM materiales WHERE pedido_id = ?", (pedido_id,)).fetchall()
        for m in materiales:
            is_checked = 1 if request.form.get(f"mat_{m['id']}") else 0
            cursor.execute("UPDATE materiales SET entregado = ? WHERE id = ?", (is_checked, m['id']))
        
        conn.commit()
        conn.close()
        return redirect(url_for('buscar', id=pedido_id))

    pedido = cursor.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    materiales = cursor.execute("SELECT * FROM materiales WHERE pedido_id = ?", (pedido_id,)).fetchall()
    conn.close()
    return render_template_string(ADMIN_TEMPLATE, pedido=pedido, materiales=materiales)

if __name__ == "__main__":
    app.run(debug=True)
