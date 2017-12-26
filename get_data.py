import json
import spotipy
import time
import sys
import pandas as pd
from spotipy.oauth2 import SpotifyClientCredentials
from dateutil.parser import parse
import collections

def get_songs(userID, playlistID, sp):
    """ Gets ids and songs for a specific playlist

    Args:
        userID: spotify URI code for owner
        playlistID: spotify URI code for playlist
        sp = Spotify credentials object

    Returns:
        ids: spotify uri code for songs
        songs: list of song names
    """

    results = sp.user_playlist_tracks(userID, playlistID)
    songs = results['items']
    ids = []
    while results['next']:
        results = sp.next(results)
        songs.extend(results['items'])

    for i in songs:
        ids.append(i['track']['id'])

    return ids, songs

def get_audio_features(ids, songs, sp):
    """ Gets the audio features for a set of songs

    Args:
        ids: spotify uri code for songs
        songs: list of song names
        sp = Spotify credentials object

    Returns:
        df: pandas data frame of audio features for the list of songs
    """

    index = 0
    length_feature = []
    popularity_feature = []
    explicit_feature = []
    audio_features = []

    for i in songs:
        length_feature.append(i['track']['duration_ms'])
        popularity_feature.append(i['track']['popularity'])
        explicit_feature.append(i['track']['explicit'])

    while index < len(ids):
        audio_features += sp.audio_features(ids[index:index + 50])
        index += 50

    features_list = []
    for features in audio_features:
        features_list.append([features['energy'], features['liveness'],
            features['tempo'], features['speechiness'],
            features['acousticness'], features['instrumentalness'],
            features['time_signature'], features['danceability'],
            features['key'], features['duration_ms'],
            features['loudness'], features['valence'],
            features['mode']])

    df = pd.DataFrame(features_list, columns=['energy', 'liveness',
                                                  'tempo', 'speechiness',
                                                  'acousticness', 'instrumentalness',
                                                  'time_signature', 'danceability',
                                                  'key', 'duration_ms', 'loudness',
                                                  'valence', 'mode'])

    df = df.assign(length = length_feature)
    df = df.assign(popularity = popularity_feature)
    df = df.assign(explicit = explicit_feature)

    return df


def preprocess_data(like, dislike):
    """ Adds labels and combines the selected like and disliked songs
        into one consolidated dataset.

    Args:
        like: dataframe of audio features for liked songs
        dislike: dataframe of audio features for disliked songs

    Returns:
        complete_data: pandas data frame of the full dataset combining 
                        liked and disliked songs with labels
    """

    like.loc[like['explicit'] == True, 'explicit'] = 1
    like.loc[like['explicit'] == False, 'explicit'] = 0
    dislike.loc[dislike['explicit'] == True, 'explicit'] = 1
    dislike.loc[dislike['explicit'] == False, 'explicit'] = 0

    like['target'] = 1
    dislike['target'] = 0

    complete_data = pd.concat([like,dislike], ignore_index = True)

    return complete_data


def get_playlist_ID(userID, sp):
    """ Gets the playlist ID's for liked and disliked songs based on user input

    Args:
        userID: spotify URI code for owner
        sp = Spotify credentials object

    Returns:
        like: list of selected songs that user LIKES
        dislike: list of selected songs that user DISLKES
        playlist_map[int(num)]: selected song to make predictions on
    """

    playlists = sp.user_playlists(userID)
    playlist_map = collections.defaultdict(str)
    print('All of your playlists: \n')
    while playlists:
        for i, playlist in enumerate(playlists['items']):
            print("%3d %s" % (i + 1 + playlists['offset'], playlist['name']))
            owner_id = playlist['owner']['uri'].split(":")[2]
            playlist_map[i + 1 + playlists['offset']] = [playlist['id'], owner_id]
        if playlists['next']:
            playlists = sp.next(playlists)
        else:
            playlists = None

    num = ""
    like = ""
    dislike = ""
    
    while num == "":
        num = input('Choose a desired playlist to analyze by entering the corresponding number: ')
    while like == "":
        like = input('Choose playlists that you LIKE (enter each playlist number space separated): ')
        like = like.split(" ")
    while dislike == "":
        dislike = input('Choose playlists that you DISLIKE (enter each playlist number space separated): ')
        dislike = dislike.split(" ")

    for i in range(len(like)):
        like[i] = playlist_map[int(like[i])]

    for i in range(len(dislike)):
        dislike[i] = playlist_map[int(dislike[i])]

    return like, dislike, playlist_map[int(num)]

