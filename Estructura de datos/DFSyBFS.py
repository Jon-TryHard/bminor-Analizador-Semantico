from collections import deque

class Nodo:

    def __init__(self, valor):
        self.valor = valor
        self.hijos = []


# Recorrido DFS (Depth First Search)
def dfs(nodo):

    print(nodo.valor)

    for hijo in nodo.hijos:
        dfs(hijo)


# Recorrido BFS (Breadth First Search) con visualización
def bfs(raiz):

    cola = deque([raiz])

    print("\nInicio BFS")
    print("Cola inicial:", [n.valor for n in cola])

    while cola:

        nodo = cola.popleft()

        print("\nVisitando nodo:", nodo.valor)

        for hijo in nodo.hijos:
            cola.append(hijo)
            print("  Agregando a la cola:", hijo.valor)

        print("Cola actual:", [n.valor for n in cola])


# Creación de nodos
A = Nodo("A")
B = Nodo("B")
C = Nodo("C")
D = Nodo("D")
E = Nodo("E")
F = Nodo("F")

# Construcción del árbol
A.hijos = [B, C, D]
B.hijos = [E, F]

# Ejecutar DFS
print("DFS")
dfs(A)

# Ejecutar BFS
print("\nBFS")
bfs(A)