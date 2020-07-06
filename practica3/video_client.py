from appJar import gui
from PIL import Image, ImageTk
import numpy as np
import _thread as thread
import collections
import cv2
import ds as ds
import socket


class VideoClient(object):
    #Constructor de la clase VideoClient el cual se inicializa con algunos parametros de configuracion iniciales
    def __init__(self, window_size):
        self.app = gui("Redes2 - P2P", window_size)
        self.app.setGuiPadding(10, 10)
        self.flagColgar=0
        self.conf = 0
        self.app.addLabel("title", "Cliente Multimedia P2P - Redes2 ")
        self.app.addImage("video", "imgs/webcam.gif")
        self.app.addLabelEntry("Nombre: ")
        self.app.addLabelSecretEntry("Contraseña: ")
        self.app.addLabelEntry("IP: ")
        self.app.addLabelNumericEntry("Puerto: ")
        self.app.addButtons(["Registrarse/Logearse", "Salir", "Configuracion"], self.buttonsCallback)
        self.cap = cv2.VideoCapture(0)

    #Funcion que comienza la ejecucion del programa
    def start(self):
        self.app.go()

    #Funcion main del programa
    def main_function(self):

        self.app.addLabel("seleccion" , "Selecciona un usuario para llamar.")
        self.app.addLabel("cambiar_config",  "Recuerde cambiar ahora la configuración si lo desea, durante la llamada no podrá.")
        usuarios = ds.listUsers()

        self.app.addListBox("lista_usuarios", usuarios)
        self.app.setListItemBg("lista_usuarios", usuarios, "blue")
        self.app.addNamedButton("Llamar", "LlamarLista", self.buttonsCallback)
        self.app.addButton("Configuracion", self.buttonsCallback)
        self.app.addButton("Salir", self.buttonsCallback)
        
        self.app.clearStatusbar()
        self.app.addStatusbar(fields=2)

    



    # Función que captura la imagen de cada momento

    def capturaVideo(self):
        
        ret, frame = self.cap.read()
        frame = cv2.resize(frame, (640,480))
        cv2_im = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))
        self.app.setImageData("video", img_tk, fmt = 'PhotoImage')	
        if self.flagColgar==1:
            self.pararCamara()	    



    #Funcion que se encarga de ir descomprimiendo el video que le llega al destinatario    
    def recibirVideo(self,socket_UDP):
        
        buffer=collections.deque(maxlen=60000)

        while 1:
            video_comprimido = socket_UDP.recv(60000)
            video_descomprimido=cv2.imdecode(np.frombuffer(video_comprimido,np.uint8),1)
            video_descomprimido=cv2.resize(video_descomprimido,(640,480))
            cv2_im=cv2.cvtColor(video_descomprimido,cv2.COLOR_BGR2RGB)
            img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))
            buffer.append(img_tk)
            self.app.setImageData("video",buffer.pop() , fmt='PhotoImage')
            if video_comprimido is None:
                self.app.infoBox("Llamada finalizada", "Llamada concluida")
                thread.exit()

    #Funcion que para la ejecucion de la camara	
    def pararCamara(self):
        cv2.destroyAllWindows()


    #Funcion que permite cambiar la resolucion por defecto de la camara
    def setImageResolution(self, resolution):
        if resolution == "LOW":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
        elif resolution == "MEDIUM":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        elif resolution == "HIGH":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    #Funcion que da funcionalidad a cada uno de los botones de la aplicacion
    def buttonsCallback(self, button):

        if button == "Salir":
            self.app.stop()
        elif button== "Colgar":
            self.app.removeAllWidgets()
            self.flagColgar=1
            thread.start_new_thread(self.main_function,())
        elif button == "Configuracion":
            self.configuracion()
        elif button == "ACEPTAR":
            resolution = self.app.getOptionBox("Calidad del Video: ")
            self.setImageResolution(resolution)
            self.app.hideSubWindow("Configuracion")
        elif button == "CANCELAR":
            self.app.hideSubWindow("Configuracion")
        elif button == "Registrarse/Logearse":
            self.nick = self.app.getEntry("Nombre: ")
            self.password = self.app.getEntry("Contraseña: ")
            self.ip = self.app.getEntry("IP: ")
            self.port = self.app.getEntry("Puerto: ")
            if ds.registarUsuario(self.nick, self.password, self.ip, self.port) == True:
                self.app.removeAllWidgets()
                hilo = thread.start_new_thread(self.recibir_llamada, (self.ip, self.port))
                self.main_function()
            else:
                self.app.errorBox("Registro incorrecto", "Intentelo otra vez")
        elif button == "Conectar":
            nick = self.app.textBox("Conexión", "Introduce el nick del usuario a buscar")
        elif button == "LlamarLista":
            hilo = thread.start_new_thread(self.realizar_llamada,(self.app.getListBox("lista_usuarios")[0], 8080))
            self.app.removeAllWidgets()
            self.app.addLabel("Llamando","Llamando, espere por favor.")
            self.app.addButton("Colgar",self.buttonsCallback)

    #Funcion que se encarga de la screen para el cambio de resolucion del video
    def configuracion(self):
        if self.conf == 0:
            self.app.startSubWindow("Configuracion")
            self.app.setSize("379x265")
            self.app.addLabelOptionBox("Calidad del Video: ", ["- Calidad -","HIGH", "MEDIUM","LOW"])
            self.app.addButtons(["ACEPTAR", "CANCELAR"], self.buttonsCallback)
            self.app.stopSubWindow()
            self.conf=1
        self.app.showSubWindow("Configuracion")

    #Funcion que establece la conexion mediante sockest de una llamda a un usuario destinatario
    def realizar_llamada(self,nickDest, srcUDPport):
        answer = ds.query(nickDest).split(' ')
        socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        socket1.connect((answer[3], int(float(answer[4]))))

        message = 'CALLING ' + self.nick + ' ' + str(srcUDPport)
        socket1.sendall(message.encode())
        aux = socket1.recv(8192)
        response=aux.decode().split(' ')
        if response[0]=="CALLING_ACCEPTED":
            self.app.removeAllWidgets()
            print("Calling")
            hilo = thread.start_new_thread(self.enviar_video, (answer[3], response[2]))
            hilo2 = thread.start_new_thread(self.recibir_video, (8080,))
        else:
            self.app.infoBox("Respuesta rechazada")
            self.app.removeAllWidgets()
            self.app.clearStatusbar()
            self.main_function()

    #Funcion que bindeo un socket para empezar a recibir una llamada
    def recibir_llamada(self,ip,puerto):
        socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket1.bind((ip,int(puerto)))
        
        while (True):
            socket1.listen(1)
            (socket2,direccion)=socket1.accept()
            message= socket2.recv(8196)
            call=message.decode().split(' ')
            respuesta=self.app.textBox("Llamada entrante de " + call[1],"Puerto para recibir:")
            if respuesta is not None:
                message = 'CALLING_ACCEPTED ' + self.nick + ' ' + respuesta
                socket2.sendall(message.encode())
                socket2.close()
                self.app.removeAllWidgets()
                print("Receiving")
                hilo1 = thread.start_new_thread(self.recibir_video, (respuesta,))
                hilo2 = thread.start_new_thread(self.enviar_video, (direccion[0], call[2]))
                self.app.addButtons(["Pausar", "Colgar"], self.buttonsCallback)
            else:
                message = 'CALLING_DENIED ' + self.nick
                socket2.sendall(message.encode())
                socket2.close()


    #Funcion que registra el socket para la llamada y que usa la funcion de obtener imagenes de la camara
    def comenzar_llamada(self,socket_UDP):
        self.socket_UDP=socket_UDP

        self.app.addLabel("title", "Cliente Multimedia P2P - Redes2 ")
        self.cap = cv2.VideoCapture(0)
        self.app.setPollTime(20)

        self.app.registerEvent(self.capturaVideo)
    #Funcion que se conecta a un puerto y una id para empezar a mandar video
    def enviar_video(self,ip,puerto):

        socket_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_UDP.connect((ip, int(puerto)))
        self.comenzar_llamada(socket_UDP)

    #Funcion que se encarga de empezar a obtener video y a llamar a la funcion que lo descomprime
    def recibir_video(self,puerto):
        socket_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_UDP.bind((self.ip, int(puerto)))
        self.app.addImage("video","imgs/webcam.gif")
        self.recibirVideo(socket_UDP)





if __name__ == '__main__':
    vc = VideoClient("840x620")
    vc.start()


