
from requests_oauthlib import OAuth2Session
import flask
import os
import logging
import threading
import asyncio

logging.basicConfig(level=logging.INFO, format='%(levelname)s-%(name)s-%(message)s')
logger = logging.getLogger(__name__)


class LennyService(flask.Flask):

    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._OAUTH2_CLIENT_ID = os.environ['LENNYBOT_OAUTH2_CLIENT_ID']
        self._OAUTH2_CLIENT_SECRET = os.environ['LENNYBOT_OAUTH2_CLIENT_SECRET']
        # self.__OAUTH2_REDIRECT_URI = 'http://localhost:5000/callback'
        self._OAUTH2_REDIRECT_URI = os.environ['LENNYBOT_OAUTH2_REDIRECT_URI']
        self._API_BASE_URL = os.environ.get('API_BASE_URL', 'https://discordapp.com/api')
        self._AUTHORIZATION_BASE_URL = self._API_BASE_URL + '/oauth2/authorize'
        self._TOKEN_URL = self._API_BASE_URL + '/oauth2/token'
        self.config['SECRET_KEY'] = self._OAUTH2_CLIENT_SECRET

        if 'http://' in self._OAUTH2_REDIRECT_URI:
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'

        self._bot = bot
        self.route('/')(self.index)
        self.route('/callback')(self.callback)
        self.route('/lennybot')(self.lenny)
        self.route('/channels')(self.channels)

    def run(self, *args, **kwargs):
        threading.current_thread().setName('t_lennyservice')
        super().run(*args, **kwargs)

    def token_updater(self, token):
        flask.session['oauth2_token'] = token

    def make_session(self, token=None, state=None, scope=None):
        return OAuth2Session(
            client_id = self._OAUTH2_CLIENT_ID,
            token = token,
            state = state,
            scope = scope,
            redirect_uri = self._OAUTH2_REDIRECT_URI,
            auto_refresh_kwargs = {
                'client_id': self._OAUTH2_CLIENT_ID,
                'client_secret': self._OAUTH2_CLIENT_SECRET,
            },
            auto_refresh_url = self._TOKEN_URL,
            token_updater = self.token_updater,
            # token_updater = (lambda x: session['oauth2_token'] = x),
        )

    def index(self):
        scope = flask.request.args.get('scope', 'identify guilds messages.read')
        # permissions = request.args.get('permissions', 0x00000008)
        discord = self.make_session(scope=scope.split(' '))
        # authorization_url, state = discord.authorization_url(_AUTHORIZATION_BASE_URL, permissions=permissions)
        authorization_url, state = discord.authorization_url(self._AUTHORIZATION_BASE_URL)
        flask.session['oauth2_state'] = state
        return flask.redirect(authorization_url)

    def callback(self):
        if flask.request.values.get('error'):
            return flask.request.values['error']
        discord = self.make_session(state=flask.session.get('oauth2_state'))
        token = discord.fetch_token(
            self._TOKEN_URL,
            client_secret = self._OAUTH2_CLIENT_SECRET,
            authorization_response = flask.request.url
        )
        flask.session['oauth2_token'] = token
        flask.session['user_id'] = discord.get(self._API_BASE_URL + '/users/@me').json()['id']
        return flask.redirect(flask.url_for('.lenny'))

    def lenny(self):
        discord = self.make_session(token=flask.session.get('oauth2_token'))
        user = discord.get(self._API_BASE_URL + '/users/@me').json()
        guilds = discord.get(self._API_BASE_URL + '/users/@me/guilds').json()
        connections = discord.get(self._API_BASE_URL + '/users/@me/connections').json()
        ##TODO: how do we handle standalone service w/ no bot? should we need to?
        return flask.jsonify(user=user, guilds=guilds, connections=connections, sessionid=flask.session.get('user_id'))

    def channels(self):
        # discord = self.make_session(token=flask.session.get('oauth2_token'))
        # self._bot.loop.call_soon_threadsafe(self._bot.message_squaar, 'test')
        logger.info('loop from service: %s' % id(self._bot.loop))
        asyncio.run_coroutine_threadsafe(self._bot.message_squaar('test'), self._bot.loop)
        return flask.jsonify(channels=list(self._bot.channels.keys()))


# This isn't really meant to be run without the bot. Things will break! Try running from main.py instead
if __name__ == '__main__':
    LennyService(None, __name__).run(host='0.0.0.0')
