"""Tabla de símbolos con soporte para alcances léxicos anidados."""
from __future__ import annotations
from collections import ChainMap
from dataclasses import dataclass, field
from typing import Any, Optional, List

from rich.table   import Table
from rich.console import Console
from rich         import print

try:
	# Intentar importar Node del módulo model
	from model import Node
except Exception:
	# Fallback mínimo si model.py no está disponible
	class Node:
		def __init__(self, name): self.name = name
		
console = Console()

class Symtab:
	"""Tabla de símbolos con soporte para alcances léxicos anidados.
	
	Implementación basada en ChainMap que mantiene una jerarquía padre-hijo
	de tablas de símbolos. Permite:
	- Crear alcances anidados para bloques, funciones, etc.
	- Buscar símbolos respetando la cadena padre (alcance léxico)
	- Detectar redeclaraciones y sombreado de variables
	- Imprimir el árbol completo de alcances para depuración
	"""
	class SymbolDefinedError(Exception):
		"""Excepción lanzada cuando se intenta redeclarar un símbolo con el mismo tipo
		en el mismo alcance.
		
		Esto indica que el símbolo ya existe en el alcance actual
		y se está intentando definir nuevamente, lo cual es un error.
		"""
		pass
		
	class SymbolConflictError(Exception):
		"""Excepción lanzada cuando existe un conflicto de tipos en la redeclaración.
		
		Ocurre cuando se intenta registrar un símbolo que ya existe en el alcance
		actual pero con una definición de tipo diferente (incompatible).
		"""
		pass
		
	# --- implementación
	
	def __init__(self, name: str, parent: Optional["Symtab"] = None):
		'''
		Crea un scope con nombre y (opcional) padre.
		- self._map: dict del scope actual (escrituras van aquí)
		- self.cm: ChainMap que encadena (self._map, parent.cm, ...)
		- self.entries: alias al dict del scope actual (compatibilidad)
		'''
		self.name: str = name
		self.parent: Optional["Symtab"] = parent
		self.children: List["Symtab"] = []
		
		self._map: dict[str, Any] = {}
		if parent is None:
			self.cm: ChainMap = ChainMap(self._map)
		else:
			# encadena con el ChainMap del padre
			self.cm: ChainMap = parent.cm.new_child(self._map)
			parent.children.append(self)
			
		# Compatibilidad con código existente
		self.entries = self._map
		
	# --- helpers privados
	
	def _type_of(self, obj: Any):
		'''
		Devuelve "tipo" compatible con tu chequeo previo.
		'''
		try:
			return obj.type
		except Exception:
			return type(obj)
			
	# --- API pública compatible
	
	def add(self, name: str, value: Any):
		'''
		Define un símbolo en *este scope*.
		- Si ya existe *en este mismo scope*:
		* mismo tipo  -> SymbolDefinedError
		* tipo distinto -> SymbolConflictError
		- Si existe sólo en padres, se permite *sombrar* (shadowing).
		'''
		if name in self._map:
			# chequeo de conflictos como el original
			existing = self._map[name]
			if self._type_of(existing) != self._type_of(value):
				raise Symtab.SymbolConflictError(f"Conflicto: '{name}' ya definido con tipo distinto en scope '{self.name}'")
			else:
				raise Symtab.SymbolDefinedError(f"Redefinición: '{name}' ya definido en scope '{self.name}'")
		self._map[name] = value
		return value
		
	def get(self, name: str):
		"""
		Recupera el símbolo buscando desde el scope actual hacia los padres.
		Devuelve None si no existe.
		"""
		# Usamos ChainMap para lookups; emula la recursión padre.get(...)
		if name in self.cm:
			return self.cm[name]
		return None
		
	# --- utilidades de depuración
	
	def print(self):
		'''
		Imprime esta tabla y recursivamente sus hijas (árbol de scopes).
		Muestra sólo el *scope actual* en cada nodo.
		'''
		table = Table(title=f"Symbol Table: '{self.name}'")
		table.add_column('key', style='cyan')
		table.add_column('value', style='bright_green')
		
		for k, v in self._map.items():
			if isinstance(v, Node):
				value = f"{v.__class__.__name__}({getattr(v, 'name', '?')})"
			else:
				value = f"{v}"
			table.add_row(k, value)
		print(table, '\n')
		
		for child in self.children:
			child.print()
			
	# --- extensiones opcionales

	def merged_view(self) -> dict:
		"""Vista efectiva (dict) del scope actual (interno > padres)."""
		return dict(self.cm)
		
	def lineage(self) -> list[str]:
		"""Lista de nombres de scopes desde global hasta éste."""
		out = []
		node: Optional[Symtab] = self
		while node:
			out.append(node.name)
			node = node.parent
		return list(reversed(out))
		
# --- Pequeña prueba manual (opcional)

if __name__ == "__main__":
	# Global
	g = Symtab("global")
	g.add("x", 1)
	
	# función f (hija de global)
	f = Symtab("function f", parent=g)
	f.add("x", 3)   # sombreo permitido
	f.add("a", 10)
	
	# bloque dentro de f
	b = Symtab("block", parent=f)
	b.add("t", True)
	
	# Lookups
	assert b.get("t") is True
	assert b.get("a") == 10
	assert b.get("x") == 3
	assert g.get("x") == 1
	assert g.get("a") is None
	
	# Print árbol
	g.print()
	
	# Vista unificada desde b
	# print(b.merged_view())