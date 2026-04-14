from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "kvnex_marine_key"

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

# --- ESTILOS CSS CON "VIDA" (MARÍTIMO MODERNO) ---
ESTILOS_VIVOS = """
<style>
    /* Fondo animado sutil */
    body { 
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; 
        margin: 0; 
        padding: 20px;
        min-height: 100vh;
        background: linear-gradient(-45deg, #1e3c72, #2a5298, #2193b0, #6dd5ed);
        background-size: 400% 400%;
        animation: gradientAnimation 15s ease infinite;
        display: flex;
        justify-content: center;
        align-items: flex-start;
    }

    @keyframes gradientAnimation {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Contenedor estilo "Cristal" (Glassmorphism) */
    .container { 
        max-width: 850px; 
        width: 100%;
        background: rgba(255, 255, 255, 0.9); 
        padding: 30px; 
        border-radius: 16px; 
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); 
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
        box-sizing: border-box;
    }

    h2 { 
        color: #1e3c72; 
        margin-top: 0; 
        border-bottom: 3px solid #2a5298; 
        padding-bottom: 10px; 
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    h3 { color: #2a5298; margin-top: 20px; margin-bottom: 10px;}

    .nav { margin-bottom: 20px; text-align: right; }
    
    /* Botones más vivos */
    .btn { 
        padding: 10px 20px; 
        border: none; 
        border-radius: 8px; 
        cursor: pointer; 
        text-decoration: none; 
        font-weight: bold; 
        font-size: 14px; 
        display: inline-block; 
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,0.3); }

    .btn-blue { background: #2a5298; color: white; }
    .btn-blue:hover { background: #1e3c72; }

    .btn-green { 
        background: #27ae60; 
        color: white; 
        width: 100%; 
        font-size: 18px; 
        margin-top: 25px; 
        padding: 15px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .btn-green:hover { background: #219150; }

    .btn-add { background: #f39c12; color: white; margin-top: 15px; }
    .btn-add:hover { background: #d3840b; }
    
    /* Formularios */
    .form-row { display: flex; gap: 20px; margin-bottom: 15px; }
    .form-group { flex: 1; }
    label { font-size: 12px; font-weight: bold; color: #555; display: block; text-transform: uppercase; margin-bottom: 5px; letter-spacing: 0.5px;}
    
    input[type="text"], input[type="number"], select { 
        width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; box-sizing: border-box; font-size: 15px; 
        transition: border-color 0.3s ease;
        background-color: rgba(255,255,255,0.8);
    }
    input[type="text"]:focus, input[type="number"]:focus, select:focus { 
        border-color: #6dd5ed; outline: none; background-color: #fff;
    }

    /* Tabla compacta y limpia */
    table { width: 100%; border-collapse: collapse; margin-top: 15px; table-layout: fixed; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);}
    th { background: #f2f2f2; font-size: 11px; border: 1px solid #ddd; padding: 10px; color: #333; text-transform: uppercase;}
    td { border: 1px solid #ddd; padding: 0; background: white; }
    
    .input-tabla { 
        width: 100%; border: none; padding: 12px; box-sizing: border-box; outline: none; font-size: 15px; background: transparent;
    }
    .input-tabla:focus { background: #e0f7fa; }
    
    .col-item { width: 50px; text-align: center; background: #f9f9f9; font-weight: bold; color: #1e3c72;}
    .col-cant { width: 100px; }
    
    /* Estados */
    .badge { padding: 5px 10px; border-radius: 20px; font-size: 11px; font-weight: bold; text-transform: uppercase;}
    .bg-ok { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .bg-wait { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }

    /* Panel Admin */
    .admin-container { background: rgba(44, 62, 80, 0.95); color: white; }
    .admin-container h2 { color: #6dd5ed; border-bottom-color: #6dd5ed; }
    .admin-container label { color: #ccc; }
    .admin-container table td { background: #fff; color: #000; }
</style>
"""

# --- PLANTILLA REGISTRO ---
REGISTRO_HTML = ESTILOS_VIVOS + """
<div class="container">
    <div class="nav"><a href="/buscar" class="btn btn-blue">🔍 BUSCAR VALE EXISTENTE</a></div>
    <h2>Registro de Pedido de Materiales</h2>
    <form method="POST" action="/guardar_pedido">
        <div class="form-row">
            <div class="form-group">
                <label>Embarcación / Nave</label>
                <input type="text" name="embarcacion" required>
            </div>
            <div style="width: 180px;">
                <label>Prioridad</label>
                <select name="prioridad">
                    <option value="NORMAL">🟢 NORMAL</option>
                    <option value="URGENTE">🔴 URGENTE</option>
                </select>
            </div>
        </div>
        <div class="form-group">
            <label>Solicitado por (Nombre Completo)</label>
            <input type="text" name="solicitado" required>
        </div>

        <h3>Lista de Materiales Solicitados</h3>
        <table>
            <thead>
                <tr>
                    <th class="col-item">ITEM</th>
                    <th class="col-cant">CANT / UND</th>
                    <th>DESCRIPCIÓN DETALLADA</th>
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
        <div style="text-align: right;">
            <button type="button" class="btn btn-add" onclick="agregarFila()">+ Añadir Fila</button>
        </div>
        <button type="submit" class="btn btn-green">⚓ GRABAR Y GENERAR VALE CORRELATIVO</button>
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
BUSCAR_HTML = ESTILOS_VIVOS + """
<div class="container">
    <div class="nav"><a href="/" class="btn btn-blue">📝 REGISTRAR NUEVO PEDIDO</a></div>
    <h2>Seguimiento de Vale</h2>
    <form method="GET" style="display: flex; gap: 10px; margin-bottom: 25px; background: rgba(0,0,0,0.05); padding: 15px; border-radius: 8px;">
        <input type="number" name="id" placeholder="Ingrese Número de Vale a buscar..." style="flex: 1;" required>
        <button type="submit" class="btn btn-blue" style="font-size: 16px;">🔍 BUSCAR</button>
    </form>

    {% if pedido %}
    <div style="border: 2px solid #2a5298; padding: 20px; border-radius: 12px; position: relative; background: rgba(255,255,255,0.5);">
        <div onclick="loginAdm({{ pedido.id }})" style="position: absolute; right: 15px; top: 15px; cursor: pointer; color: #aaa; font-size: 12px; font-weight:bold;">[ ADM ]</div>
        <h1 style="margin-top: 0; color: #1e3c72;">VALE N° {{ pedido.id }}</h1>
        
        <div class="form-row" style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #eee;">
            <div style="font-size: 14px; line-height: 1.6;">
                <b>FECHA REGISTRO:</b> {{ pedido.fecha }}<br>
                <b>EMBARCACIÓN:</b> {{ pedido.embarcacion }}
            </div>
            <div style="font-size: 14px; line-height: 1.6; text-align: right; flex:1;">
                <b>SOLICITANTE:</b> {{ pedido.solicitado_por }}<br>
                <b>PRIORIDAD:</b> 
                <span style="font-weight:bold; color: {{ 'red' if pedido.prioridad == 'URGENTE' else 'green' }}">
                    {{ pedido.prioridad }}
                </span>
            </div>
        </div>

        <div class="form-row" style="margin-top: 15px; gap: 10px;">
            <div style="background: #e0f7fa; padding: 10px; border-radius: 8px; flex:1; border: 1px solid #b2ebf2;">
                <b style="color: #006064; font-size:12px;">PEDIDO(S) COMPRA:</b><br>
                <span style="font-size: 16px; font-weight:bold;">{{ pedido.pedido_compra or 'PENDIENTE' }}</span>
            </div>
            <div style="background: #fff9c4; padding: 10px; border-radius: 8px; flex:1; border: 1px solid #fff9c4;">
                <b style="color: #827717; font-size:12px;">SEDE / DESTINO:</b><br>
                <span style="font-size: 16px; font-weight:bold;">{{ pedido.sede or 'PENDIENTE' }}</span>
            </div>
        </div>
        
        <h3 style="margin-top: 25px;">Detalle de Materiales</h3>
        <table>
            <thead>
                <tr>
                    <th style="width: 40px;">#</th>
                    <th style="width: 80px;">CANT</th>
                    <th>DESCRIPCIÓN</th>
                    <th style="width: 110px;">ESTADO</th>
                </tr>
            </thead>
            <tbody>
                {% for m in materiales %}
                <tr>
                    <td class="col-item">{{ m.item }}</td>
                    <td style="text-align: center; padding: 10px; font-weight:bold;">{{ m.cantidad }}</td>
                    <td style="padding: 10px; font-size: 14px;">{{ m.descripcion }}</td>
                    <td style="text-align: center;">
                        <span class="badge {{ 'bg-ok' if m.entregado else 'bg-wait' }}">
                            {{ '✅ ENTREGADO' if m.entregado else '⏳ PENDIENTE' }}
                        </span>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% elif error %}
    <div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; border: 1px solid #f5c6cb; font-weight: bold; text-align: center;">
        ⚠️ {{ error }}
    </div>
    {% endif %}
</div>
<script>
    function loginAdm(id) {
        let clave = prompt("Clave de Acceso Administrador:");
        if (clave === "Kvnex123") { window.location.href = "/admin/" + id; }
        else if (clave != null) { alert("Clave Incorrecta"); }
    }
</script>
"""

# --- PLANTILLA ADMIN ---
ADMIN_HTML = ESTILOS_VIVOS + """
<div class="container admin-container">
    <h2>Panel de Administración - Vale #{{ pedido.id }}</h2>
    <form method="POST">
        <div class="form-row">
            <div class="form-group">
                <label>Órdenes / Pedidos de Compra (PCs)</label>
                <input type="text" name="pedido_compra" value="{{ pedido.pedido_compra or '' }}">
            </div>
            <div class="form-group">
                <label>Sede o Destino de Entrega</label>
                <input type="text" name="sede" value="{{ pedido.sede or '' }}>
            </div>
        </div>
        
        <h3>Checklist de Entrega de Materiales</h3>
        <table style="margin-top: 10px;">
            <thead>
                <tr>
                    <th style="width: 40px;">#</th>
                    <th>DESCRIPCIÓN DEL MATERIAL</th>
                    <th style="width: 80px;">¿ENTREGADO?</th>
                </tr>
            </thead>
            <tbody>
                {% for m in materiales %}
                <tr>
                    <td class="col-item">{{ m.item }}</td>
                    <td style="padding: 12px; font-size: 14px;">{{ m.descripcion }}</td>
                    <td style="text-align: center;">
                        <input type="checkbox" name="mat_{{ m.id }}" style="transform: scale(1.5); cursor:pointer;" {{ 'checked' if m.entregado }}>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <button type="submit" class="btn btn-green">💾 GUARDAR CAMBIOS Y ACTUALIZAR ESTADOS</button>
        
        <div style="text-align: center; margin-top: 20px;">
            <a href="/buscar?id={{ pedido.id }}" style="color: #6dd5ed; text-decoration: none; font-size: 14px; font-weight:bold;">← Volver al Vale sin guardar</a>
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
    try:
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
        mensaje = f"✅ Vale N° {pedido_id} generado correctamente."
    except Exception as e:
        conn.rollback()
        mensaje = f"❌ Error al guardar: {str(e)}"
    finally:
        conn.close()
        
    return f"""<script>alert('{mensaje}'); window.location.href='/';</script>"""

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
    return render_template_string(BUSCAR_HTML, error="El Número de Vale especificado no existe en la base de datos.")

@app.route("/admin/<int:p_id>", methods=["GET", "POST"])
def admin_panel(p_id):
    conn = sqlite3.connect('pedidos.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if request.method == "POST":
        try:
            cursor.execute("UPDATE pedidos SET pedido_compra = ?, sede = ? WHERE id = ?", 
                           (request.form['pedido_compra'], request.form['sede'], p_id))
            mats = cursor.execute("SELECT id FROM materiales WHERE pedido_id = ?", (p_id,)).fetchall()
            for m in mats:
                st = 1 if request.form.get(f"mat_{m['id']}") else 0
                cursor.execute("UPDATE materiales SET entregado = ? WHERE id = ?", (st, m['id']))
            conn.commit()
        except:
            conn.rollback()
        finally:
            conn.close()
        return redirect(url_for('buscar', id=p_id))
    
    pedido = cursor.execute("SELECT * FROM pedidos WHERE id = ?", (p_id,)).fetchone()
    materiales = cursor.execute("SELECT * FROM materiales WHERE pedido_id = ? ORDER BY item", (p_id,)).fetchall()
    conn.close()
    return render_template_string(ADMIN_HTML, pedido=pedido, materiales=materiales)

if __name__ == "__main__":
    # Escucha en todas las IPs de la red local en el puerto 5000
    app.run(debug=True, host='0.0.0.0', port=5000)
