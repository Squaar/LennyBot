
from requests_oauthlib import OAuth2Session
import flask
import os
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OAUTH2_CLIENT_ID = os.environ['LENNYBOT_OAUTH2_CLIENT_ID']
OAUTH2_CLIENT_SECRET = os.environ['LENNYBOT_OAUTH2_CLIENT_SECRET']
OAUTH2_BOT_TOKEN = os.environ['LENNYBOT_OAUTH2_BOT_TOKEN']
# OAUTH2_REDIRECT_URI = 'http://localhost:5000/callback'
OAUTH2_REDIRECT_URI = os.environ['LENNYBOT_OAUTH2_REDIRECT_URI']
API_BASE_URL = os.environ.get('API_BASE_URL', 'https://discordapp.com/api')
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'


if 'http://' in OAUTH2_REDIRECT_URI:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'


class LennyService(flask.Flask):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bot = bot
        self.config['SECRET_KEY'] = OAUTH2_CLIENT_SECRET
        self.route('/')(self.index)
        self.route('/callback')(self.callback)
        self.route('/lennybot')(self.lenny)
        self.route('/channels')(self.channels)

    def token_updater(self, token):
        flask.session['oauth2_token'] = token

    def make_session(self, token=None, state=None, scope=None):
        return OAuth2Session(
            client_id = OAUTH2_CLIENT_ID,
            token = token,
            state = state,
            scope = scope,
            redirect_uri = OAUTH2_REDIRECT_URI,
            auto_refresh_kwargs = {
                'client_id': OAUTH2_CLIENT_ID,
                'client_secret': OAUTH2_CLIENT_SECRET,
            },
            auto_refresh_url = TOKEN_URL,
            token_updater = self.token_updater,
            # token_updater = (lambda x: session['oauth2_token'] = x),
        )

    def index(self):
        scope = flask.request.args.get('scope', 'identify guilds messages.read')
        # permissions = request.args.get('permissions', 0x00000008)
        discord = self.make_session(scope=scope.split(' '))
        # authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL, permissions=permissions)
        authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
        flask.session['oauth2_state'] = state
        return flask.redirect(authorization_url)

    def callback(self):
        if flask.request.values.get('error'):
            return flask.request.values['error']
        discord = self.make_session(state=flask.session.get('oauth2_state'))
        token = discord.fetch_token(
            TOKEN_URL,
            client_secret = OAUTH2_CLIENT_SECRET,
            authorization_response = flask.request.url
        )
        flask.session['oauth2_token'] = token
        flask.session['user_id'] = discord.get(API_BASE_URL + '/users/@me').json()['id']
        return flask.redirect(flask.url_for('.lenny'))

    def lenny(self):
        discord = self.make_session(token=flask.session.get('oauth2_token'))
        user = discord.get(API_BASE_URL + '/users/@me').json()
        guilds = discord.get(API_BASE_URL + '/users/@me/guilds').json()
        connections = discord.get(API_BASE_URL + '/users/@me/connections').json()
        ##TODO: how do we handle standalone service w/ no bot? should we need to?
        return flask.jsonify(user=user, guilds=guilds, connections=connections, sessionid=flask.session.get('user_id'))

    ##TODO: need to refactor lennybot commands to take args for this to work
    # @app.route('/hellotest')
    # def hello_test():
    #     discord = make_session(token=session.get('oauth2_token'))

    ##TODO: get communication with bot working
    # https://docs.python.org/3/library/asyncio-dev.html#asyncio-multithreading
    def channels(self):
        discord = self.make_session(token=flask.session.get('oauth2_token'))
        self._bot.loop.call_soon_threadsafe(self._bot.message_squaar, 'test')
        future = asyncio.run_coroutine_threadsafe(self._bot.message_squaar('test'), self._bot.loop)
        return flask.jsonify(lennybot_channels=str(self._bot.channels))


if __name__ == '__main__':
    LennyService(None, __name__).run(host='0.0.0.0')
