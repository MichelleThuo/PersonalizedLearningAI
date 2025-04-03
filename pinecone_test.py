import os
import sys
import importlib

for mod in ['pinecone']:
    try:
        module = importlib.import_module(mod)
        print(f"{mod} version: {getattr(module, '__version__', 'unknown')}")
        print(f"{mod} path: {module.__file__}")
        print(f"{mod} dir: {[x for x in dir(module) if not x.startswith('_')]}")
    except ImportError as e:
        print(f"Error importing {mod}: {e}")