import requests
from bs4 import BeautifulSoup
import youtube_dl
import json
import threading


class DownloaderOperations(object):
    def __init__(self):
        self.inst_jo = JsonOperations()

    def get_song_dict(self):
        """ zwraca słownik z parami tytuł url, a w miejscu zmiany z nowych na stare utwory wstawia pustą wartość none"""
        channel = self.get_config("channel")
        try:
            page = requests.get(channel + "/videos?view=0&sort=dd&flow=grid")
        except requests.exceptions.ConnectionError:
            return {"Error: Can't connect to internet": 'Error'}
        except requests.exceptions.MissingSchema:
            return {"Error: Invalid YouTube channel address": 'Error'}

        pagebs = BeautifulSoup(page.content, "html.parser")
        url_dict = {}

        last_track = JsonOperations.get_last_track(self.inst_jo)

        for tag in pagebs.find_all("a", class_="yt-uix-sessionlink yt-uix-tile-link spf-link yt-ui-ellipsis yt-ui-ellipsis-2"):
            if tag.get_text() == last_track:
                url_dict["↑ New, ↓ Old"] = None
            print(tag.get_text())           # do usuniecia <-<-<---------------------------------------
            url_dict[tag.get_text()] = self.urll(tag.get("href"))

        if url_dict == {}:
            url_dict = {"Error: Can't connect to this yt channel": 'Error'}

        return url_dict

    @staticmethod
    def urll(href):  # tworzy url
        u = "https://www.youtube.com" + href
        return u

    def download_music(self, name, url):
        """ Kompleksowo pobiera utwór i zapisuje go do bazy jako ostatnio pobrany """
        status = self.ytdl_download(url)
        JsonOperations.save_last_track(self.inst_jo, name)

    def ytdl_download(self, url):
        """ pobiera jeden utwór o podanym url """
        ydl = self.get_download_object()
        try:
            dwn_thread = DownloadThread(ydl, url)
            dwn_thread.start()
            dwn_thread.join()
            return "Status: Downloaded"
        except AttributeError:
            return "Status: Error"

    def get_download_object(self):
        """ zwraca obiekt pobierający o specyfikacji zgodnej z programem """
        path = self.get_config("save_path")
        ftype = self.get_config("file_type")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': path + '/%(title)s.%(ext)s',
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': ftype,
                'preferredquality': '192',
            }],
        }
        ydl = youtube_dl.YoutubeDL(ydl_opts)
        return ydl

    def get_adress_dict_from_search(self, search_str):
        """ Zwraca efekt wyszukiwania search_srt w yt jako słownik 5 pierwszych znalezionych filmików o wartościach
        nazwa: adres(krótki)"""
        search_str_form = self.query_parse(search_str)
        try:
            page = requests.get('https://www.youtube.com/results?search_query=%s' % search_str_form)
        except requests.exceptions.ConnectionError:
            return {"Error: Can't connect to this yt channel": 'Error'}
        pagebs = BeautifulSoup(page.content, "html.parser")
        url_dict = {}

        counter = 0
        for tag in pagebs.find_all("a", class_='yt-uix-tile-link yt-ui-ellipsis yt-ui-ellipsis-2 yt-uix-sessionlink spf-link'):
            if counter >= 5:
                break
            url_dict[tag.get_text()] = self.urll(tag.get("href"))
            counter += 1

        if url_dict == {}:
            url_dict = {"Error: Can't connect to this yt channel": 'Error'}
        return url_dict

    @staticmethod
    def query_parse(parse_string):
        """ zamienia stringa na taki format jaki stosuje wyszukiwanie youtuba, aby zyskać zgodność otrzymanych wyników
        wyszukiwania """
        replace_dict = {
            '#': '%23',
            '$': '%24',
            '@': '%40',
            '%': '%25',
            '&': '%26',
            '+': '%2B',
            '=': '%3D',
            ',': '%2C',
            ';': '%3B',
            ':': '%3A',
            ' ': '+',
        }
        for x, y in replace_dict.items():
            parse_string = parse_string.replace(x, y)
        return parse_string

    def get_config(self, what_key):
        return self.get_all_config()[what_key]

    @staticmethod
    def get_all_config():
        config_dict = JsonOperations.load_json('config.json')
        return config_dict


class DownloadThread(threading.Thread):

    def __init__(self, ytdl_object, url, **kwargs):
        super(DownloadThread, self).__init__(**kwargs)
        self.ytdl_object = ytdl_object
        self.url = url

    def run(self):
        self.ytdl_object.download([self.url])


class JsonOperations(object):
    @staticmethod
    def load_json(file_name):
        """ wczytuje słownik """
        scores_file = open(file_name, "r")
        json_scores = scores_file.read()
        dict_last_track = json.loads(json_scores)
        scores_file.close()
        return dict_last_track

    @staticmethod
    def save_json(dict_last_track, file_name):
        """ zapisuje słownik """
        json_scores = json.dumps(dict_last_track)
        scores_file = open(file_name, "w")
        scores_file.write(json_scores)
        scores_file.close()

    def get_last_track(self):
        """ wczytuje ostatnią ścieżkę """
        channel = self.get_config("channel")
        dict_last_track = self.load_json("last_track.json")
        return dict_last_track[channel].strip()

    def save_last_track(self, last_track):
        """ zapisuje ostanią ścieżkę, lasttrack to json """
        dict_last_track = self.load_json('last_track.json')
        channel = self.get_config('channel')
        dict_last_track[channel] = last_track
        self.save_json(dict_last_track, "last_track.json")

    def get_config(self, what):
        conf_dict = self.load_json('config.json')
        return conf_dict[what].strip()
