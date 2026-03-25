import uuid
from rich import print as rprint
from rich.tree import Tree
from graphviz import Digraph
from parse import parse
from model import Node

def build_rich_tree(node, tree=None):
    """Genera una estructura de árbol para la terminal usando Rich."""
    label = type(node).__name__
    
    # Añadir detalles si existen (valor o nombre)
    detail = ""
    if hasattr(node, 'value'): detail = f": [bold cyan]{node.value}[/]"
    elif hasattr(node, 'op'): detail = f": [bold yellow]'{node.op}'[/]"
    elif hasattr(node, 'name'): detail = f": [green]{node.name}[/]"
    
    current_tree = Tree(f"{label}{detail}") if tree is None else tree.add(f"{label}{detail}")

    for field_name, value in vars(node).items():
        if field_name in ['value', 'op', 'name']: continue
        
        if isinstance(value, list):
            for item in value:
                if isinstance(item, Node):
                    build_rich_tree(item, current_tree)
        elif isinstance(value, Node):
            build_rich_tree(value, current_tree)
            
    return current_tree

def build_graphviz(node, dot=None, parent_id=None):
    """Genera un archivo DOT para visualizar con Graphviz."""
    if dot is None:
        dot = Digraph(comment='AST B-Minor', node_attr={'shape': 'record', 'style': 'filled', 'fillcolor': 'lightblue'})

    node_id = str(uuid.uuid4())
    
    # Etiqueta amigable
    label = type(node).__name__
    if hasattr(node, 'value'): label = f"{label} | {node.value}"
    elif hasattr(node, 'op'): label = f"{label} | {node.op}"
    elif hasattr(node, 'name'): label = f"{label} | {node.name}"
    
    dot.node(node_id, label)

    if parent_id:
        dot.edge(parent_id, node_id)

    for field_name, value in vars(node).items():
        if field_name in ['value', 'op', 'name']: continue
        
        if isinstance(value, list):
            for item in value:
                if isinstance(item, Node):
                    build_graphviz(item, dot, node_id)
        elif isinstance(value, Node):
            build_graphviz(value, dot, node_id)

    return dot

def main():
    # 1. Crear archivo de prueba
    test_code = """
    main() {
        return 5 + 10 * 2;
    }
    """
    with open("test.bminor", "w") as f:
        f.write(test_code)

    # 2. Leer y parsear
    source = open("test.bminor").read()
    print("--- Analizando código B-Minor ---")
    ast = parse(source)

    if ast:
        # 3. Visualización en Terminal (Rich)
        print("\n[AST en Terminal]")
        rprint(build_rich_tree(ast))

        # 4. Visualización en Imagen (Graphviz)
        dot = build_graphviz(ast)
        dot.render("ast_output", format="png", cleanup=True)
        print("\n✅ AST generado con éxito en 'ast_output.png'")

if __name__ == "__main__":
    main()