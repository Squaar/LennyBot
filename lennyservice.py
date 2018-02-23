
from flask import Flask, session, redirect, request, url_for, jsonify
from requests_oauthlib import OAuth2Session
import os
import logging
import lennybot

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

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = OAUTH2_CLIENT_SECRET

if 'http://' in OAUTH2_REDIRECT_URI:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'


def token_updater(token):
    session['oauth2_token'] = token


def make_session(token=None, state=None, scope=None):
    session = OAuth2Session(
        client_id=OAUTH2_CLIENT_ID,
        token=token,
        state=state,
        scope=scope,
        redirect_uri=OAUTH2_REDIRECT_URI,
        auto_refresh_kwargs={
            'client_id': OAUTH2_CLIENT_ID,
            'client_secret': OAUTH2_CLIENT_SECRET,
        },
        auto_refresh_url=TOKEN_URL,
        token_updater=token_updater,
    )
    session.headers = {
        'Authorization': 'Bot ' + OAUTH2_BOT_TOKEN
    }
    return session


@app.route('/')
def index():
    scope = request.args.get(
        'scope',
        'identify guilds messages.read'
    )
    permissions = request.args.get(
        'permissions',
        0x00000008
    )
    discord = make_session(scope=scope.split(' '))
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL, permissions=permissions)
    session['oauth2_state'] = state
    return redirect(authorization_url)


# I think this token is the authorization token needed for requests
# probably shouldn't save that in the session... need to return to the page so it can be sent in subsequent requests
# should be sent back to microservice in post arg
@app.route('/callback')
def callback():
    if request.values.get('error'):
        return request.values['error']
    discord = make_session(state=session.get('oauth2_state'))
    token = discord.fetch_token(
        TOKEN_URL,
        client_secret=OAUTH2_CLIENT_SECRET,
        authorization_response=request.url
    )
    session['oauth2_token'] = token
    return redirect(url_for('.me'))


@app.route('/me')
def me():
    discord = make_session(token=session.get('oauth2_token'))
    user = discord.get(API_BASE_URL + '/users/@me').json()
    guilds = discord.get(API_BASE_URL + '/users/@me/guilds').json()
    connections = discord.get(API_BASE_URL + '/users/@me/connections').json()
    ##TODO: how do we handle standalone service w/ no bot? should we need to? 
    return jsonify(user=user, guilds=guilds, connections=connections)


##TODO: need to refactor lennybot commands to take args for this to work
# @app.route('/hellotest')
# def hello_test():
#     discord = make_session(token=session.get('oauth2_token'))


@app.route('/channels')
def channels():
    discord = make_session(token=session.get('oauth2_token'))
    return jsonify(lennybot_channels=str(lennybot.channels))


if __name__ == '__main__':
    app.run(host='0.0.0.0')
