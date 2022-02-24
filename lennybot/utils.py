import os.path

def path_is_within(path, dir):
    path = os.path.abspath(path)
    dir = os.path.abspath(dir)
    return os.path.commonpath((path, dir)) == dir