from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from reconocimiento import cargar_estudiantes, reconocer_estudiante, registrar_estudiante, obtener_estudiante_por_id
from reconocimiento import obtener_todos_los_estudiantes, actualizar_estudiante, eliminar_estudiante

app = Flask(__name__)


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

    if resultado.get("status") == "ok":
        global estudiantes_precargados
        estudiantes_precargados = cargar_estudiantes()

    return jsonify(resultado)

@app.route('/estudiantes', methods=['GET'])
def listar_estudiantes():
    estudiantes = obtener_todos_los_estudiantes()
    if isinstance(estudiantes, dict) and "error" in estudiantes:
        return jsonify(estudiantes), 500
    return jsonify(estudiantes)

@app.route('/estudiantes/<id_estudiante>', methods=['GET'])
def obtener_estudiante(id_estudiante):
    resultado = obtener_estudiante_por_id(id_estudiante)
    if resultado is None:
        return jsonify({"error": "Estudiante no encontrado"}), 404
    if isinstance(resultado, dict) and "error" in resultado:
        return jsonify(resultado), 500
    return jsonify(resultado)

@app.route('/estudiantes/<id_estudiante>', methods=['PUT'])
def modificar_estudiante(id_estudiante):
    data = request.get_json()
    campos = ['nombres', 'apellidos', 'correo', 'requisitoriado']
    if not all(campo in data for campo in campos):
        return jsonify({"error": "Faltan campos obligatorios"}), 400
    actualizado = actualizar_estudiante(id_estudiante, data)
    if isinstance(actualizado, dict):
        return jsonify(actualizado), 500
    if not actualizado:
        return jsonify({"error": "Estudiante no encontrado"}), 404
    
    global estudiantes_precargados
    estudiantes_precargados = cargar_estudiantes()

    return jsonify({"status": "ok", "mensaje": "Estudiante actualizado correctamente"})

@app.route('/estudiantes/<id_estudiante>', methods=['DELETE'])
def eliminar_estudiante_api(id_estudiante):
    resultado = eliminar_estudiante(id_estudiante)
    if isinstance(resultado, dict):
        return jsonify(resultado), 500
    if not resultado:
        return jsonify({"error": "Estudiante no encontrado"}), 404
    
    global estudiantes_precargados
    estudiantes_precargados = cargar_estudiantes()
    
    return jsonify({"status": "ok", "mensaje": "Estudiante eliminado correctamente"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
