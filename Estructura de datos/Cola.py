from collections import deque

# Creamos una cola vacía
cola = deque()

# Agregamos clientes a la cola (Equivalente a append en la imagen)
cola.append("Cliente 1") # Agregamos un cliente a la cola
cola.append("Cliente 2") # Agregamos otro cliente a la cola
cola.append("Cliente 3")

# Mostramos la cola completa
print(cola) # Mostramos la cola completa

# Atendemos al primer cliente (Cliente 1) y lo eliminamos de la cola
print("Atendiendo:", cola.popleft()) # Atendemos al primer cliente y lo eliminamos

# Mostramos la cola después de atender al primero
print(cola) # Quedando Cliente 2 y Cliente 3 en la cola