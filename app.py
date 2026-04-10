from flask import Flask, request
import pandas as pd

app = Flask(__name__)

# 🔥 EXCEL DESDE GITHUB
ruta_excel = "https://raw.githubusercontent.com/Kvnex/PEDIDO-MATERIALES/main/PEDIDOS.xlsx"

def generar_html(resultados=None):
    contenido = ""

    if resultados:
        if "error" in resultados:
            contenido = f"<p style='color:red; font-weight:bold;'>{resultados['error']}</p>"
        else:
            filas_html = ""

            for r in resultados:
                estado = r["estado"]

                if estado == "ATENDIDO":
                    color_class = "green"
                elif estado in ["PC", "EN CURSO"]:
                    color_class = "yellow"
                    estado = "EN CURSO"
                elif estado == "NO ATENDIDO":
                    color_class = "red"
                else:
                    color_class = "gray"

                filas_html += f"""
                <div class="resultado {color_class}">
                    <p><b>Vale:</b> {r['vale']}</p>
                    <p><b>Sede:</b> {r['sede']}</p>
                    <p><b>Embarcación:</b> {r['embarcacion']}</p>
                    <p><b>Programa:</b> {r['programa']}</p>
                    <p><b>Estado:</b> {estado}</p>
                </div>
                """

            contenido = filas_html

    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Consulta de Vales</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial;
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 0;
        }}

        .card {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            width: 400px;
            text-align: center;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }}

        input {{
            width: 80%;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #ccc;
            margin-bottom: 15px;
            font-size: 16px;
        }}

        button {{
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            background: #2a5298;
            color: white;
            font-weight: bold;
            cursor: pointer;
        }}

        .resultado {{
            margin-top: 15px;
            padding: 15px;
            border-radius: 10px;
            color: white;
            font-weight: bold;
        }}

        .green {{ background: #28a745; }}
        .yellow {{ background: #ffc107; color: black; }}
        .red {{ background: #dc3545; }}
        .gray {{ background: #6c757d; }}

        .leyenda {{
            margin-top: 20px;
        }}

        .leyenda div {{
            margin: 5px;
            padding: 5px;
            border-radius: 5px;
            color: white;
        }}
    </style>
</head>

<body>

<div class="card">
    <h2>🔍 Buscar Vale</h2>

    <form method="POST">
        <input name="vale" placeholder="Ingrese N° de Vale" required>
        <br>
        <button type="submit">Buscar</button>
    </form>

    {contenido}

    <div class="leyenda">
        <div class="green">ATENDIDO</div>
        <div class="yellow">EN CURSO</div>
        <div class="red">NO ATENDIDO</div>
    </div>

</div>

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        numero_vale = request.form["vale"]

        try:
            df = pd.read_excel(ruta_excel, header=None)

            # 🔥 BUSCAR VALES
            filas = df[df.iloc[:,1].astype(str) == str(numero_vale)]

            if not filas.empty:
                resultados = []

                for _, row in filas.iterrows():
                    resultados.append({
                        "vale": numero_vale,
                        "sede": row[4],          # ✅ Columna E
                        "embarcacion": row[2],   # Columna C
                        "programa": row[3],      # Columna D
                        "estado": str(row[5]).strip().upper()  # ✅ Columna F
                    })

                return generar_html(resultados)

            else:
                return generar_html({"error": "Vale no encontrado"})

        except Exception as e:
            return generar_html({"error": str(e)})

    return generar_html()

if __name__ == "__main__":
    app.run(debug=True)
