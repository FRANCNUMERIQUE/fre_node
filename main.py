import sys
import os
from fre_node.node import FRENode

# Ajoute le chemin du package interne
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "fre_node"))

if __name__ == "__main__":
    node = FRENode()
    node.start()
