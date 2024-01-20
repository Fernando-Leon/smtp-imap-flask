from flask import Flask, render_template, request, redirect, url_for
import smtplib
import imaplib
from flask import jsonify
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback

import email
from email.header import decode_header
from email.utils import parseaddr

app = Flask(__name__)

# Configuración del servidor SMTP de Gmail
smtp_server = "smtp.gmail.com"
smtp_port = 587  # Puerto de Gmail
usuario_correo = "testpruebascorreotest@gmail.com"
contrasena_correo = "jiie dvza pngx padt"

app.static_folder = 'static'

# Configuración IMAP
imap_server = "imap.gmail.com"
usuario = "testpruebascorreotest@gmail.com"
contrasena = "jiie dvza pngx padt"

def obtener_cuerpo_mensaje(mensaje):
    """Obtener el cuerpo del mensaje, considerando mensajes multipart."""
    if mensaje.is_multipart():
        for parte in mensaje.walk():
            if parte.get_content_type() == "text/plain":
                return parte.get_payload(decode=True).decode("utf-8")
    else:
        return mensaje.get_payload(decode=True).decode("utf-8")

@app.route('/')
def mostrar_correos():
    # Conexión al servidor IMAP
    conexion = imaplib.IMAP4_SSL(imap_server)

    # Autenticación
    conexion.login(usuario, contrasena)

    # Seleccionar el buzón (inbox en este caso)
    conexion.select("inbox")

    # Buscar todos los correos electrónicos en el buzón
    resultado, mensajes = conexion.search(None, "ALL")

    correos = []

    if resultado == "OK":
        # Obtener la lista de ID de mensajes
        lista_mensajes = mensajes[0].split()


        # Iterar sobre cada mensaje
        for mensaje_id in lista_mensajes:
            
            # Obtener el correo electrónico completo
            resultado, datos_mensaje = conexion.fetch(mensaje_id, "(RFC822)")
            mensaje_raw = datos_mensaje[0][1]

            # Parsear el correo electrónico
            mensaje = email.message_from_bytes(mensaje_raw)

            # Obtener el asunto del correo
            asunto, encoding = decode_header(mensaje["Subject"])[0]
            if isinstance(asunto, bytes):
                asunto = asunto.decode(encoding if encoding is not None else "utf-8")

            # Obtener el cuerpo del mensaje
            cuerpo_mensaje = obtener_cuerpo_mensaje(mensaje)

            # Obtener el nombre del remitente utilizando parseaddr
            remitente_nombre, remitente_direccion = parseaddr(mensaje["From"])

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

    # Cerrar la conexión
    conexion.logout()

    # Renderizar la plantilla HTML con la lista de correos
    return render_template('index.html', correos=correos)

@app.route('/obtener_correo/<correo_id>')
def obtener_correo(correo_id):
    try:
        # Connect to the IMAP server
        conexion = imaplib.IMAP4_SSL(imap_server)
        conexion.login(usuario, contrasena)

        # Select the mailbox (inbox in this case)
        conexion.select("inbox")

        # Fetch details of the email with the provided ID
        resultado, datos_mensaje = conexion.fetch(correo_id, "(RFC822)")
        mensaje_raw = datos_mensaje[0][1]

        # Parse the email
        mensaje = email.message_from_bytes(mensaje_raw)

        # Get email details
        asunto = decode_header(mensaje["Subject"])[0][0]
        if isinstance(asunto, bytes):
            asunto = asunto.decode("utf-8")
        else:
            asunto = str(asunto)

        cuerpo_mensaje = obtener_cuerpo_mensaje(mensaje)

        remitente_nombre, remitente_direccion = parseaddr(mensaje["From"])
        fecha = mensaje["Date"]

        # Close the connection
        conexion.logout()

        # Return email details as JSON
        correo = {
            "asunto": asunto,
            "remitente": remitente_nombre,
            "fecha": fecha,
            "contenido": cuerpo_mensaje,
        }

        return jsonify(correo)

    except Exception as e:
        # Print the exception traceback for debugging
        traceback.print_exc()

        # Handle exceptions (e.g., connection error, email not found, etc.)
        return jsonify({"error": str(e)}), 500  # Return a JSON response with the error message and status code 500
    
@app.route('/nuevo_correo', methods=['GET', 'POST'])
def nuevo_correo():
    if request.method == 'POST':
        destinatario = request.form['destinatario']
        asunto = request.form['asunto']
        contenido = request.form['contenido']

        # Lógica para enviar el correo
        enviar_correo(destinatario, asunto, contenido)

        # Redirigir a la página principal después de enviar el correo
        return redirect(url_for('mostrar_correos'))

    return render_template('nuevo_correo.html')

def enviar_correo(destinatario, asunto, contenido):
    # Configurar el correo
    mensaje = MIMEMultipart()
    mensaje['From'] = usuario_correo
    mensaje['To'] = destinatario
    mensaje['Subject'] = asunto
    mensaje.attach(MIMEText(contenido, 'plain'))

    # Configurar la conexión al servidor SMTP
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        # Iniciar sesión en el servidor
        server.starttls()
        server.login(usuario_correo, contrasena_correo)

        # Enviar el correo
        server.sendmail(usuario_correo, destinatario, mensaje.as_string())

if __name__ == '__main__':
    app.run(debug=True)
