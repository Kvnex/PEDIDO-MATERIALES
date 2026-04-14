from flask import Flask, render_template_string, request, redirect, url_for
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
app.secret_key = "kvnex_marine_key"

# === CONFIGURACIÓN DE SUPABASE ===
SUPABASE_URL = "https://uyibbpixwpaxwgcvvgka.supabase.co"
SUPABASE_KEY = "sb_secret_cSRWBgY1LfdXK9HdrKWbnQ_Wm1HRsVu"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- ESTILOS VISUALES ---
ESTILOS = """
<style>
    body { 
        font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; min-height: 100vh;
        background: linear-gradient(-45deg, #1e3c72, #2a5298, #2193b0, #6dd5ed);
        background-size: 400% 400%; animation: gradient 15s ease infinite;
        display: flex; justify-content: center;
    }
    @keyframes gradient { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
    .container { 
        max-width: 850px; width: 100%; background: rgba(255, 255, 255, 0.95); 
        padding: 25px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); backdrop-filter: blur(5px);
    }
    h2 { color: #1e3c72; border-bottom: 3px solid #1e3c72; padding-bottom: 10px; margin-top: 0; }
    .nav { margin-bottom: 20px; text-align: right; }
    .btn { padding: 10px 18px; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; font-weight: bold; font-size: 13px; transition: 0.3s; display: inline-block; }
    .btn-blue { background: #1e3c72; color: white; }
    .btn-green { background: #27ae60; color: white; width: 100%; font-size: 16px; margin-top: 20px; padding: 12px; border-radius: 8px; }
    .btn-add { background: #f39c12; color: white; margin-top: 10px; }
    .form-row { display: flex; gap: 15px; margin-bottom: 15px; }
    .form-group { flex: 1; }
    label { font-size: 11px; font-weight: bold; color: #444; display: block; text-transform: uppercase; margin-bottom: 4px; }
    input[type="text"], input[type="number"], select { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 14px; }
    table { width: 100%; border-collapse: collapse; margin-top: 15px; table-layout: fixed; background: white; }
    th { background: #f2f2f2; font-size: 11px; border: 1px solid #ddd; padding: 8px; color: #333; }
    td { border: 1px solid #ddd; padding: 0; }
    .input-tabla { width: 100%; border: none; padding: 10px; box-sizing: border-box; outline: none; font-size: 14px; background: transparent; }
    .col-item { width: 45px; text-align: center; background: #f9f9f9; font-weight: bold; color: #1e3c72; }
    .badge { padding: 5px 10px; border-radius: 12px; font-size: 11px; font-weight: bold; }
    .bg-ok { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .bg-wait { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .prio-urgente { background: #ffebee; color: #c62828; border: 1px solid #ef9a9a; }
    .prio-normal { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
</style>
"""

# --- PLANTILLAS HTML ---
REGISTRO_HTML = ESTILOS + """
<div class="container">
    <div class="nav"><a href="/buscar" class="btn btn-blue">🔍 BUSCAR VALE</a></div>
    <h2>Registro de Pedido</h2>
    <form method="POST" action="/guardar_pedido">
        <div class="form-row">
            <div class="form-group"><label>Embarcación</label><input type="text" name="embarcacion" required></div>
            <div style="width: 160px;"><label>Prioridad</label><select name="prioridad"><option value="NORMAL">🟢 NORMAL</option><option value="URGENTE">🔴 URGENTE</option></select></div>
        </div>
        <div class="form-group"><label>Solicitado por</label><input type="text" name="solicitado" required></div>
        <table>
            <thead><tr><th class="col-item">#</th><th style="width: 90px;">CANT/UND</th><th>DESCRIPCIÓN</th></tr></thead>
            <tbody id="tabla-body">
                {% for i in range(1, 6) %}
                <tr><td class="col-item">{{ i }}</td><td><input type="text" name="cant_{{ i }}" class="input-tabla"></td><td><input type="text" name="desc_{{ i }}" class="input-tabla"></td></tr>
                {% endfor %}
            </tbody>
        </table>
        <button type="button" class="btn btn-add" onclick="agregarFila()">+ Fila</button>
        <button type="submit" class="btn btn-green">⚓ GRABAR PEDIDO</button>
    </form>
</div>
<script>
    let n = 5;
    function agregarFila() {
        n++;
        let tbody = document.getElementById('tabla-body');
        let fila = document.createElement('tr');
        fila.innerHTML = `<td class="col-item">${n}</td><td><input type="text" name="cant_${n}" class="input-tabla"></td><td><input type="text" name="desc_${n}" class="input-tabla"></td>`;
        tbody.appendChild(fila);
    }
</script>
"""

BUSCAR_HTML = ESTILOS + """
<div class="container">
    <div class="nav"><a href="/" class="btn btn-blue">📝 NUEVO REGISTRO</a></div>
    <h2>Seguimiento de Vale</h2>
    <form method="GET" style="display: flex; gap: 10px; margin-bottom: 20px;">
        <input type="number" name="id" placeholder="N° de Vale" style="flex: 1;" required>
        <button type="submit" class="btn btn-blue">BUSCAR</button>
    </form>
    {% if pedido %}
    <div style="border: 2px solid #1e3c72; padding: 15px; border-radius: 10px; position: relative; background: #fff;">
        <div onclick="loginAdm({{ pedido.id }})" style="position: absolute; right: 10px; top: 10px; cursor: pointer; color: #bbb; font-size: 10px;">[ ADM ]</div>
        <h3>VALE #{{ pedido.id }}</h3>
        <p style="font-size: 13px; margin: 5px 0;"><b>FECHA:</b> {{ pedido.fecha }}</p>
        <p style="font-size: 13px; margin: 5px 0;"><b>EMBARCACION:</b> {{ pedido.embarcacion }}</p>
        <p style="font-size: 13px; margin: 8px 0;"><b>PRIORIDAD:</b> 
            <span class="badge {{ 'prio-urgente' if pedido.prioridad == 'URGENTE' else 'prio-normal' }}">
                {{ '🔴 URGENTE' if pedido.prioridad == 'URGENTE' else '🟢 NORMAL' }}
            </span>
        </p>
        <hr>
        <p style="font-size: 13px; margin: 5px 0;"><b>PEDIDO COMPRA:</b> {{ pedido.pedido_compra or '---' }}</p>
        <p style="font-size: 13px; margin: 5px 0;"><b>SEDE:</b> {{ pedido.sede or '---' }}</p>
        <table>
            <thead><tr><th style="width: 40px;">#</th><th style="width: 70px;">CANT</th><th>DESCRIPCIÓN</th><th style="width: 100px;">ESTADO</th></tr></thead>
            <tbody>
                {% for m in materiales %}
                <tr><td class="col-item">{{ m.item }}</td><td style="text-align: center; font-size: 13px;">{{ m.cantidad }}</td><td style="padding: 8px; font-size: 13px;">{{ m.descripcion }}</td>
                <td style="text-align: center;"><span class="badge {{ 'bg-ok' if m.entregado else 'bg-wait' }}">{{ 'ENTREGADO' if m.entregado else 'PENDIENTE' }}</span></td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% elif error %}<p style="color: red; font-weight: bold; text-align: center;">{{ error }}</p>{% endif %}
</div>
<script>function loginAdm(id) { if (prompt("Clave ADM:") === "Kvnex123") { window.location.href = "/admin/" + id; } }</script>
"""

ADMIN_HTML = ESTILOS + """
<div class="container" style="background: #2c3e50; color: white;">
    <h3>Gestión ADM - Vale #{{ pedido.id }}</h3>
    <form method="POST">
        <label style="color: white;">PEDIDOS DE COMPRA:</label><input type="text" name="pedido_compra" value="{{ pedido.pedido_compra or '' }}">
        <br><br><label style="color: white;">SEDE:</label><input type="text" name="sede" value="{{ pedido.sede or '' }}">
        <table style="background: white; color: black; margin-top: 15px;">
            <thead><tr><th style="width: 40px;">#</th><th>MATERIAL</th><th style="width: 60px;">OK</th></tr></thead>
            <tbody>
                {% for m in materiales %}
                <tr><td class="col-item">{{ m.item }}</td><td style="padding: 8px; font-size: 13px;">{{ m.descripcion }}</td>
                <td style="text-align: center;"><input type="checkbox" name="mat_{{ m.id }}" style="transform: scale(1.3);" {{ 'checked' if m.entregado }}></td></tr>
                {% endfor %}
            </tbody>
        </table>
        <button type="submit" class="btn btn-green">💾 GUARDAR CAMBIOS</button>
        <div style="text-align: center; margin-top: 15px;"><a href="/buscar?id={{ pedido.id }}" style="color: #ccc; text-decoration: none; font-size: 12px;">← Cancelar</a></div>
    </form>
</div>
"""

# --- RUTAS ---
@app.route("/")
def index(): return render_template_string(REGISTRO_HTML)

@app.route("/guardar_pedido", methods=["POST"])
def guardar_pedido():
    f = request.form
    tz_peru = timezone(timedelta(hours=-5))
    fecha = datetime.now(tz_peru).strftime("%d/%m/%Y %H:%M")
    
    res_p = supabase.table("pedidos").insert({"fecha": fecha, "embarcacion": f['embarcacion'], "prioridad": f['prioridad'], "solicitado_por": f['solicitado']}).execute()
    p_id = res_p.data[0]['id']
    
    mats = []
    item_n = 1
    for key in f.keys():
        if key.startswith('desc_'):
            idx = key.split('_')[1]
            c, d = f.get(f'cant_{idx}', '').strip(), f.get(f'desc_{idx}', '').strip()
            if d:
                mats.append({"pedido_id": p_id, "item": item_n, "cantidad": c, "descripcion": d})
                item_n += 1
    if mats: supabase.table("materiales").insert(mats).execute()
    return f"<script>alert('Vale N° {p_id} guardado correctamente'); window.location.href='/';</script>"

@app.route("/buscar")
def buscar():
    p_id = request.args.get('id')
    if not p_id: return render_template_string(BUSCAR_HTML)
    res_p = supabase.table("pedidos").select("*").eq("id", p_id).execute()
    if res_p.data:
        res_m = supabase.table("materiales").select("*").eq("pedido_id", p_id).order("item").execute()
        return render_template_string(BUSCAR_HTML, pedido=res_p.data[0], materiales=res_m.data)
    return render_template_string(BUSCAR_HTML, error="Vale no encontrado.")

@app.route("/admin/<int:p_id>", methods=["GET", "POST"])
def admin_panel(p_id):
    if request.method == "POST":
        supabase.table("pedidos").update({"pedido_compra": request.form['pedido_compra'], "sede": request.form['sede']}).eq("id", p_id).execute()
        res_m = supabase.table("materiales").select("id").eq("pedido_id", p_id).execute()
        for m in res_m.data:
            st = 1 if request.form.get(f"mat_{m['id']}") else 0
            supabase.table("materiales").update({"entregado": st}).eq("id", m['id']).execute()
        return redirect(url_for('buscar', id=p_id))
    
    res_p = supabase.table("pedidos").select("*").eq("id", p_id).execute()
    res_m = supabase.table("materiales").select("*").eq("pedido_id", p_id).order("item").execute()
    return render_template_string(ADMIN_HTML, pedido=res_p.data[0], materiales=res_m.data)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
