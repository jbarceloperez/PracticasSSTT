# coding=utf-8
#!/usr/bin/env python3

import socket
import selectors    #https://docs.python.org/3/library/selectors.html
import select
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
MAX_ACCESOS = 5

# Extensiones admitidas (extension, name in HTTP)
filetypes = {"gif":"image/gif", "jpg":"image/jpg", "jpeg":"image/jpeg", "png":"image/png", "htm":"text/htm", 
             "html":"text/html", "css":"text/css", "js":"text/js"}

# Configuración de logging
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s.%(msecs)03d] [%(levelname)-7s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger()


def enviar_mensaje(cs, data):
    """ Esta función envía datos (data) a través del socket cs
        Devuelve el número de bytes enviados.
    """
    bytes=cs.send(cs,data.encode())
    return bytes


def recibir_mensaje(cs):
    """ Esta función recibe datos a través del socket cs
        Leemos la información que nos llega. recv() devuelve un string con los datos.
    """
    data = cs.recv(BUFSIZE)
    try:
        dec_data = data.decode()
        return dec_data
    except: 
        print("el cliente quiere cerrar la conexion")
        cerrar_conexion(cs)


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
    # Procesamiento principal de los mensajes recibidos.
     #   Típicamente se seguirá un procedimiento similar al siguiente (aunque el alumno puede modificarlo si lo desea)

      #  * Bucle para esperar hasta que lleguen datos en la red a través del socket cs con select()
    lista_sockets=[cs]
    while True:
       #     * Se comprueba si hay que cerrar la conexión por exceder TIMEOUT_CONNECTION segundos
        #      sin recibir ningún mensaje o hay datos. Se utiliza select.select
            lectura,escritura,error = select.select(lista_sockets, [], [], TIMEOUT_CONNECTION)
         #   * Si no es por timeout y hay datos en el socket cs.
          #      * Leer los datos con recv.
            if lectura:
                for s in lectura:
                    data=recibir_mensaje(s)
                    if len(data)!=0:
                        print("el cliente dice: ", data)
                        headers=data.split()
                        if(headers[0]!="GET"):
                            f=open("notallowed.html","rb")
                            tamanof=os.stat("notallowed.html").st_size
                            respuesta='HTTP/1.1 405 Method Not Allowed\r\nDate: '+datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT\r\n')+'Server: web.medicosdemurcia22.org\r\nConnection: Keep-Alive\r\nKeep-Alive: timeout=24\r\nContent-Length: '+str(tamanof)+'\r\nContent-Type: text/html\r\n\r\n'
                            data=f.read(BUFSIZE)
                            respuesta=respuesta.encode()
                            by=respuesta+data
                            while(by):
                                s.send(by)
                                by=f.read(BUFSIZE)
                            f.close()
                            logger.error("HTTP/1.1 405 Method Allowed")
                            break
                        #     * Analizar que la línea de solicitud y comprobar está bien formateada según HTTP 1.1
                        #expresion regular de prueba
                        pattern='GET\s(.+)\sHTTP/1.1*([\][a-z])*(\s*.*)\sHost:([a-z]*[0-9]*[.:]?[a-z]*[0-9]*)([\][a-z])*(\s*.*)*'
                        if re.fullmatch(pattern,data):
                            print("coincide")
                        else:
                            if 'HTTP/1.5' in headers:
                                print("HTTP/1.1 505 HTTP Version Not Supported")
                                logger.error("HTTP/1.1 505 HTTP Version Not Supported")
                                f=open("badVersion.html","rb")
                                tamanof=os.stat("badVersion.html").st_size
                                respuesta='HTTP/1.1 505 Version Not Supported\r\nDate: '+datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT\r\n')+'Server: web.medicosdemurcia22.org\r\nConnection: Keep-Alive\r\nKeep-Alive: timeout=24\r\nContent-Length: '+str(tamanof)+'\r\nContent-Type: text/html\r\n\r\n'
                                data=f.read(BUFSIZE)
                                respuesta=respuesta.encode()
                                by=respuesta+data
                                while(by):
                                    s.send(by)
                                    by=f.read(BUFSIZE)
                                f.close()
                                break
                            f=open("badReq.html","rb")
                            tamanof=os.stat("badReq.html").st_size
                            respuesta='HTTP/1.1 400 Bad Request\r\nDate: '+datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT\r\n')+'Server: web.medicosdemurcia22.org\r\nConnection: Keep-Alive\r\nKeep-Alive: timeout=24\r\nContent-Length: '+str(tamanof)+'\r\nContent-Type: text/html\r\n\r\n'
                            data=f.read(BUFSIZE)
                            respuesta=respuesta.encode()
                            by=respuesta+data
                            while(by):
                                s.send(by)
                                by=f.read(BUFSIZE)
                            f.close()
                            logger.error("HTTP/1.1 400 Bad Request")
                            #sys.exit(0)
                            #pass
                            break
                            """
                            patternVersion='HTTP/1.5([\][a-z])*(\s*.*)'
                            version=headers[2]
                            if re.fullmatch(patternVersion,version):
                            print("HTTP/1.1 505 HTTP Version Not Supported")
                            logger.error("HTTP/1.1 505 HTTP Version Not Supported")
                            f=open("badVersion.html","rb")
                            tamanof=os.stat("badVersion.html").st_size
                            respuesta='HTTP/1.1 505 Version Not Supported\r\nDate: '+datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT\r\n')+'Server: Sstt\r\nConnection: Keep-Alive\r\nKeep-Alive: timeout=20\r\nContent-Length: '+str(tamanof)+'\r\nContent-Type: text/html\r\n\r\n'
                            data=f.read(BUFSIZE)
                            respuesta=respuesta.encode()
                            by=respuesta+data
                            while(by):
                                s.send(by)
                                by=f.read(BUFSIZE)
                            f.close()
                            break
                            """
                        #       * Comprobar si la versión de HTTP es 1.1
                        #headers=data.split()
                        #ELIMINAR LOS PARAMETROS DE LA URL
                        #     * Leer URL y eliminar parámetros si los hubiera
                        #    * Comprobar si el recurso solicitado es /, En ese caso el recurso es index.html
                        #if(headers[1]=="/"):
                         #   f=open("index.html","r")
                        #   * Construir la ruta absoluta del recurso (webroot + recurso solicitado)
                        #  * Comprobar que el recurso (fichero) existe, si no devolver Error 404 "Not found"
                       # for i in headers:
                        #    print(i)
                        if 'Cookie:' in headers:
                            indice=headers.index('Cookie:')
                            indice+=1
                            cookie_counter=int(headers[indice])
                            cookie_counter+=1
                            print('contenido cookie:',headers[indice])
                            print('cookienueva:',str(cookie_counter))
                            if(cookie_counter>=MAX_ACCESOS):
                                f=open("max_accesos.html","rb")
                                tamanof=os.stat("max_accesos.html").st_size
                                respuesta='HTTP/1.1 403 Forbidden\r\nDate: '+datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT\r\n') + 'Server: web.medicosdemurcia22.org\r\nConnection: Keep-Alive\r\nKeep-Alive: timeout=24\r\nContent-Length: '+str(tamanof)+'\r\nContent-Type: text/html\r\n\r\n'
                                data=f.read(BUFSIZE)
                                respuesta=respuesta.encode()
                                by=respuesta+data
                                print(by)
                                while(by):
                                    s.send(by)
                                    by=f.read(BUFSIZE)
                                f.close()
                                #sys.exit(0)
                            #cookie_counter=0
                        else:
                           #vale 1 porque es la primera vez que accede
                            cookie_counter=1 
                        if(headers[1]=="/"):
                            filepath=webroot+"/index.html"
                            isFile=os.path.isfile("index.html")
                           # print("el fichero esta: ",isFile)
                            tamano=os.stat("index.html").st_size
                            f=open("index.html","rb")
                            #cabeceras
                            respuesta='HTTP/1.1 200 OK\r\nDate: '+ datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT\r\n') + 'Server: web.medicosdemurcia22.org\r\nSet-Cookie: '+str(cookie_counter)+'; Max-age=5\r\nConnection: Keep-Alive\r\nKeep-Alive: timeout= 24\r\nContent-Length: '+ str(tamano) + '\r\nContent-Type: text/html\r\n\r\n'
                            #print("cabeceras: ",respuesta)
                            data=f.read(BUFSIZE)
                            respuesta=respuesta.encode()
                            by=respuesta+data
                            while(by):
                                s.send(by)
                                by=f.read(BUFSIZE)
                            f.close()
                        else:
                            solicitado=webroot+headers[1]
                            print("el fichero solicitado es:",solicitado)
                            isFile=os.path.isfile(solicitado)
                            print("el fichero esta: ",isFile)
                            if isFile:
                                f=open(solicitado,"rb")
                                tamanof=os.stat(solicitado).st_size
                                respuesta='HTTP/1.1 200 OK\r\nDate: '+ datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT\r\n') + 'Server: web.medicosdemurcia22.org\r\nSet-Cookie: '+str(cookie_counter)+'; Max-age=5\r\nConnection: Keep-Alive\r\nKeep-Alive: timeout= 24\r\nContent-Length: '+ str(tamanof) + '\r\nContent-Type: image/jpg\r\n\r\n'
                             #   print("cabeceras: ",respuesta)
                                data=f.read(BUFSIZE)
                                respuesta=respuesta.encode()
                                by=respuesta+data
                                while(by):
                                    s.send(by)
                                    by=f.read(BUFSIZE)
                                f.close()
                            else:
                                 f=open("notfound.html","rb")
                                 tamanof=os.stat("notfound.html").st_size
                                 respuesta='HTTP/1.1 404 Not Found\r\nDate: '+datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT\r\n') + 'Server: web.medicosdemurcia22.org\r\nConnection: Keep-Alive\r\nKeep-Alive: timeout=24\r\nContent-Length: '+str(tamanof) + '\r\nContent-Type: text\html\r\n\r\n'
                                 data=f.read(BUFSIZE)
                                 respuesta=respuesta.encode()
                                 by=respuesta+data
                                 while(by):
                                     s.send(by)
                                     by=f.read(BUFSIZE)
                                 f.close()
#COMPROBAR LA CABECERA COOKIE
                        #if(len(headers[6])!=0):
                            #print("Valor de la cookie: ",headers[6])
                        #if(headers[6]==MAX_ACCESOS):
                         #   print("403 Forbidden")
                   # * Analizar las cabeceras. Imprimir cada cabecera y su valor. Si la cabecera es Cookie comprobar
                    #  el valor de cookie_counter para ver si ha llegado a MAX_ACCESOS.
                    # Si se ha llegado a MAX_ACCESOS devolver un Error "403 Forbidden"
                    #* Obtener el tamaño del recurso en bytes.
                        
                    #os.path con la ruta del archivo
                    #* Extraer extensión para obtener el tipo de archivo. Necesario para la cabecera Content-Type
                    #* Preparar respuesta con código 200. Construir una respuesta que incluya: la línea de respuesta y
                    #  las cabeceras Date, Server, Connection, Set-Cookie (para la cookie cookie_counter),
                    #  Content-Length y Content-Type.
                    #* Leer y enviar el contenido del fichero a retornar en el cuerpo de la respuesta.
                    #* Se abre el fichero en modo lectura y modo binario
                    #    * Se lee el fichero en bloques de BUFSIZE bytes (8KB)            
        #   * Cuando ya no hay más información para leer, se corta el bucle
                        #contenido=f.read(BUFSIZE)
                        #tamano-=BUFSIZE
                        #contenido=f.read(BUFSIZE)
                    else:
                       logger.error("Timeout socket {}".format(cs))
                       #print('hola')
                       t='TIMEOUT'
                       t=t.encode()
                       s.send(t)
                       cerrar_conexion(cs)
            else:
               logger.error("Timeout socket{}".format(cs))
               cerrar_conexion(cs)
       #sys.exit(0) #* Si es por timeout, se cierra el socket tras el período de persistencia.
                #   * NOTA: Si hay algún error, enviar una respuesta de error con una pequeña página HTML que informe del error.
    


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

        """ Funcionalidad a realizar
        * Crea un socket TCP (SOCK_STREAM)
        * Permite reusar la misma dirección previamente vinculada a otro proceso. Debe ir antes de sock.bind
        * Vinculamos el socket a una IP y puerto elegidos

        * Escucha conexiones entrantes

        * Bucle infinito para mantener el servidor activo indefinidamente
            - Aceptamos la conexión

            - Creamos un proceso hijo

            - Si es el proceso hijo se cierra el socket del padre y procesar la petición con process_web_request()

            - Si es el proceso padre cerrar el socket que gestiona el hijo.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((args.host,args.port))
        s.listen()
        while (True):
            conn, addr = s.accept()
            print("se ha conectado: ", addr)
            pid= os.fork()
            #proceso hijo
            if pid==0:
                s.close()
                process_web_request(conn, args.webroot)
            #cuando el proceso hijo acaba muere y acaba su ejecución
            #proceso padre 
            else: 
                cerrar_conexion(conn)
              #  sys.exit(0)
    except KeyboardInterrupt:
        True

if __name__== "__main__":
    main()
