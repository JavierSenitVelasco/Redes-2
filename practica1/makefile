CC = gcc -pthread
CFLAGS = -Wall -ansi -pedantic -g
EXE = server

all : $(EXE) clean2


$(EXE): % : picohttpparser.o servidor.o 
	
	@${CC} ${CFLAGS} -o  $@ $^

servidor.o: src/servidor.c libs/picohttpparser.h src/types.h
	@${CC} ${CFLAGS} -c  $<



picohttpparser.o: libs/picohttpparser.c libs/picohttpparser.h
	@${CC} ${CFLAGS} -c  $<


clean :
	@rm -rf *\.o *~ $(EXE)

clean2 :
	@rm -rf *\.o *~ 
