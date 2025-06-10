from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from reconocimiento import cargar_estudiantes, reconocer_estudiante, registrar_estudiante

app = Flask(__name__)

# Precargar los datos al iniciar
estudiantes_precargados = cargar_estudiantes()

@app.route('/reconocer', methods=['POST'])
def reconocer():
    if 'imagen' not in request.files:
        return jsonify({"error": "No se envió ninguna imagen"}), 400

    imagen = request.files['imagen']
    ruta = "imagen_recibida.jpg"
    imagen.save(ruta)

    resultado = reconocer_estudiante(ruta, estudiantes_precargados)
    return jsonify(resultado)

@app.route('/recargar', methods=['POST'])
def recargar():
    global estudiantes_precargados
    estudiantes_precargados = cargar_estudiantes()
    return jsonify({"status": "ok", "mensaje": "Datos recargados desde la base de datos"})

@app.route('/registrar', methods=['POST'])
def registrar():
    if 'imagen' not in request.files:
        return jsonify({"error": "No se envió ninguna imagen"}), 400

    campos = ['id_estudiante', 'nombres', 'apellidos', 'correo', 'requisitoriado']
    for campo in campos:
        if campo not in request.form:
            return jsonify({"error": f"Falta el campo requerido: {campo}"}), 400

    datos = {
        "id_estudiante": request.form['id_estudiante'],
        "nombres": request.form['nombres'],
        "apellidos": request.form['apellidos'],
        "correo": request.form['correo'],
        "requisitoriado": request.form['requisitoriado'].strip().lower() == 's',
        "imagen": request.files['imagen']
    }

    resultado = registrar_estudiante(datos)
    return jsonify(resultado)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
