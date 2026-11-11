# µRPN (micro reverse polish notation)

## example compile

```
make compile
clang [your file] -I[path to librpn_amalgamated.h] -L[path to librpn.a] -lrpn -o [final exec name]
```

## use in embedded

```
make amalgamate
mv ./librpn_amalgamated.* [path to your embedded project]
```
