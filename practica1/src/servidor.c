/**
 * @author Javier Senit Velasco
 */

#include <stdio.h>
#include <string.h>
#include <strings.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/socket.h>
#include <syslog.h>
#include <errno.h>
#include <time.h>
#include "types.h"
#include <arpa/inet.h>
#include <netinet/in.h>
#include <netdb.h>
#include <sys/types.h>
#include <signal.h>
#include <pthread.h>
#include <sys/stat.h>
#include "../libs/picohttpparser.h"
#include <assert.h>

/*Estructura de un servidor*/
typedef struct{
    char server_root[100];
    int port; 
    int max_clients;
    char server_signature[100]; 
}Config_Server;



/*Funcion que demoniza la ejecución del servidor*/
void demonizar(){
	pid_t pid;
	pid = fork();
	if(pid<0)
		exit(EXIT_FAILURE);
	if(pid>0)
		exit(EXIT_SUCCESS);
	umask(0);
	setlogmask(LOG_UPTO(LOG_INFO));
	openlog("Mensajes del servidor:",LOG_CONS | LOG_PID | LOG_NDELAY, LOG_LOCAL3);
	syslog(LOG_ERR,"Initiating new server.");
	
	if(setsid()<0){
		syslog(LOG_ERR,"Error creando el SID del hijo");
		exit(EXIT_FAILURE);
	}
	
	if((chdir("/"))<0){
		syslog (LOG_ERR, "Error cambiando el directorio");
		exit(EXIT_FAILURE);
	}
	
	syslog (LOG_INFO, "Cerrando descriptores");
    close(STDOUT_FILENO); 
	close(STDERR_FILENO);
	close(STDIN_FILENO); 
	
	return ;
}

/*Variables globales*/
Config_Server * configuracion_servidor; 
int conexion; 



/*Funcion que controla la señal sigint*/
void controlador_SIGINT (int sig){
  syslog (LOG_INFO, "Servidor cerrado");
  /*Se libera el servidor*/
  free(configuracion_servidor);
  close(conexion); 
  return;  
}   


/*Esta funcion se encarga de enviar la extension*/
STATUS sendExt(int usuario, char * ext){
      if (ext!=NULL){
        if(strcmp(ext, ".txt") == 0){
            write(usuario,"Content-Type: text/plain\r\n",26);
        }
        else if(strcmp(ext, ".pdf") == 0 ){
            write(usuario,"Content-Type: aplication/pdf\r\n",30);
        }
        else if(strcmp(ext, ".html") == 0){
            write(usuario,"Content-Type: text/html\r\n",25);
        }
        
        else if(strcmp(ext, ".jpeg") == 0 || strcmp(ext, ".jpg") == 0){
            write(usuario,"Content-Type: image/jpeg\r\n",26);
        }else if(strcmp(ext, ".gif") == 0){
            write(usuario,"Content-Type: image/gif\r\n",25);
        }
        else if(strcmp(ext, ".mpeg") == 0 || strcmp(ext, ".mpg") == 0){
            write(usuario,"Content-Type: video/mpeg\r\n",26);
        }
        else if(strcmp(ext, ".doc") == 0 || strcmp(ext, ".docx") == 0){
            write(usuario,"Content-Type: aplication/msword\r\n",33);
        }
        
        else
            return ERROR;
        
        return OK;
      }else{
          return ERROR;
      }
}



/*Esta funcion se encarga del campo last_modified de la cabecera*/
STATUS fechaModificada(int usuario, char * ruta){
    char last_modified[80];  
    struct tm *tmod;
    struct stat time_modified;    
    
    if(ruta !=NULL){
        stat(ruta,&time_modified);
        tmod= localtime(&(time_modified.st_mtime));
        strftime(last_modified, 80,"Last-Modified: %a, %d %b %Y %H:%M:%S %Z \r\n",tmod);
        
        write(usuario, last_modified, strlen(last_modified));
        
        return OK;
    }else{
        return ERROR;
    }
}



/*Esta funcion ejecuta los scripts que puedan haber en la web*/
STATUS scriptEXE(char * root, int usuario, TIPO_SCRIPT tipo){
    FILE * fp;
    char * buff;
    char ruta[4096];
    char rutaTemporal[WORD_SIZE];
  
    int size_f;
    
    if(root !=NULL){
        if(tipo!=NULL){
            strcpy(rutaTemporal, configuracion_servidor->server_root);
            strcat(rutaTemporal, "/aux.txt");
            
            if(tipo == PHP)
                strcpy(ruta,"php ");
            else if(tipo == PYTHON)
                strcpy(ruta,"python ");
            
            strcat(ruta,root);
            strcat(ruta, " > "); 
            strcat(ruta,rutaTemporal);
            
            system(ruta);

            fp = fopen(rutaTemporal, "r"); 
            if(!fp){
            syslog(LOG_ERR,"Error executing script");
            return ERROR;  
            }
        
            write(usuario,"Content-Type: text/plain\r\n",26);

            fseek(fp, 0L, SEEK_END);
            size_f= ftell(fp);
             char resp[100];
            sprintf(resp,"Content-Length: %d\r\n",size_f);
            write(usuario, resp, strlen(resp));
            write(usuario,"\r\n",2);
            fseek(fp,0L,SEEK_SET);
            buff=(char *)malloc(sizeof(char)*size_f);
            fread(buff,size_f, 1, fp);
            write(usuario, buff, size_f);
            memset(ruta,0,strlen(ruta));
            strcpy(ruta, "rm ");
            strcat(ruta, rutaTemporal);
            system(ruta); 
            fclose(fp);
            free(buff);
            
            return OK;  
    }else{
        return ERROR;
    }  
    }else{
        return ERROR;
    }

}

/*Esta funcion procesa las peticiones GET del usuario*/
STATUS procesarGET(int usuario, char * fichero_de_inicio){
        int size_f;
        char ruta[4096],flagRaiz[4096];
        char * tokens, *ext, * buff;
        FILE * f;
        int aux = NULL;

        if(fichero_de_inicio!=NULL){
       	strcpy(flagRaiz,configuracion_servidor->server_root);
        strcat(flagRaiz,"/");
        if(strcmp(fichero_de_inicio,flagRaiz)==0){
                    
            send(usuario, "HTTP/1.1 200 OK\r\n", 24,0);
            f = fopen(fichero_de_inicio,"r");
            
        }
        else{

	        tokens=strtok(fichero_de_inicio,"?");
            strcpy(ruta,tokens);          
            while((tokens=strtok(aux,"=")) !=NULL){
                tokens=strtok(aux,"&");
                strcat(ruta," ");
                strcat(ruta, tokens);          
                       
            }
            
            
            f = fopen(fichero_de_inicio,"r");
            
            if(!f){
                memset(fichero_de_inicio,0,strlen(fichero_de_inicio));
                send(usuario, "HTTP/1.1 404 Not Found\r\n", 24,0);
                f = fopen(fichero_de_inicio,"r");
         	    if(!f){
		            return ERROR;
	            }    
            }
            else{
                write(usuario, "HTTP/1.1 200 OK\r\n", 17);
                           
            }
        }
        
        /*Se envia la fecha local*/
        char mi_fecha[50] = " ";
        time_t tiempo = time(NULL);    
        struct tm *tiempolocal = localtime(&tiempo);
        strftime(mi_fecha, 50,"mi_fecha: %a, %d %b %Y %H:%M:%S %Z \r\n",tiempolocal);
        write(usuario, mi_fecha, strlen(mi_fecha));


        /*Se envia el nombre o frima del servidor*/
         char resp[100];    
        sprintf(resp,"Server: %s\r\n",configuracion_servidor->server_signature);
        write(usuario, resp, strlen(resp));
            
        /*Se obtiene la extension del fichero*/          
        ext=strchr(fichero_de_inicio,'.');

        if(strcmp(ext, ".py") == 0){
             scriptEXE(ruta, usuario, PYTHON);
        }
        else if(strcmp(ext, ".php") == 0){
             scriptEXE(ruta, usuario, PHP);
        }
        else{

            if(sendExt(usuario, ext) == ERROR)
                return ERROR;

            fechaModificada(usuario, fichero_de_inicio);

            fseek(f, 0L, SEEK_END);
            size_f= ftell(f);

            /*Se envia el tamanio de la respuesta*/
            char resp[100];
            sprintf(resp,"Content-Length: %d\r\n",size_f);
            write(usuario, resp, strlen(resp));
    
         

            write(usuario,"\r\n",2);
        
            fseek(f,0L,SEEK_SET);
     
            buff=(char *)malloc(sizeof(char)*size_f);
            fread(buff,size_f, 1, f);

            write(usuario, buff, size_f);
            free(buff);      
            
        }
         
        fclose(f);
        return OK;
        }else{
            return ERROR;
        }

}  

/*Esta funcion se encarga de procesar las funciones POST del usuario*/
STATUS postEXE(int usuario, char * fichero_de_inicio, char * argumentos){
        int size_f = 0;
        char ruta[100];
        char * tokens = NULL, *ext = NULL, * buff = NULL;
        FILE * f = NULL;
        int aux = NULL;
        if(argumentos!=NULL){
                if(fichero_de_inicio == NULL){
                    memset(fichero_de_inicio,0,strlen(fichero_de_inicio));
                    send(usuario, "HTTP/1.1 200 OK\r\n", 24,0);
                    f = fopen(fichero_de_inicio,"r");
                }
                else{
                    strcpy(ruta,fichero_de_inicio); 
                    tokens=strtok(argumentos,"=");
                    tokens=strtok(aux,"&"); 
                    strcat(ruta," ");
                    strcat(ruta,tokens);        
                    while((tokens=strtok(aux,"=")) !=NULL){
                        tokens=strtok(aux,"&");
                        strcat(ruta," ");
                        strcat(ruta, tokens);          
                            
                    }

            f = fopen(fichero_de_inicio,"r");
                    
            if(!f){
            memset(fichero_de_inicio,0,strlen(fichero_de_inicio));
            send(usuario, "HTTP/1.1 404 Not Found\r\n", 24,0);          
            f = fopen(fichero_de_inicio,"r");
            if(!f){		   
                return ERROR;
                        }   
            }else{
                        write(usuario, "HTTP/1.1 200 OK\r\n", 20);
                    }
                }

                /*Se envia la fecha local*/
                char mi_fecha[50] = " ";
                time_t tiempo = time(NULL);    
                struct tm *tiempolocal = localtime(&tiempo);
                strftime(mi_fecha, 50,"mi_fecha: %a, %d %b %Y %H:%M:%S %Z \r\n",tiempolocal);
                write(usuario, mi_fecha, strlen(mi_fecha));
               

                /*Se envia el nombre o firma del servidor*/
                char resp[100];    
                sprintf(resp,"Server: %s\r\n",configuracion_servidor->server_signature);
                write(usuario, resp, strlen(resp));
                
                /*Se obtiene la extension del fichero*/
                ext=strchr(fichero_de_inicio,'.');
                if(strcmp(ext, ".php") == 0 ){
                    scriptEXE(ruta, usuario, PHP);
                    
                } 
                else if(strcmp(ext, ".py") == 0){
                    scriptEXE(ruta, usuario, PYTHON);
                    
                }
                else{
                    if(sendExt(usuario, ext) != OK)
                        return ERROR;

                    fechaModificada(usuario, fichero_de_inicio);

                    fseek(f, 0L, SEEK_END);
                    size_f= ftell(f);
                    

                    /*Se envia el tamanio de la respuesta*/
                    char resp[100];
                    sprintf(resp,"Content-Length: %d\r\n",size_f);
                    write(usuario, resp, strlen(resp));
    
                    
                    write(usuario,"\r\n",2);

                    fseek(f,0L,SEEK_SET);
                    buff=(char *)malloc(sizeof(char)*size_f);
                    fread(buff,size_f, 1, f);

                    write(usuario, buff, size_f);
                
                }
            fclose(f);   

            return OK;
        }else{
            return ERROR;
        }
}




/*Esta funcion se encarga de procesar las peticiones, ya sean POST o GET o OPTIONS*/
void * peticionEXE(void* conexion_usuario){
    
	int flag=0;
	char buf[4096]={'\0'}, flagRaiz[100];
    const char *ruta, *metodo1;
    char *metodo2;
	int pret, minor_version;
	struct phr_header headers[200];
	size_t tamanio = 0, tamanio_previo = 0, metodo1_len, longitud_de_la_ruta, cabeceras;
	ssize_t aux;
    char * tokens = NULL;

    if(conexion_usuario!=NULL){
        flag=*((int *)conexion_usuario);
        
        pthread_detach(pthread_self());

        do{
            while(1){
                while ((aux = read(flag, buf + tamanio, sizeof(buf) - tamanio)) == -1 && errno == EINTR);
            
                if (aux <= 0){
                    close(flag);
                    return NULL;
                }
                tamanio_previo = tamanio;
                tamanio =tamanio + aux;
        
                cabeceras = sizeof(headers) / sizeof(headers[0]);
                
                pret = phr_parse_request(buf, tamanio, &metodo1, &metodo1_len, &ruta, &longitud_de_la_ruta,&minor_version, headers, &cabeceras, tamanio_previo);
                if (pret > 0)
                    break;
                else if (pret == -1){
                    write(flag, "HTTP/1.0 400 ERROR\r\n", 16);
                    close(flag);
                    return NULL;
                }	
                
                assert(pret == -2);
                if (tamanio == sizeof(buf)){
                    close(flag);
                    return NULL;
                }
                
            }
        
                
            metodo2 = (char*)malloc(sizeof(char)*(int)metodo1_len);
            sprintf(metodo2,"%.*s",(int)metodo1_len, metodo1);

            sprintf(flagRaiz,"%s%.*s",configuracion_servidor->server_root,(int)longitud_de_la_ruta, ruta);

        
            if(strcmp(metodo2, "GET") == 0){
                
                if(procesarGET(flag,flagRaiz) != OK)
                    return NULL;
            
            }
            else if(strcmp(metodo2, "POST")==0){
                tokens=strtok((char *)headers[cabeceras-1].value,"\r\n\r\n");
                tokens=strtok(NULL,"\r\n\r\n");

                postEXE(flag, flagRaiz, tokens);
                
            
            }
            else if(strcmp(metodo2, "OPTIONS") == 0){
                /*Se escriben las opciones posibles*/
                write(flag, "HTTP/1.1 200 OK\r\n", 20);
                write(flag, "ALLOW: GET, POST, OPTIONS\r\n", 27);

                /*Se envia la fecha local*/
                char mi_fecha[50] = " ";
                time_t tiempo = time(NULL);    
                struct tm *tiempolocal = localtime(&tiempo);
                strftime(mi_fecha, 50,"mi_fecha: %a, %d %b %Y %H:%M:%S %Z \r\n",tiempolocal);
                write(flag, mi_fecha, strlen(mi_fecha));
    

                /*Se envia el nombre o firma del servidor*/
                char resp[100];    
                sprintf(resp,"Server: %s\r\n",configuracion_servidor->server_signature);
                write(flag, resp, strlen(resp));
                    
            }
            else{
                write(flag, "HTTP/1.1 400 ERROR\r\n", 20);
            }
            
            memset(buf,0,strlen(buf));
            tamanio=0;
        
            
            memset(flagRaiz,0,strlen(flagRaiz));
            free(metodo2);

        }while(minor_version==1);

        close(flag);
        pthread_exit(NULL);
    }else{
        return NULL;
    }
}



/*Ejecucion principal del programa*/
int main(int argc, char **argv){
	
  pthread_t numHilos = 0;
  int flag=0;
  int conexion_usuario; 
  socklen_t longc; 
  struct sockaddr_in servidor, usuario;
 
  if (signal (SIGINT, controlador_SIGINT) == SIG_ERR) {
    syslog(LOG_ERR, "Error creating signal");
	exit(EXIT_FAILURE);
  } 

  /*Creacion del server*/
  Config_Server * newConfig_Server = NULL;
  newConfig_Server = (Config_Server*)malloc(sizeof(Config_Server)); 
  configuracion_servidor = newConfig_Server;
  if(!configuracion_servidor){
    syslog(LOG_ERR, "Error creando la configuracion del servidor");
	exit(EXIT_FAILURE);
  }

/*Leer la configuración del fichero. Se leen todos sus atributos*/
    FILE * f;
    char linea_leida[WORD_SIZE];
    char * tokens = NULL;
    int aux = NULL;
    f = fopen("server.conf", "r");
    if (!f){ 
        exit(EXIT_FAILURE);
    }
   
    while(fgets(linea_leida, WORD_SIZE,f)){ 
        if(strncmp(linea_leida,"#",1) != 0){ 
            tokens=strtok(linea_leida,"=");
            
            if(strcmp(tokens, "server_root") == 0){
                tokens=strtok(aux,"\n");
                strcpy(configuracion_servidor->server_root,tokens);
            }
            else if(strcmp(tokens, "max_clients")== 0){
                tokens=strtok(aux, "\n");
                configuracion_servidor->max_clients=atoi(tokens);
            }
            else if(strcmp(tokens, "server_signature") == 0){
                tokens=strtok(aux, "\n");
                strcpy(configuracion_servidor->server_signature,tokens);
            }

            else if(strcmp(tokens, "listen_port") == 0){
                tokens=strtok(aux, "\n");
                configuracion_servidor->port=atoi(tokens);
            }
           
        }

    }
    fclose(f);
  

  /*Se crea el socket*/
  syslog (LOG_INFO, "Creating socket");
  conexion = socket(AF_INET, SOCK_STREAM, 0); 
  if(conexion<0){
	  syslog(LOG_ERR, "Error creando el socket");
	  exit(EXIT_FAILURE);
  }
  bzero((char *)&servidor, sizeof(servidor)); 
  servidor.sin_family = AF_INET; 
  servidor.sin_port = htons(configuracion_servidor->port);
  servidor.sin_addr.s_addr = INADDR_ANY; 
  bzero((void *)&(servidor.sin_zero), 8);

  syslog (LOG_INFO, "Binding socket");
  if(bind(conexion, (struct sockaddr *)&servidor, sizeof(servidor)) < 0){ 
    syslog(LOG_ERR, "Error bindeando el socket");
    exit(EXIT_FAILURE);
  }
  
  syslog (LOG_INFO, "Esperando conexiones");
  if(listen(conexion, configuracion_servidor->max_clients)<0){ 
	syslog(LOG_ERR, "Error escuchando");
	exit(EXIT_FAILURE);
  }
  
  printf("Puerto %d\n", ntohs(servidor.sin_port));
  longc = sizeof(usuario); 
  printf("Antes de demonizar");
  demonizar();
  printf("Demonizado");
  for( ; ; ){
	  conexion_usuario = accept(conexion, (struct sockaddr *)&usuario, &longc); 
	  if(conexion_usuario<0){
		syslog(LOG_ERR, "Error escuchando peticiones");
		exit(EXIT_FAILURE);
	  }
	  flag=conexion_usuario;
       
	  if (pthread_create(&numHilos, NULL, peticionEXE, &flag) != 0){
          syslog(LOG_ERR, "Error creando hilos");
		  exit(EXIT_FAILURE);
      }
		
   }
  close(conexion);
  /*Se libera el servidor*/
  free(configuracion_servidor);
  return 0;
}


