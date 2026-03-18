class Pila:
    
    def __init__(self):
        self.items = []
        
    def push(self, elemento):
        self.items.append(elemento)
        
    def pop(self):
        return self.items.pop()
        
    def mostrar(self):
        print(self.items)

pila = Pila()

pila.push(10)
pila.push(20)
pila.push(30)
pila.push(40)
pila.push(50)
pila.push(60)
pila.push(70)
pila.push(80)
pila.push(90)
pila.push(100)

pila.mostrar()

print("Elemento eliminado:", pila.pop())
print("Elemento eliminado:", pila.pop())
print("Elemento eliminado:", pila.pop())

pila.mostrar()