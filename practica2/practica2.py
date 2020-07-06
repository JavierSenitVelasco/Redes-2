#!/usr/bin/python
# -*- coding: utf-8 -*-

from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.Util.Padding import *
import requests
import json
import urllib3
import sys
import codecs

def main():
	urllib3.disable_warnings() 

	comando = sys.argv[1]
	#Listado de comandos aceptados
	if comando == "--get":
			getPublicKey()
	if comando == "--create_id":
			registrar()
	if comando == "--search_id":
			buscarUsuario()
	if comando == "--delete_id":
			eliminarUsuario()
	if comando == "--sign":
			firmar()
	if comando == "--encrypt":
			cifrar()
	if comando == "--enc_sign":
			cifrafYfirmar()
	if comando == "--list_files":
			listarArchivos()
	if comando == "--upload":
			subir()
	if comando == "--delete_file":
			borrarArchivo()
	if comando == "--download":
			bajar()

	
#Esta funcion genera una clave publica para un usuario
def generarClavePublica():

	key = RSA.generate(2048) 
	clave_encriptada = key.exportKey(pkcs=8, protection="scryptAndAES128-CBC") 

	fichero_salida = open("rsa_key.bin", "wb") 
	fichero_salida.write(clave_encriptada)

#Esta funcion registra a un usuario en el servidor
def registrar():
	generarClavePublica() # genera una clave publica al usuario.
	nombre = ""
	for i in range(2, len(sys.argv)-1): 
		nombre += sys.argv[i]
		if i != len(sys.argv)-2:
			nombre += " "

	email = sys.argv[len(sys.argv)-1] 

	
	url = 'https://vega.ii.uam.es:8080/api/users/register'
	
	clave_codificada = open("rsa_key.bin", "rb").read() 
	key = RSA.import_key(clave_codificada) 

	args = {'nombre': nombre, 'email': email, 'publicKey': key.publickey().exportKey()}
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer 3D9c4fA6CEd0a72b'} 
	print("Se está usando pycryptodome==3.9.7")
	req = requests.post(url,  json=args, headers=headers) 
	
	respuesta = req.json()
	try:
		print("El usuario "+respuesta['userID']+" ha sido logueado correctamente.") 
	except:
		print(respuesta['description'])
	


#Esta funcion obtiene la clave publica del usuario especificado
def getPublicKey():

	url = 'https://vega.ii.uam.es:8080/api/users/getPublicKey' 
	args = {'userID': '336706'}
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer 3D9c4fA6CEd0a72b'} 
	req = requests.post(url,  json=args, headers=headers)

	respuesta = req.json()
	try:
		print(respuesta['description'])
	except:
		
		print("\nClave publica del usuario:\n\n"+respuesta[u'publicKey']+"\n")


#Esta funcion busca usuarios a partir de un string introducido
def buscarUsuario():
	cadena = ""
	for i in range(2, len(sys.argv)): 
		cadena += sys.argv[i]
		if i != len(sys.argv)-1: 
			cadena += " "

	url = 'https://vega.ii.uam.es:8080/api/users/search' 
	args = {'data_search': cadena}
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer 3D9c4fA6CEd0a72b'} 
	req = requests.post(url,  json=args, headers=headers)

	respuesta = req.json()
	try:	 
		print(respuesta['description'])
	except:
		print(req.text)
	

#Esta funcion elimina un usuario junto con su token, se necesitara pues conseguir uno despues
def eliminarUsuario():
	id = sys.argv[2]

	url = 'https://vega.ii.uam.es:8080/api/users/delete' 
	args = {'userID': id}
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer 3D9c4fA6CEd0a72b'} 
	req = requests.post(url,  json=args, headers=headers)

	respuesta = req.json()
	try:
		print("el usuario "+respuesta[u'userID']+" ha sido eliminado correctamente.") 
	except:
		print(respuesta['description'])


#Esta funcion firma un archivo con un sha256
def firmar():


	ruta = sys.argv[2] 
	f=open(ruta, "rb").read()
	
	
	clave_codificada = open("rsa_key.bin", "rb").read()
	clave_privada = RSA.import_key(clave_codificada)

	h = SHA256.new(f)
	mi_firma = pkcs1_15.new(clave_privada).sign(h) 

	

	ruta_secundario, extension = ruta.split('.') 
	f2 = open(ruta_secundario+"Firmado.bin", "wb")
	f2.write(mi_firma)
	f2.write(f)
	f2.close()


#Esta funcion cifra un fichero, cifrando la clave simetrica con RSA y el contenido del fichero con AES
def cifrar():


	ruta = sys.argv[2]
	f=open(ruta, "rb").read()

	id = sys.argv[4] 
	

	url = 'https://vega.ii.uam.es:8080/api/users/getPublicKey' 
	args = {'userID': id}
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer 3D9c4fA6CEd0a72b'}
	req = requests.post(url,  json=args, headers=headers)

	text = req.json()
	try:
		print(text['description'])
	except:
		print("el archivo ha sido encriptado correctamente.") 
		
		clave_publica_destino = RSA.import_key(text[u'publicKey'])
		clave_simetrica = get_random_bytes(16) 
		vector_inicializacion=get_random_bytes(16)
		cifradoRSA = PKCS1_OAEP.new(clave_publica_destino)	
		cifradoAES=AES.new(clave_simetrica, AES.MODE_CBC, vector_inicializacion) 
		textocifrado = cifradoAES.encrypt(pad(f, 16, style='pkcs7')) 	
		ruta_secundario, extension = ruta.split('.')
		f2 = open(ruta_secundario	+"Cifrado.bin", "wb")	
		f2.write(cifradoRSA.encrypt(clave_simetrica))
		f2.write(vector_inicializacion+textocifrado)
		f2.close()


#Esta funcion realiza la union de firmar y cifrar
def cifrafYfirmar():

	ruta = sys.argv[2]
	f=open(ruta, "r").read().encode('utf-8')
	clave_codificada = open("rsa_key.bin", "rb").read()
	key = RSA.import_key(clave_codificada)
	h = SHA256.new(f)
	mi_firma = pkcs1_15.new(key).sign(h)

	id = sys.argv[4]

	url = 'https://vega.ii.uam.es:8080/api/users/getPublicKey'
	args = {'userID': id}
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer 3D9c4fA6CEd0a72b'}
	req = requests.post(url,  json=args, headers=headers)

	text = req.json() 
	try:
		print(text['description'])
	except:
		 

		clave_publica_destino = RSA.import_key(text[u'publicKey'])
		clave_simetrica = get_random_bytes(32)
		cifradoRSA = PKCS1_OAEP.new(clave_publica_destino)
		vector_inicializacion=get_random_bytes(16)
		cifradoAES=AES.new(clave_simetrica, AES.MODE_CBC, vector_inicializacion)
		textocifrado = cifradoAES.encrypt(pad(vector_inicializacion+mi_firma+f, 16, style='pkcs7'))
		ruta_secundario, extension = ruta.split('.')
		f2 = open(ruta_secundario+"FirmadoYCifrado.bin", "wb")	
		f2.write(cifradoRSA.encrypt(clave_simetrica)+textocifrado)
		print("El archivo ha sido encriptado y firmado correctamente.")
		f2.close()


#Esta funcion lista todos los archivos de un usuario
def listarArchivos(): 

	url = 'https://vega.ii.uam.es:8080/api/files/list'
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer 3D9c4fA6CEd0a72b'}
	req = requests.post(url, headers=headers)

	text = req.json()
	try:
		print(text['description'])
	except:
		print(text['files_list'] , "El usuario tiene " , text['num_files'] , " archivos")


#Esta funcion sube un archivo al servidor, cifrandolo y firmandolo previamente
def subir():

	cifrafYfirmar() 

	

	ruta = sys.argv[2]
	ruta_secundario, extension = ruta.split('.')
	
	
	
	f = open(ruta_secundario+"FirmadoYCifrado.bin", "rb")
	files = {'ufile' : f}
	url = 'https://vega.ii.uam.es:8080/api/files/upload' 
	headers = {'Authorization': 'Bearer 3D9c4fA6CEd0a72b'}
	req = requests.post(url, headers=headers, files=files) 

	respuesta = req.json()

	try:
		print(respuesta['description'])
	except:
		print ("Archivo subido correctamente.")
	f.close()


#Esta funcion borra un archivo de un usuario introduciendo su id
def borrarArchivo():

	id = sys.argv[2]

	url = 'https://vega.ii.uam.es:8080/api/files/delete' 
	args = {'file_id': id}
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer 3D9c4fA6CEd0a72b'}
	req = requests.post(url,  json=args, headers=headers)

	respuesta = req.json()
	try:
		print(respuesta['description'])
	except:
		print(respuesta['file_id'] , "borrado correctamente")

#Esta funcion descarga el fichero cuyo id sea el introducido
def bajar():

	idArchivo = sys.argv[2]

	url = 'https://vega.ii.uam.es:8080/api/files/download' 
	args = {'file_id': idArchivo}
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer 3D9c4fA6CEd0a72b'}
	req = requests.post(url,  json=args, headers=headers)

	try:
		respuesta = req.json()
		print(respuesta['description'])
	except:

		aux = req.content 

		f = open("aux.bin", "wb")
		f.write(aux)
		f.close()
		f = open("aux.bin", "rb")

		id = sys.argv[4]

		

		url = 'https://vega.ii.uam.es:8080/api/users/getPublicKey'
		args = {'userID': id}
		headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer 3D9c4fA6CEd0a72b'}
		req = requests.post(url,  json=args, headers=headers)
		text = req.json()


		try:
			print(text['description'])
		except:

			clave_publica_emisor = RSA.import_key(text[u'publicKey']) 
			clave_codificada = open("rsa_key.bin", "rb").read()
			private_key = RSA.import_key(clave_codificada)
			clave_sesion_encriptada = f.read(private_key.size_in_bytes())
			cifradoRSA = PKCS1_OAEP.new(private_key) 
			clave_sesion = cifradoRSA.decrypt(clave_sesion_encriptada)
			textocifrado = f.read()
			cifradoAES_aes = AES.new(clave_sesion, AES.MODE_CBC) 
			resultado = cifradoAES_aes.decrypt(textocifrado) 
			resultado = unpad(resultado, 16)
			mi_firma = resultado [16:272] 
			resultado2 = resultado[272:]

			h = SHA256.new(resultado2) 

			
			try:
				pkcs1_15.new(clave_publica_emisor).verify(h, mi_firma)
				print ("Archivo bajado correctamente")
			except (ValueError, TypeError):
				print ("Error durante la descarga")
				return


			

			fichero_salida = open("ficheroDescargado.bin", "wb")
			fichero_salida.write(resultado2)
			fichero_salida.close()

if __name__ == "__main__":
	main()
