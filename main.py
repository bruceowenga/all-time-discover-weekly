import os
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from icecream import ic

from flask import Flask, request, url_for, session, redirect

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')

app = Flask(__name__)

app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = 'gh78erui(g&@099309$df!bgf'
TOKEN_INFO = 'token_info'

@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)


@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('save_discover_weekly'))


@app.route('/saveDiscoverWeekly')
def save_discover_weekly():

    try:
        token_info = get_token()
    except:
        print("User not logged in")
        return redirect("/")
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    my_user_id = sp.current_user()['id']

    all_time_discover_weekly_playlist_id = None
    discover_weekly_playlist_id = None

    current_playlists = sp.current_user_playlists()['items']
    ic(len(current_playlists))
    for playlist in current_playlists:
        ic(playlist['name'])
        if(playlist['name'] == "Discover Weekly"):
            discover_weekly_playlist_id = playlist['id']
        if(playlist['name'] == "All-Time Discover Weekly"):
            all_time_discover_weekly_playlist_id = playlist['id']

    if not discover_weekly_playlist_id:
        return("Discover Weekly Playlist not found")
    
    if not all_time_discover_weekly_playlist_id:
        new_playlist = sp.user_playlist_create(my_user_id, "All-Time Discover Weekly", public=True)
        all_time_discover_weekly_playlist_id = new_playlist['id']

    discover_weekly_playlist = sp.playlist_items(discover_weekly_playlist_id)
    song_uris = []
    for song in discover_weekly_playlist['items']:
        song_uri = song['track']['uri']
        song_uris.append(song_uri)
    sp.user_playlist_add_tracks(my_user_id, all_time_discover_weekly_playlist_id, song_uris)


def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        redirect(url_for('login', external=False))

    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

    return token_info


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=client_id, 
        client_secret=client_secret, 
        redirect_uri=url_for('redirect_page', _external=True),
        scope='user-library-read playlist-modify-public playlist-modify-private'
        )


app.run(debug=True)