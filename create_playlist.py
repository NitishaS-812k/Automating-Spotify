import json
import requests
from secrets import spotify_user_id, spotify_token
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import os
import youtube_dl

class CreatePlaylist:
    
    def __init__(self):
        self.user_id = spotify_user_id
        self.spotify_token = spotify_token
        self.youtube_client = self.get_youtube_client()
        self.all_songs_info = {}

    #log into youtube
    def get_youtube_client(self):
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "YOUR_CLIENT_SECRET_FILE.json"

        # Get credentials and create an API client
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)
        return youtube_client

    #get music playlist videos
    def get_music_videos(self):
        #obtained my playlistId by using playlists.lists
        request = self.youtube_client.playlistItems().list(
        part="snippet,contentDetails",
        maxResults= 8,
        playlistId="PLw1uBewiC8Rmi3BGdtmqjRXqA3B0-UsE4"
    )
        response = request.execute()
        
        #collect each video and get their info
        for item in response['items']:
            video_title = item['snippet']['title']
            youtube_url = 'https://www.youtube.com/watch?v={}'.format(item['contentDetails']['videoId'])
            
            #using youtube_dl to collect the song and artist name
            video = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download = False)
            song_name = video['track']
            artist = video['artist']

            #saving all info in dictionary
            self.all_songs_info[video_title] = {
                'youtube_url' : youtube_url,
                'song_name': song_name,
                'artist': artist,

                #add the uri
                'spotify_uri': self.get_spotify_uri(song_name, artist)
            }

    #create a new playlist
    def create_playlist(self):
        request_body = json.dumps({
            "name": "Youtube Music",
            "description": "All music on youtube",
            "public": True
        })
        query = 'https://api.spotify.com/v1/users/{}/playlists'.format(self.user_id)
        response = requests.post(
            query,
            data=request_body,
            headers={
                "Content-Type":"application/json",
                "Authorization":"Bearer {}".format(self.spotify_token)
            }
        )
        response_json = response.json()

        #playlist id
        return response_json['id']

    #search for song
    def get_spotify_uri(self, song_name, artist):
        query = 'https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20'.format(
            song_name,
            artist
        )
        response = requests.get(
            query,
            headers={
                "Content-Type":"application/json",
                "Authorization":"Bearer {}".format(self.spotify_token)
            }
        )
        response_json = response.json()
        songs = response_json['tracks']['items']

        #use first song
        uris = songs[0]['uri']

        return uris

    #add song into created spotify playlist
    def add_song_to_playlist(self):
        #populate our songs dictionary
        self.get_music_videos()

        #collect all of uri
        uri = []
        for _, info in self.all_songs_info.items():
            uri.append(info['spotify_uri'])

        #create new playlist
        playlist_id = self.create_playlist()

        #add all songs into new playlist
        request_data = json.dumps(uri)

        query = 'https://api.spotify.com/v1/playlists/{}/tracks'.format(playlist_id)
        response = requests.post(
            query,
            data=request_data,
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {}'.format(self.spotify_token)
            }
        )


        response_json = response.json()
        return response_json


if __name__ == '__main__':
    cp = CreatePlaylist()
    cp.add_song_to_playlist()