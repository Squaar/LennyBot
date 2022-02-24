import json
import os

def get_all_resources():
    path = os.path.join(os.getcwd(), 'resources', 'resources.json')
    with open(path) as f:
        resources = json.load(f)
    return resources

def find_resource(resource_name, resources=None):
    if resources is None:
        resources = get_all_resources()
    if not resources:
        return None
    for k, v in resources.items():
        if isinstance(v, dict):
            return find_resource(resource_name, resources=v)
        elif k == resource_name:
            return v


if __name__ == '__main__':
    from pprint import pprint
    pprint(get_all_resources())