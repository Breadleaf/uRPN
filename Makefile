ROOT := $(shell git rev-parse --show-toplevel)
INPUTS := $(wildcard $(ROOT)/src/*.c)

all:
	clang $(INPUTS)

deep_clean:
	git clean -Xdi
