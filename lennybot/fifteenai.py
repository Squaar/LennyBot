import requests
import urllib
import itertools
import discord
from io import BytesIO
from .resources import Resource

class FifteenAIClient(Resource):
    _API_ROOT_URL = 'https://api.15.ai/'
    _CDN_ROOT_URL = 'https://cdn.15.ai/'
    _BASE_HEADERS = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
    }

    def getAudioSource(self, text, character):
        return discord.FFmpegPCMAudio(BytesIO(self.getTTS(text, character)), pipe=True)

    def _checkResponse(self, resp):
        if not 200 <= resp.status_code < 300:
            raise RuntimeError(resp.text)

    def _getHeaders(self, headerDict=None):
        headerDict = headerDict or {}
        return self._BASE_HEADERS.update(headerDict)

    def getTTS(self, text, character, emotion='Contextual', i=0):
        wavNames = self.submitRequest(text, character, emotion=emotion)
        return self.getWav(wavNames[i])

    def submitRequest(self, text, character, emotion='Contextual'):
        url = urllib.parse.urljoin(self._API_ROOT_URL, '/app/getAudioFile5')
        payload = {'text': text, 'character': character, 'emotion': emotion}
        headers = self._getHeaders({
            'content-type': 'application/json;charset=UTF-8',
            'accept': 'application/json, text/plain, */*',
        })
        resp = requests.post(url, data=payload)
        self._checkResponse(resp)
        if not resp.json().get('wavNames'):
            raise RuntimeError(f'No wavNames returned from 15.ai')
        return resp.json()['wavNames']

    def getWav(self, wavName):
        url = urllib.parse.urljoin(self._CDN_ROOT_URL, f'/audio/{wavName}')
        headers = self._getHeaders()
        resp = requests.get(url, headers=headers)
        self._checkResponse(resp)
        return resp.content

    def getCharacters(self):
        return itertools.chain.from_iterable(self.getCharactersBySource().values())

    def getCharactersBySource(self):
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