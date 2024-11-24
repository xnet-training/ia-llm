from fnmatch import fnmatch
import os, re

def get_base_dir():
    base_dir = os.path.dirname(os.path.abspath(os.path.join(__file__,"../../")))
    print(f"Directorio Base: {base_dir}")
    return base_dir

def get_absolute_path(*relative_paths):
    return os.path.join(get_base_dir(), *relative_paths)
