# Librerias necesarias
from flask import Flask, render_template, request, redirect, url_for
import smtplib # Libreria de SMTP para python
import imaplib # Libreria de IMAP para python
from flask import jsonify
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback
import email
from email.header import decode_header
from email.utils import parseaddr

app = Flask(__name__)
app.static_folder = 'static'

# Credenciales para el acceso a los servidores: SMTP - IMAP 
usuario = "testpruebascorreotest@gmail.com" # Direccion de tu correo electronico
password = "jiie dvza pngx padt" # Clave para la autenticaion de tu correo

# Configuración del servidor SMTP de Gmail
smtp_server = "smtp.gmail.com"
smtp_port = 587  # Puerto de Gmail

# Configuración IMAP
imap_server = "imap.gmail.com"
    
# Configuracion para mostrar los correos
@app.route('/')
def mostrar_correos():
    conexion = imaplib.IMAP4_SSL(imap_server)  # Conexión al servidor IMAP
    conexion.login(usuario, password) # Autenticación
    conexion.select("inbox") # Seleccionar el buzón
    resultado, mensajes = conexion.search(None, "ALL") # Buscar todos los correos electrónicos

    correos = []

    if resultado == "OK":
        lista_mensajes = mensajes[0].split() # Obtener la lista de ID de mensajes

        for mensaje_id in lista_mensajes:
            # Obtener el correo electrónico completo
            resultado, datos_mensaje = conexion.fetch(mensaje_id, "(RFC822)")
            mensaje_raw = datos_mensaje[0][1]

            mensaje = email.message_from_bytes(mensaje_raw) # Parsear el correo electrónico

            # Obtener el asunto del correo
            asunto, encoding = decode_header(mensaje["Subject"])[0]
            if isinstance(asunto, bytes):
                asunto = asunto.decode(encoding if encoding is not None else "utf-8")

            cuerpo_mensaje = obtener_cuerpo_mensaje(mensaje) # Obtener el cuerpo del mensaje

            # Obtener el nombre del remitente 
            remitente_nombre, direccion_remitente = parseaddr(mensaje["From"])

            # Guardamo el id del mensaje decodificado 
            mensaje_id = mensaje_id.decode("utf-8") if isinstance(mensaje_id, bytes) else mensaje_id
            mensaje_id = mensaje_id.replace("b'", "").replace("'", "") 

            # Agregar información del correo a la lista
            correos.append({
                "id": str(mensaje_id),
                "asunto": asunto,
                "remitente": remitente_nombre,
                "fecha": mensaje["Date"],
                "contenido": cuerpo_mensaje,
            })

    conexion.logout() # Cerrar la conexion

    return render_template('index.html', correos=correos) # Retornamos los resultados a nuestro index.html

# Configuracion para obtener un mail por su Id
@app.route('/obtener_correo/<correo_id>')
def obtener_correo(correo_id):
    try:
        conexion = imaplib.IMAP4_SSL(imap_server)
        conexion.login(usuario, password)
        conexion.select("inbox")

        # Obtenemos los datos del mensajej por medio de su Id
        resultado, datos_mensaje = conexion.fetch(correo_id, "(RFC822)")
        mensaje_raw = datos_mensaje[0][1]

        mensaje = email.message_from_bytes(mensaje_raw) 

        # Get email details
        asunto = decode_header(mensaje["Subject"])[0][0]
        if isinstance(asunto, bytes):
            asunto = asunto.decode("utf-8")
        else:
            asunto = str(asunto)

        cuerpo_mensaje = obtener_cuerpo_mensaje(mensaje)

        remitente_nombre = parseaddr(mensaje["From"])
        fecha = mensaje["Date"]

        correo = {
            "asunto": asunto,
            "remitente": remitente_nombre,
            "fecha": fecha,
            "contenido": cuerpo_mensaje,
        }

        conexion.logout()

        return jsonify(correo)
    
    # Manejamos una excepcion en caso de algun error
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500  
    
# Configuracion para enviar un correo
@app.route('/nuevo_correo', methods=['GET', 'POST'])
def nuevo_correo():
    if request.method == 'POST':
        destinatario = request.form['destinatario']
        asunto = request.form['asunto']
        contenido = request.form['contenido']

        # Configurar el correo
        mensaje = MIMEMultipart()
        mensaje['From'] = usuario
        mensaje['To'] = destinatario
        mensaje['Subject'] = asunto
        mensaje.attach(MIMEText(contenido, 'plain'))

        # Configurar la conexión al servidor SMTP
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            # Autenticion
            server.starttls()
            server.login(usuario, password)

            # Enviar el correo
            server.sendmail(usuario, destinatario, mensaje.as_string())

            # Redirigir a la página principal después de enviar el correo
            return redirect(url_for('mostrar_correos'))

    return render_template('nuevo_correo.html')

def obtener_cuerpo_mensaje(mensaje):
    """Obtener el cuerpo del mensaje, considerando mensajes multipart."""
    if mensaje.is_multipart():
        for parte in mensaje.walk():
            if parte.get_content_type() == "text/plain":
                return parte.get_payload(decode=True).decode("utf-8")
    else:
        return mensaje.get_payload(decode=True).decode("utf-8")

if __name__ == '__main__':
    app.run(debug=True)