# coding=utf-8

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
MAX_ACCESOS = 10

# Extensiones admitidas (extension, name in HTTP)
filetypes = {"gif":"image/gif", "jpg":"image/jpg", "jpeg":"image/jpeg", "png":"image/png", "htm":"text/htm", 
             "html":"text/html", "css":"text/css", "js":"text/js"}

# Configuración de logging
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s.%(msecs)03d] [%(levelname)-7s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger()


def enviar_mensaje(cs, data):
    """ Esta función envía datos (data) a través del socket cs.
        Devuelve el número de bytes enviados.
    """
    numwrite = cs.send(cs,data.encode())
    return numwrite


def recibir_mensaje(cs,data):
    """ Esta función recibe datos a través del socket cs
        Leemos la información que nos llega. recv() devuelve un string con los datos.
    """
    aux = cs.recv(BUFSIZE)
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


def process_web_request(cs, webroot):
    """ Procesamiento principal de los mensajes recibidos.


            * Si no es por timeout y hay datos en el socket cs.
                * Leer los datos con recv.
                * Analizar que la línea de solicitud y comprobar está bien formateada según HTTP 1.1
                    * Devuelve una lista con los atributos de las cabeceras.
                    * Comprobar si la versión de HTTP es 1.1
                    * Comprobar si es un método GET. Si no devolver un error Error 405 "Method Not Allowed".
                    * Leer URL y eliminar parámetros si los hubiera
                    * Comprobar si el recurso solicitado es /, En ese caso el recurso es index.html
                    * Construir la ruta absoluta del recurso (webroot + recurso solicitado)
                    * Comprobar que el recurso (fichero) existe, si no devolver Error 404 "Not found"
                    * Analizar las cabeceras. Imprimir cada cabecera y su valor. Si la cabecera es Cookie comprobar
                      el valor de cookie_counter para ver si ha llegado a MAX_ACCESOS.
                      Si se ha llegado a MAX_ACCESOS devolver un Error "403 Forbidden"
                    * Obtener el tamaño del recurso en bytes.
                    * Extraer extensión para obtener el tipo de archivo. Necesario para la cabecera Content-Type
                    * Preparar respuesta con código 200. Construir una respuesta que incluya: la línea de respuesta y
                      las cabeceras Date, Server, Connection, Set-Cookie (para la cookie cookie_counter),
                      Content-Length y Content-Type.
                    * Leer y enviar el contenido del fichero a retornar en el cuerpo de la respuesta.
                    * Se abre el fichero en modo lectura y modo binario
                        * Se lee el fichero en bloques de BUFSIZE bytes (8KB)
                        * Cuando ya no hay más información para leer, se corta el bucle

            * Si es por timeout, se cierra el socket tras el período de persistencia.
                * NOTA: Si hay algún error, enviar una respuesta de error con una pequeña página HTML que informe del error.
    """
    # bucle para esperar los datos a través del socket cs con el select()
    while(True):
        # el select debe comprobar si el socket cs tiene datos para leer.
        # además se comprueba si hay que cerrar la conexión por un timeout
        r, wsublist, xsublist = select.select([cs],[],[], TIMEOUT_CONNECTION)
        # si hay algo en el conjunto de lectura r, se procesa. Si no, es que ha saltado el timeout.
        if r:
            # Leer los datos con recv.
            s = r[0]    # el unico posible valor de la lista es el socket
            print(len(r)) # debug select
            if (s==r):
                print("ole")
            else:
                print("not ole :(")
                sys.exit(1)
            

            pass
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
