import time

def algoritmo(n):
    
    contador = 0
    
    for i in range(n): # O(n)
       j=1
       while j<n:
        contador += 1
       j *= 2

    return contador # El tiempo de ejecución total es O(n^2) debido a los dos bucles anidados, aunque el segu...

tamaños = [100, 200, 400, 800]

for n in tamaños: # O(1) para cada tamaño de entrada
    inicio = time.time() # O(1)
    
    algoritmo(n) # O(n^2)
    
    fin = time.time()
    
    print("n =", n, "tiempo =", fin - inicio)