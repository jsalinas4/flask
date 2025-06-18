import face_recognition
import pickle
import psycopg2
import os
from werkzeug.utils import secure_filename

def cargar_estudiantes():
    estudiantes = []
    try:
        conn = psycopg2.connect(
            host="dpg-d150l7p5pdvs73ep34t0-a.oregon-postgres.render.com",
            database="bd_estudiantes",
            user="bd_estudiantes_user",
            password="p8kt9BUdSQHRPtS17BE84goMpCmFSn12"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT id_estudiante, nombres, apellidos, correo, requisitoriado, kp FROM estudiantes")
        for id_est, nombres, apellidos, correo, requisitoriado, kp_blob in cursor.fetchall():
            try:
                encoding = pickle.loads(kp_blob)
                estudiantes.append({
                    "encoding": encoding,
                    "id": id_est,
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "correo": correo,
                    "requisitoriado": requisitoriado
                })
            except Exception:
                continue  
        cursor.close()
        conn.close()
    except Exception as e:
        print("Error al cargar estudiantes desde la base de datos:", e)
    return estudiantes

def reconocer_estudiante(ruta_imagen, estudiantes):
    try:
        imagen = face_recognition.load_image_file(ruta_imagen)
        face_encodings = face_recognition.face_encodings(imagen)
    except Exception as e:
        return {"status": "error", "mensaje": f"Error al procesar imagen: {str(e)}"}

    if not face_encodings:
        return {"status": "no_detectado", "mensaje": "No se detectó ningún rostro"}

    for encoding_detectado in face_encodings:
        encodings_bd = [est["encoding"] for est in estudiantes]
        matches = face_recognition.compare_faces(encodings_bd, encoding_detectado, tolerance=0.45)
        distances = face_recognition.face_distance(encodings_bd, encoding_detectado)

        if distances.size > 0:
            mejor_idx = distances.argmin()
            if matches[mejor_idx]:
                est = estudiantes[mejor_idx]
                return {
                    "status": "identificado",
                    "id_estudiante": est["id"],
                    "nombres": est["nombres"],
                    "apellidos": est["apellidos"],
                    "correo": est["correo"],
                    "requisitoriado": est["requisitoriado"]
                }

    return {"status": "desconocido", "mensaje": "No se encontró coincidencia"}


def registrar_estudiante(datos):
    try:
        imagen = datos['imagen']
        filename = secure_filename(imagen.filename)
        ruta_imagen = os.path.join("imagenes_temporales", filename)
        os.makedirs("imagenes_temporales", exist_ok=True)
        imagen.save(ruta_imagen)

        
        estudiantes = cargar_estudiantes()

        
        reconocimiento = reconocer_estudiante(ruta_imagen, estudiantes)
        if reconocimiento.get("status") == "identificado":
            os.remove(ruta_imagen)
            return {
                "status": "duplicado",
                "mensaje": f"Ya está registrado como: {reconocimiento['nombres']} {reconocimiento['apellidos']} (ID: {reconocimiento['id_estudiante']})"
            }

       
        imagen_cargada = face_recognition.load_image_file(ruta_imagen)
        encodings = face_recognition.face_encodings(imagen_cargada)

        if not encodings:
            os.remove(ruta_imagen)
            return {"error": "No se detectó rostro en la imagen"}

        encoding_serializado = pickle.dumps(encodings[0])

        imagen.seek(0)
        foto_binaria = imagen.read()

        conn = psycopg2.connect(
            host="dpg-d150l7p5pdvs73ep34t0-a.oregon-postgres.render.com",
            database="bd_estudiantes",
            user="bd_estudiantes_user",
            password="p8kt9BUdSQHRPtS17BE84goMpCmFSn12"
        )
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO estudiantes (id_estudiante, nombres, apellidos, correo, requisitoriado, foto, kp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            datos["id_estudiante"],
            datos["nombres"],
            datos["apellidos"],
            datos["correo"],
            datos["requisitoriado"],
            foto_binaria,
            encoding_serializado
        ))
        conn.commit()
        cursor.close()
        conn.close()

        os.remove(ruta_imagen)

        return {"status": "ok", "mensaje": "Estudiante registrado correctamente"}

    except Exception as e:
        try:
            os.remove(ruta_imagen)
        except:
            pass
        return {"error": f"Error al registrar estudiante: {str(e)}"}


# Obtener todos los estudiantes
def obtener_todos_los_estudiantes():
    estudiantes = []
    try:
        conn = psycopg2.connect(
            host="dpg-d150l7p5pdvs73ep34t0-a.oregon-postgres.render.com",
            database="bd_estudiantes",
            user="bd_estudiantes_user",
            password="p8kt9BUdSQHRPtS17BE84goMpCmFSn12"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT id_estudiante, nombres, apellidos, correo, requisitoriado FROM estudiantes")
        for fila in cursor.fetchall():
            estudiantes.append({
                "id_estudiante": fila[0],
                "nombres": fila[1],
                "apellidos": fila[2],
                "correo": fila[3],
                "requisitoriado": fila[4]
            })
        cursor.close()
        conn.close()
    except Exception as e:
        return {"error": str(e)}
    return estudiantes

# Obtener estudiante por ID
def obtener_estudiante_por_id(id_estudiante):
    try:
        conn = psycopg2.connect(
            host="dpg-d150l7p5pdvs73ep34t0-a.oregon-postgres.render.com",
            database="bd_estudiantes",
            user="bd_estudiantes_user",
            password="p8kt9BUdSQHRPtS17BE84goMpCmFSn12"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT id_estudiante, nombres, apellidos, correo, requisitoriado FROM estudiantes WHERE id_estudiante = %s", (id_estudiante,))
        fila = cursor.fetchone()
        cursor.close()
        conn.close()
        if fila:
            return {
                "id_estudiante": fila[0],
                "nombres": fila[1],
                "apellidos": fila[2],
                "correo": fila[3],
                "requisitoriado": fila[4]
            }
        else:
            return None
    except Exception as e:
        return {"error": str(e)}

# Actualizar estudiante
def actualizar_estudiante(id_estudiante, datos):
    try:
        conn = psycopg2.connect(
            host="dpg-d150l7p5pdvs73ep34t0-a.oregon-postgres.render.com",
            database="bd_estudiantes",
            user="bd_estudiantes_user",
            password="p8kt9BUdSQHRPtS17BE84goMpCmFSn12"
        )
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE estudiantes SET nombres=%s, apellidos=%s, correo=%s, requisitoriado=%s
            WHERE id_estudiante=%s
        """, (
            datos["nombres"],
            datos["apellidos"],
            datos["correo"],
            datos["requisitoriado"],
            id_estudiante
        ))
        conn.commit()
        actualizado = cursor.rowcount
        cursor.close()
        conn.close()
        return actualizado > 0
    except Exception as e:
        return {"error": str(e)}

# Eliminar estudiante
def eliminar_estudiante(id_estudiante):
    try:
        conn = psycopg2.connect(
            host="dpg-d150l7p5pdvs73ep34t0-a.oregon-postgres.render.com",
            database="bd_estudiantes",
            user="bd_estudiantes_user",
            password="p8kt9BUdSQHRPtS17BE84goMpCmFSn12"
        )
        cursor = conn.cursor()
        cursor.execute("DELETE FROM estudiantes WHERE id_estudiante = %s", (id_estudiante,))
        conn.commit()
        eliminado = cursor.rowcount
        cursor.close()
        conn.close()
        return eliminado > 0
    except Exception as e:
        return {"error": str(e)}
