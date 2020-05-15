import requests
from bs4 import BeautifulSoup
import youtube_dl
import json
import threading


class DownloaderOperations(object):
    def __init__(self):
        self.inst_jo = JsonOperations()

    def get_song_dict(self, inst):
        """ zwraca słownik z parami tytuł url, a w miejscu zmiany z nowych na stare utwory wstawia pustą wartość none"""
        it = InternetThread(self, inst)
        it.start()

    @staticmethod
    def urll(href):  # tworzy url
        u = "https://www.youtube.com" + href
        return u

    def download_music(self, name, url, cause_inst=None):
        """ Kompleksowo pobiera utwór i zapisuje go do bazy jako ostatnio pobrany """
        _ = self.ytdl_download(url, cause_inst)
        JsonOperations.save_last_track(self.inst_jo, name)

    def ytdl_download(self, url, cause_inst=None):
        """ pobiera jeden utwór o podanym url """
        ydl = self.get_download_object()
        dwn_thread = DownloadThread(ydl, url, cause_inst)
        dwn_thread.start()

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
        return ydl_opts

    def get_adress_dict_from_search(self, search_str, inst):
        """ Zwraca efekt wyszukiwania search_srt w yt jako słownik 5 pierwszych znalezionych filmików o wartościach
        nazwa: adres(krótki)"""
        search_str_form = self.query_parse(search_str)
        ist = InternetSearchThread(self, inst, search_str_form)
        ist.start()

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

    @staticmethod
    def get_video_title(url, cause_inst):
        """ zdobywa tytuł video z podanego url, przy błędzie url, lub połączenia swraca error do instancji wywołującej """
        try:
            page = requests.get(url)
        except requests.exceptions.ConnectionError:
            cause_inst.download_error()
            return 'Error'
        except requests.exceptions.MissingSchema:
            cause_inst.download_error()
            return 'Error'
        pagebs = BeautifulSoup(page.content, "html.parser")
        elem = pagebs.find("span", class_='watch-title')
        return elem.get_text().strip()


class InternetThread(threading.Thread):
    """ wątek odciążający DownloaderOperations.get_song_dict() dostaje instancje DownloaderOperations na której wykonuje
     run, oraz instrukcje layoutu do którego ma wywołać skończenie swojej pracy, przy błędzie wywołuje funkcje od błędu
     pobierania w danej instancji """
    def __init__(self, instance, lay_inst, **kwargs):
        super(InternetThread, self).__init__(**kwargs)
        self.instance = instance
        self.lay_inst = lay_inst

    def run(self):
        channel = self.instance.get_config("channel")
        try:
            page = requests.get(channel + "/videos?view=0&sort=dd&flow=grid")
        except requests.exceptions.ConnectionError:
            print("\t116 requests.exceptions.ConnectionError")
            self.lay_inst.internet_thread_end({"Error: Can't connect to internet": 'Error'})
        except requests.exceptions.MissingSchema:
            print("\t118 requests.exceptions.MissingSchema")
            self.lay_inst.internet_thread_end({"Error: Invalid YouTube channel address": 'Error'})
        else:
            pagebs = BeautifulSoup(page.content, "html.parser")
            url_dict = {}

            last_track = JsonOperations.get_last_track(self.instance.inst_jo)

            for tag in pagebs.find_all("a",
                                       class_="yt-uix-sessionlink yt-uix-tile-link spf-link yt-ui-ellipsis yt-ui-ellipsis-2"):
                if tag.get_text() == last_track:
                    url_dict["↑ New, ↓ Old"] = None
                # print("\tTag in bs4 parsing:", tag.get_text())
                url_dict[tag.get_text()] = self.instance.urll(tag.get("href"))

            if url_dict == {}:
                print("\t135 url_dict == {}")
                url_dict = {"Error: Can't connect to this yt channel": 'Error'}

            self.lay_inst.internet_thread_end(url_dict)


class InternetSearchThread(threading.Thread):
    """ wątek robiący pracę za DownloaderOperations.get_adress_dict_from_search(), dizałanie podobne do InternetThread"""
    def __init__(self, instance, lay_inst, search_str, **kwargs):
        super(InternetSearchThread, self).__init__(**kwargs)
        self.instance = instance
        self.lay_inst = lay_inst
        self.search_str = search_str

    def run(self):
        try:
            page = requests.get('https://www.youtube.com/results?search_query=%s' % self.search_str)
        except requests.exceptions.ConnectionError:
            self.lay_inst.internet_thread_end({"Error: Can't connect": 'Error', "Error 1": 'Error',
                                               "Error 2": 'Error', "Error 3": 'Error',
                                               "Error 4": 'Error'})
        else:
            pagebs = BeautifulSoup(page.content, "html.parser")
            url_dict = {}

            counter = 0
            for tag in pagebs.find_all("a",
                                       class_='yt-uix-tile-link yt-ui-ellipsis yt-ui-ellipsis-2 yt-uix-sessionlink spf-link'):
                if counter >= 5:
                    break
                url_dict[tag.get_text()] = self.instance.urll(tag.get("href"))
                counter += 1

            if url_dict == {}:
                url_dict = {"Error: Can't connect": 'Error', "Error 1": 'Error',
                            "Error 2": 'Error', "Error 3": 'Error',
                            "Error 4": 'Error'}

            self.lay_inst.internet_thread_end(url_dict)


class DownloadThread(threading.Thread):
    """ Oddzielny wątek do pobierania muzyki, odciąża layout, wywołuje się go za pomocą start() """
    def __init__(self, ytdl_config, url, cause_inst, **kwargs):
        super(DownloadThread, self).__init__(**kwargs)
        self.ytdl_config = ytdl_config
        self.url = url
        self.cause_inst = cause_inst

    def run(self):
        try:
            ytdl_object = youtube_dl.YoutubeDL(self.ytdl_config)
            # print("downloading url: %s" % self.url, "\nwith config: ", self.ytdl_config)
            ytdl_object.download([self.url])
        except ConnectionError:
            print('DownloadThread: Error: ConnectionError')
            self.cause_inst.download_error()
        except youtube_dl.utils.ExtractorError:
            print('DownloadThread: Error: youtube_dl.utils.ExtractorError')
            self.cause_inst.download_error()
        except AttributeError:
            print('DownloadThread: Error: AttributeError')
            self.cause_inst.download_error()
        else:
            self.cause_inst.end_thread_download()


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
