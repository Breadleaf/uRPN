#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define STACK_SIZE (1 << 10)
#define LINE_SIZE (1 << 8)

static double stack[STACK_SIZE];
static size_t depth = 0 ;

static int push(double v) {
	if (depth >= STACK_SIZE) return 0;
	stack[depth++] = v;
	return 1;
}

static int pop(double *out) {
	if (depth == 0) return 0;
	*out = stack[--depth];
	return 1;
}

static int is_space(char c) {
	return c == ' ' || c == '\t' || c == '\n' || c == '\r';
}

static int run_token(const char *token, size_t length) {
	char *end;
	double v = strtod(token, &end);
	if (end == token + length) {
		if (!(push(v))) {
			puts("error: stack overflow");
			return 0;
		}
		return 1;
	}

	if (length == 1 && strchr("+-*/", token[0])) {
		if (depth < 2) {
			puts("error: stack underflow");
			return 0;
		}
		double b = stack[depth - 1];
		double a = stack[depth - 2];
		double r;
		switch (token[0]) {
			case '+':
				r = a + b;
				break;
			case '-':
				r = a - b;
				break;
			case '*':
				r = a * b;
				break;
			case '/':
				if (b == 0) {
					puts("error: divide by zero");
					return 0;
				}
				r = a / b;
				break;
		}
		depth -= 2;
		push(r);
		return 1;
	}

	printf("error: unknown word '%.*s'\n", (int)length, token);
	return 0;
}

int main() {
	char line[LINE_SIZE];
	for (;;) {
		printf("> ");
		fflush(stdout);
		if (!fgets(line, sizeof line, stdin)) break; // ctrl-d ends program

		const char *p = line;
		while (*p) {
			while (*p && is_space(*p)) p++; // skip spaces
			if (!*p) break;
			const char *start = p;
			while (*p && !is_space(*p)) p++; // find end of token
			if (!run_token(start, (size_t)(p - start))) break;
		}

		if (depth > 0) {
			printf("decimal:    %F\n", stack[depth - 1]);
			printf("scientific: %G\n", stack[depth - 1]);
		}
	}

	return 0;
}
