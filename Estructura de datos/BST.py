Class Nodo:

def __init__(self, valor):
        self.valor = valor
        self.izq = None
        self.der = None


def insertar(raiz, valor):

    if raiz is None:
        return Nodo(valor)

    if valor < raiz.valor:
        raiz.izq = insertar(raiz.izq, valor)

    else:
        raiz.der = insertar(raiz.der, valor)

    return raiz

def inorden(nodo):

    if nodo:

        inorden(nodo.izq)

        print(nodo.valor)

        inorden(nodo.der)

raiz = None

valores = [50, 30, 70, 20, 40, 60, 80]

for v in valores:
    raiz = insertar(raiz, v)

inorden(raiz)