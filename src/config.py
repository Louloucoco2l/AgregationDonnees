#plutot que de s amuser avec les chemins a la main (merci chatgpt)

from pathlib import Path

class Node:
    """
    Représente un dossier sous forme d'objet dynamique.
    Exemple : paths.data.DVF.geocodes.brut
    """
    def __init__(self, path: Path):
        self._path = path

    @property
    def path(self):
        return self._path

    def __truediv__(self, other):
        """Permet d'utiliser paths.data / 'file.csv' """
        return self._path / other

    def __repr__(self):
        return f"Node({self._path})"


def build_tree(path: Path):
    node = Node(path)
    for item in path.iterdir():
        if item.is_dir():
            name = item.name.replace(" ", "_").replace("-", "_")
            if name == "path":
                continue  # Évite le conflit avec la propriété path
            setattr(node, name, build_tree(item))
    return node

PROJECT_ROOT = Path(__file__).resolve().parents[1]

paths = build_tree(PROJECT_ROOT)

