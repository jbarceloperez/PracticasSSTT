# coding=utf-8

from http.cookiejar import Cookie
import socket
import selectors    #https://docs.python.org/3/library/selectors.html
import select
from ssl import SOL_SOCKET
import types        # Para definir el tipo de datos data
import argparse     # Leer parametros de ejecución
import os           # Obtener ruta y extension
from datetime import datetime, timedelta # Fechas de los mensajes HTTP
import time         # Timeout conexión
import sys          # sys.exit
import re           # Analizador sintáctico
import logging      # Para imprimir logs



BUFSIZE = 8192 # Tamaño máximo del buffer que se puede utilizar
TIMEOUT_CONNECTION = 20 # Timout para la conexión persistente
KEEPALIVE_TIMEOUT = 25  # Timeout HTTP
MAX_ACCESOS = 10

# Extensiones admitidas (extension, name in HTTP)
filetypes = {"gif":"image/gif", "jpg":"image/jpg", "jpeg":"image/jpeg", "png":"image/png", "htm":"text/htm", 
             "html":"text/html", "css":"text/css", "js":"text/js"}

# Configuración de logging
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s.%(msecs)03d] [%(levelname)-7s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger()

def make_header(codigo, tam):
    '''Crea la cadena de texto con la cabecera de la respuesta en función del código de estado.
    '''
    aux = '\r\nDate: ' + datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT\r\n') + 'Server: web.rugbycartagena78.org\r\nConnection: Keep-Alive\r\nKeep-Alive: timeout=' + str(KEEPALIVE_TIMEOUT) + '\r\nContent-Length: ' + str(tam) + '\r\nContent-Type: text/html\r\n\r\n'
    if codigo==200:     # OK
        # TODO acordarse de las cookies
        pass
    elif codigo==404:   # NOT FOUND
        logger.error("HTTP/1.1 404 NOT FOUND")
        return 'HTTP/1.1 404 Not Found' + aux
    elif codigo==403:   # FORBIDDEN
        logger.error("HTTP/1.1 403 FORBIDDEN")
        return 'HTTP/1.1 403 Forbidden' + aux
    elif codigo==400:   # BAD REQUEST
        logger.error("HTTP/1.1 400 BAD REQUEST")
        return 'HTTP/1.1 400 Bad Request' + aux
    elif codigo==405:   # METHOD NOT ALLOWED
        logger.error("HTTP/1.1 405 METHOD NOT ALLOWED")
        return "HTTP/1.1 405 Method Not Allowed" + aux
    elif codigo==505:   # HTTP VERSION NOT SUPPORTED
        logger.error("HTTP/1.1 505 VERSION NOT SUPPORTED")
        return 'HTTP/1.1 505 Version Not Supported' + aux
    else:
        logger.error("Error al construir el mensaje a enviar por el socket: código no válido.")
        return -1

def enviar_mensaje(cs, p, cookie, codigo):
    """ Esta función envía datos (data) a través del socket cs.
        Devuelve el número de bytes enviados.
    """
    # se crea un mensaje en función del código de estado de la respuesta
    if codigo==200:
        path = p
    else:
        path = str(codigo + ".html")
    f = open(path, "rb")
    tam = os.stat(path).st_size
    header = make_header(codigo, tam)
    if header==-1:  # fallo en la creación de la cabecera: código no válido
        return -1
    logger.debug("Sending " + str(codigo) + " message:\n" + header)
    header = header.encode()
    msg = f.read(BUFSIZE)   # se lee con un buffer de tamaño BUFSIZE
    # se envia la cabecera + el contenido del archivo html
    aux = header + msg
    enviado = 0
    # se envia con un bucle, de manera que mientras queden datos en el buffer aux se sigan enviando por el socket s.
    while(aux):
        enviado = enviado + cs.send(aux)
        aux = f.read(BUFSIZE)        
    f.close()
    return enviado  # devuelve el número de bytes enviados 


def recibir_mensaje(cs):
    """ Esta función recibe datos a través del socket cs
        Leemos la información que nos llega. recv() devuelve un string con los datos.
    """
    aux = cs.recv(BUFSIZE)  # no es necesario tratar lecturas parciales para este tipo de mensajes entrantes tan pequeños, digo yo
    # TODO cadena vacía es fin de conexión? manejar eso?
    return aux.decode()


def cerrar_conexion(cs):
    """ Esta función cierra una conexión activa.
    """
    cs.close()


def process_cookies(headers,  cs):
    """ Esta función procesa la cookie cookie_counter
        1. Se analizan las cabeceras en headers para buscar la cabecera Cookie
        2. Una vez encontrada una cabecera Cookie se comprueba si el valor es cookie_counter
        3. Si no se encuentra cookie_counter , se devuelve 1
        4. Si se encuentra y tiene el valor MAX_ACCESSOS se devuelve MAX_ACCESOS
        5. Si se encuentra y tiene un valor 1 <= x < MAX_ACCESOS se incrementa en 1 y se devuelve el valor
    """
    pass

def check_request(cs, lineas, webroot):
    ''' Analizar que la solicitud está bien formateada.
        Devuelve una lista con los atributos de las cabeceras.
    '''
    host = False
    params = {"url": "null"}
    for i in range(len(lineas)):
        linea = lineas[i].split()
        if i == 0:   # tratamiento distinto de la primera línea de la solicitud
            if len(linea)!=3:   # la linea no tiene el formato correcto
                enviar_mensaje(cs, "", 404)
                cerrar_conexion(cs)
                sys.exit(0) # debug
                # exit
                
            # Comprobar si la versión de HTTP es 1.1
            if linea[2]!="HTTP/1.1":
                enviar_mensaje(cs, "", 505)
                cerrar_conexion(cs)
                sys.exit(0) # debug
                # exit

            # Leer URL y eliminar parámetros si los hubiera
            # Comprobar si el recurso solicitado es /, En ese caso el recurso es index.html
            if linea[1]=="/":
                params["url"] = "index.html"
            else:
                params["url"] = linea[1]
            # Construir la ruta absoluta del recurso (webroot + recurso solicitado)
            path = webroot + linea[1]
            # Comprobar que el recurso (fichero) existe, si no devolver Error 404 "Not found"
            if not os.path.isfile(path):
                enviar_mensaje(cs, "", 404)
                logger.debug("Ruta erronea: " + path)
                cerrar_conexion(cs)
                sys.exit(0) # debug
                # exit

        # Analizar las cabeceras. Imprimir cada cabecera y su valor.
        else:   # resto de líneas de la solicitud
            if len(linea)!=2:   # la linea no tiene el formato correcto
                enviar_mensaje(cs, "", 404)
                cerrar_conexion(cs)
                sys.exit(0) # debug
                # exit

            if linea[0] in params:  # hay un parámetro repetido, bad request
                enviar_mensaje(cs, "", 400)
                cerrar_conexion(cs)
                sys.exit(0) # debug
                # exit

            if linea[0]=="Host":
                host = True
            logger.info(linea[0] + ": " + linea[1])
            params[linea[0]] = linea[1]

    if not host:    # si no se incluye la cabecera Host
        enviar_mensaje(cs, "", 400)
        cerrar_conexion(cs)
        sys.exit(0) # debug
        # exit

    return params


def process_web_request(cs, webroot):
    """ Procesamiento principal de los mensajes recibidos.
    """
    # bucle para esperar los datos a través del socket cs con el select()
    while(True):
        # el select debe comprobar si el socket cs tiene datos para leer.
        # además se comprueba si hay que cerrar la conexión por un timeout
        r, wsublist, xsublist = select.select([cs],[],[], TIMEOUT_CONNECTION)
        # si hay algo en el conjunto de lectura r, se procesa. Si no, es que ha saltado el timeout.
        if r:
            # Leer los datos con recv.
            s = r[0]    # el unico posible valor de la lista es el socket. (TODO es lo mismo este socket que cs??? debería no?)
            # print(len(r)) # debug select
            msg = recibir_mensaje(s)
            if len(msg)>0:
                logger.debug("Client message: " + msg)
                lineas = msg.splitlines()    # se divide el mensaje en líneas para que sea más cómodo de manejar
                # procesar linea a linea que todo el mensaje es correcto
                '''
                                        * 
                    * Extraer extensión para obtener el tipo de archivo. Necesario para la cabecera Content-Type
                    * Preparar respuesta con código 200. Construir una respuesta que incluya: la línea de respuesta y
                      las cabeceras Date, Server, Connection, Set-Cookie (para la cookie cookie_counter),
                      Content-Length y Content-Type.
                    * Leer y enviar el contenido del fichero a retornar en el cuerpo de la respuesta.
                    * Se abre el fichero en modo lectura y modo binario
                        * Se lee el fichero en bloques de BUFSIZE bytes (8KB)
                        * Cuando ya no hay más información para leer, se corta el bucle
                '''

                linea = lineas[0].split()
                # Comprobar si es un método GET. Si no devolver un error Error 405 "Method Not Allowed".
                if linea[0]!="GET":
                    # TODO gestionar PUT
                    enviar_mensaje(s, "", 405)
                    cerrar_conexion(cs)
                # se comprueba que la solicitud es correcta y se recogen los argumentos de la solicitud
                print("probando probando")
                heads = check_request(s, lineas, webroot)
                # Si la cabecera es Cookie comprobar  el valor de cookie_counter para ver si 
                # ha llegado a MAX_ACCESOS y devolver un Error "403 Forbidden"
                if "Cookie" in heads:
                    process_cookies(heads, cs)
                else:   # primera vez que accede al servidor
                    cookie_counter = 1


                   
                
                
                    
            else:
                logger.error("ERROR")
                        
            sys.exit(0)

        # Si es por timeout, se cierra el socket tras el período de persistencia.
        # NOTA: Si hay algún error, enviar una respuesta de error con una pequeña página HTML que informe del error.
        else:
            logger.error("Timeout alcanzado.")
            cerrar_conexion(cs)


def main():
    """ Función principal del servidor
    """

    try:

        # Argument parser para obtener la ip y puerto de los parámetros de ejecución del programa. IP por defecto 0.0.0.0
        parser = argparse.ArgumentParser()
        parser.add_argument("-p", "--port", help="Puerto del servidor", type=int, required=True)
        parser.add_argument("-ip", "--host", help="Dirección IP del servidor o localhost", required=True)
        parser.add_argument("-wb", "--webroot", help="Directorio base desde donde se sirven los ficheros (p.ej. /home/user/mi_web)")
        parser.add_argument('--verbose', '-v', action='store_true', help='Incluir mensajes de depuración en la salida')
        args = parser.parse_args()

        if args.verbose:
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug logging level is set.")

        logger.info('Enabling server in address {} and port {}.'.format(args.host, args.port))
        logger.info("Serving files from {}".format(args.webroot))


        # crear un socket TCP (SOCK_STREAM)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        # con esta opcion del socket permitimos que reuse la misma dirección
        sock.setsockopt(SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # vincular socket a ip y puerto pasados como parámetros
        sock.bind((args.host, args.port))   # !!! bind() takes exactly one argument (2 given)
        # escuchar conexiones entrantes
        sock.listen()
        logger.info("Iniciar escucha infinita del servidor web (addr={},port={})".format(args.host, args.port))  # debug
        while(True):
            # se acepta una conexión
            conn, addr = sock.accept()
            logger.info("Petición entrante (info={})".format(addr))
            pid = os.fork()
            # tratamiento del fork:'
            # caso del hijo: encargado de cerrar el socket del padre y procesar la petición
            if pid == 0:
                sock.close()
                process_web_request(conn, args.webroot)
                # TODO salir del while(True)???????
                sys.exit(1)
            # caso del padre: cerrar la conexión que gestiona el hijo
            else:
                cerrar_conexion(conn)



    except KeyboardInterrupt:
        True

if __name__== "__main__":
    main()
