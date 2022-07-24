import requests
import urllib
import itertools
import discord
import logging
import tempfile
from io import BytesIO
from .resources import Resource
from .utils import Timer

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class FifteenAIClient(Resource):
    _API_ROOT_URL = 'https://api.15.ai/'
    _CDN_ROOT_URL = 'https://cdn.15.ai/'
    _BASE_HEADERS = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
    }

    def __init__(self, text, character, emotion='Contextual'):
        super().__init__(f'FIFTEENAI__{character}__{text}')
        self.text = text
        self.character = character
        self.emotion = emotion
        self._wavNames = []
        self._wavs = {}

    def getAudioSource(self, i=0):
        # byteStream = BytesIO(self.getIthWav(i))
        # byteStream.seek(0)
        # audioSource = discord.FFmpegPCMAudio(byteStream, pipe=True)

        with tempfile.TemporaryFile() as f:
            f.write(self.getIthWav(i))
            f.seek(0)
            audioSource = discord.FFmpegPCMAudio(f, pipe=True)

        return audioSource

    def getIthWav(self, i):
        return self._getWav(self.getWavNames()[i])

    def getWavNames(self):
        if not self._wavNames:
            self._wavNames = self._submitRequest()
        return self._wavNames

    def _checkResponse(self, resp):
        log.debug(str(resp))
        if not 200 <= resp.status_code < 300:
            raise RuntimeError(resp.text)

    def _getHeaders(self, headerDict=None):
        headerDict = headerDict or {}
        return self._BASE_HEADERS.update(headerDict)

    # def getTTS(self, text, character, emotion='Contextual', i=0):
    #     wavNames = self.submitRequest(text, character, emotion=emotion)
    #     return self.getWav(wavNames[i])

    def _submitRequest(self):
        url = urllib.parse.urljoin(self._API_ROOT_URL, '/app/getAudioFile5')
        payload = {'text': self.text, 'character': self.character, 'emotion': self.emotion}
        headers = self._getHeaders({
            'content-type': 'application/json;charset=UTF-8',
            'accept': 'application/json, text/plain, */*',
        })
        log.debug('Generating Wavs, this may take a moment.')
        with Timer('Time to generate Wavs', log.info):
            resp = requests.post(url, data=payload)  ##TODO: this should be async
        self._checkResponse(resp)
        if not resp.json().get('wavNames'):
            raise RuntimeError(f'No wavNames returned from 15.ai')
        wavNames = resp.json()['wavNames']
        log.debug(f'Got wavNames: {wavNames}')
        return wavNames

    def _getWav(self, wavName):
        if wavName in self._wavs:
            return self._wavs[wavName]
        url = urllib.parse.urljoin(self._CDN_ROOT_URL, f'/audio/{wavName}')
        headers = self._getHeaders()
        log.debug(f'Downloading wav {wavName} this may take a moment.')
        with Timer(f'Time to get Wav {wavName}', log.info):
            resp = requests.get(url, headers=headers)  ##TODO: this should be async
        self._checkResponse(resp)
        self._wavs[wavName] = resp.content
        return self._wavs[wavName]

    @classmethod
    def getCharacters(cls):
        return list(itertools.chain.from_iterable(cls.getCharactersBySource().values()))

    @classmethod
    def getCharactersBySource(cls):
        # This seems to be hardcoded in https://15.ai/js/app.939e2617.js
        return {
            'Portal': [
                'GLaDos',
                'Wheatly',
                'Sentry Turret',
                'Chell',
            ],
            'SpongeBob SquarePants': [
                'SpongeBob SquarePants',
            ],
            'Aqua Teen Hunger Force': [
                'Carl Brutananadilewski',
            ],
            'Team Fortress 2': [
                'Miss Pauling',
                'Scout',
                'Soldier',
                'Demoman',
                'Heavy',
                'Engineer',
                'Medic',
                'Sniper',
                'Spy',
            ],
            'The Stanley Parable': [
                'The Narrator',
                'Stanley',
            ],
            '2001: A Space Odyssey': [
                'HAL 9000',
            ],
            'Doctor Who': [
                'Tenth Doctor',
            ],
            'Undertale': [
                'Sans',
            ],
        }

def main():
    client = FifteenAIClient()
    client.getTTS('test', 'SpongeBob SquarePagnts')

if __name__ == '__main__':
    main()