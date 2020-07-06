import socket
import time

SERVER = 'vega.ii.uam.es'
PORT = 8000

#Funcion que calcula el timeout de las conexiones
def enviar_y_recibir(mensaje):
    mi_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    mi_socket.connect((SERVER, PORT))
    mi_socket.sendall(mensaje.encode())
    aux=recv_timeout(mi_socket)		
    mi_socket.close()
    return aux





#Funcion que usa query para obtener la ip y el puerto del usuario cuyo nick se conoce
def recv_timeout(mi_socket,timeout=2):
    mi_socket.setblocking(0)
    resultado_final=[];
    res='';
    comienzo=time.time()
    while 1:
        
        if resultado_final and time.time()-comienzo>timeout:
            break
       
            break
        try:
            res=mi_socket.recv(8192)
            if res:
                resultado_final.append(res.decode())
                comienzo=time.time()
            else:
                time.sleep(0.1)
        except:
            pass
    return ''.join(resultado_final)


#Funcion que permite listar todos los usuarios registrados en el sistema
def listUsers():
    mensaje = 'LIST_USERS'
    aux = []
    respuesta = str(enviar_y_recibir(mensaje)).split('#')

    for i in range(len(respuesta)):
        if i == 0:
            aux.append(respuesta[i].split(' ')[3])
        else:
            aux.append(respuesta[i].split(' ')[0])
    return aux


#Funcion que registra un usuario en el servidor
def registarUsuario(nombre, contrasenia, ip, port):
    mensaje = 'REGISTER ' + nombre + ' ' + ip + ' ' + str(port) + ' ' + contrasenia + ' V1'
    aux=enviar_y_recibir(mensaje)
    if aux.split(' ')[0] == "OK":
        return True
    else:
        return False

#Funcion que permite obtener la dirección IP y puerto de un usuario conociendo su nick
def query(nombre):
    mensaje = 'QUERY ' + nombre
    return enviar_y_recibir(mensaje)




