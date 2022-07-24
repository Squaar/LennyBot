import os
import logging
import discord
from . import utils

logging.basicConfig(level=logging.INFO, format='[%(asctime)s]%(levelname)s-%(name)s-%(message)s')
logger = logging.getLogger(__name__)

_RESOURCE_DIR = os.path.abspath('resources')

def _validate_path(path):
    if not utils.path_is_within(path, _RESOURCE_DIR):
        raise ValueError(f'Invalid resource path: {path}')

def _strip_resource_dir(path):
    if path.startswith(_RESOURCE_DIR):
        path = path[len(_RESOURCE_DIR + os.path.sep):]
    return path

class Resource:
    def __init__(self, name, alt_names=None, description=None):
        self.name = name
        self.alt_names = alt_names or tuple()
        self.description = description

    def __repr__(self):
        return f'<Resource {self.name}>'

    async def getAudioSource(self, *args, **kwargs):
        raise RuntimeError(f'Can\'t get AudioSource for vanilla Resource: {self}')

class LocalResource(Resource):
    def __init__(self, name, path, alt_names=None, description=None):
        super().__init__(name, alt_names=alt_names, description=description)
        self._path = path

    def __repr__(self):
        return f'<LocalResource {self.name}@{self._path}>'

    @property
    def path(self):
        path = os.path.abspath(os.path.join('resources', self._path))
        # if os.path.commonpath((_PATH_DIR, path)) != _PATH_DIR:
        # if not utils.path_is_within(path, _RESOURCE_DIR):
        #     raise ValueError(f'Invalid resource path: {path}')
        _validate_path(path)
        return path

    async def getAudioSource(self, *args, **kwargs):
        return discord.FFmpegPCMAudio(self.path)

class ResourceDictionary:
    resources = [
        LocalResource('voxfull', 'audio/raw/VOX_FULL.mp3', ('vox_full',), 'Full HL1 VOX announcer mp3'),
        LocalResource('voxintro', 'audio/voxintro.mp3', ('vox_intro'), 'VOX intro song 00:00:00'),
    ]

    _translation_rules = (
        (' ', '_'),
    )

    def initialize(self):
        self._scan_dir('audio/hl1')

    @classmethod
    def _translate_resource_name(cls, resource_name):
        resource_name = resource_name.strip().lower()
        for rule in cls._translation_rules:
            resource_name = resource_name.replace(rule[0], rule[1])
        return resource_name

    def find_resource_by_path(self, path):
        path = os.path.abspath(path)
        for resource in self.resources:
            if resource.path == path:
                return resource
        return None

    def get_all_resources(self):
        return self.resources

    def find_resource(self, resource_name):
        resource_name = self._translate_resource_name(resource_name)
        for resource in self.resources:
            if resource.name == resource_name or resource_name in resource.alt_names:
                return resource

    def add_resource(self, resource):
        self.resources.append(resource)

    def _scan_dir(self, dir, dryrun=False):
        absdir = os.path.abspath(os.path.join('resources', dir))
        _validate_path(absdir)
        logger.info(f'Scanning {absdir}')
        for dirpath, dirnames, filenames in os.walk(absdir):
            for filename in filenames:
                filepath = os.path.abspath(os.path.join(dirpath, filename))
                resource = self.find_resource_by_path(filepath)
                if not resource:
                    if dryrun:
                        logger.info(f'Scanned {filepath}')
                    else:
                        name = os.path.splitext(filename)[0]
                        path = _strip_resource_dir(filepath)
                        description = path
                        self.add_resource(LocalResource(name, path, description=description))
                        logger.info(f'Added resource to dictionary {name}: {filepath}')
                else:
                    logger.info(f'Found existing resource {resource.name} at {filepath}')

RESOURCE_DICTIONARY = ResourceDictionary()
RESOURCE_DICTIONARY.initialize()

if __name__ == '__main__':
    from pprint import pprint
    # pprint(get_all_resources())
    # print(ResourceDictionary.find_resource('voxintro').path)
    print(LocalResource('', './123/abc').path)