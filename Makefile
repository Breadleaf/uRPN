ROOT := $(shell git rev-parse --show-toplevel)
INPUTS := $(wildcard $(ROOT)/src/*.c)

all: help

help:
	@echo "targets:"
	@echo "help compile deep_clean"

amalgamate:
	uv run ./amalgamate.py
	
compile: amalgamate
	clang -c $(INPUTS) -I$(ROOT)/
	ar rcs librpn.a librpn.o

clean:
	rm -i librpn*

deep_clean:
	git clean -Xdi
