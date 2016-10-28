CFLAGS?=-g -Wall -Wno-unused-variable -Wno-unused-label -Wno-unused-but-set-variable
#CFLAGS?=-g -Wall

all: main

main: main.c common.c output.c
	gcc $(CFLAGS) -omain $+

run: main
	main
run-gdb: main
	gdb main -ex "break abort" -ex "run"
start-gdb: main
	gdb main -ex "break abort" -ex "start"

.PHONY: gdb
