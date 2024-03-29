import requests
from bs4 import BeautifulSoup
from uritemplate import api
import youtube_dl
import threading

from constants import AUDIO_FORMAT_TYPES
from modules.json_operations_modul import JsonOperations
from modules.yt_api_modul import \
    get_yt_api_dict, get_yt_search_results, get_video_details


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

    @staticmethod
    def make_video_url_by_id(video_id):
        return "https://www.youtube.com/watch?v=" + video_id

    def download_music(self, url, name=None, cause_inst=None, save_as_last_track=False):
        """ Kompleksowo pobiera utwór i zapisuje go do bazy jako ostatnio pobrany """
        self.ytdl_download(url, name, cause_inst, save_as_last_track)

    def ytdl_download(self, url, name, cause_inst=None, save_as_last_track=False):
        """ pobiera jeden utwór o podanym url """
        ydl = self.get_download_object()
        dwn_thread = DownloadThread(
            ydl, url, name, cause_inst, save_as_last_track)
        dwn_thread.start()

    def get_download_object(self):
        """ zwraca obiekt pobierający o specyfikacji zgodnej z programem """
        path = self.get_config("save_path")
        ftype = self.get_config("file_type")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': path + '/%(title)s.%(ext)s',
            # 'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': ftype,
                'preferredquality': '256',
            }],
        } if ftype in AUDIO_FORMAT_TYPES else {
            'format': ftype,
            'outtmpl': path + '/%(title)s.%(ext)s',
            # 'quiet': True,
        }
        return ydl_opts

    def get_adress_dict_from_search(self, search_str, inst):
        """ Zwraca efekt wyszukiwania search_srt w yt jako słownik 5 pierwszych znalezionych filmików o wartościach
        nazwa: adres(krótki)"""
        ist = InternetSearchThread(self, inst, search_str)
        ist.start()

    def get_config(self, what_key):
        return self.get_all_config()[what_key]

    @staticmethod
    def get_all_config():
        config_dict = JsonOperations.load_json('../data/config.json')
        return config_dict

    @staticmethod
    def get_video_title(url, cause_inst):
        """ zdobywa tytuł video od podanego url """
        video_id = url.split("watch?v=")[1]
        result = get_video_details(video_id)

        if (result["pageInfo"]["totalResults"] < 1):
            return "Can not receive informations"

        video_details = result["items"][0]
        return video_details["snippet"]["title"]


class InternetThread(threading.Thread):
    """ wątek odciążający DownloaderOperations.get_song_dict() dostaje instancje DownloaderOperations na której wykonuje
     run, oraz instrukcje layoutu do którego ma wywołać skończenie swojej pracy, przy błędzie wywołuje funkcje od błędu
     pobierania w danej instancji """

    def __init__(self, instance, lay_inst, **kwargs):
        super(InternetThread, self).__init__(**kwargs)
        self.instance = instance
        self.lay_inst = lay_inst

    def run(self):
        self.lay_inst.internet_thread_end(get_yt_api_dict(50))


class InternetSearchThread(threading.Thread):
    """ wątek robiący pracę za DownloaderOperations.get_adress_dict_from_search(), dizałanie podobne do InternetThread"""

    def __init__(self, instance, lay_inst, search_str, **kwargs):
        super(InternetSearchThread, self).__init__(**kwargs)
        self.instance = instance
        self.lay_inst = lay_inst
        self.search_str = search_str

    def run(self):
        # zdobywa dane z api
        api_result = get_yt_search_results(self.search_str)

        if api_result is None:
            self.lay_inst.internet_thread_end(None)
            return

        # przygotowywuje listę z wymaganymi danymi w oparciu o informację zdobyte z api
        songs_data = []

        for index in range(len(api_result["items"])):
            search_result = api_result["items"][index]

            search_result_url = DownloaderOperations.make_video_url_by_id(
                search_result["id"]["videoId"])
            song_dict = {
                "title": search_result["snippet"]["title"],
                "href": search_result_url,
                "channelTitle": search_result["snippet"]["channelTitle"],
                "image": search_result["snippet"]["thumbnails"]["default"]
            }
            songs_data.append(song_dict)

        self.lay_inst.internet_thread_end(songs_data)


class DownloadThread(threading.Thread):
    """ Oddzielny wątek do pobierania muzyki, odciąża layout, wywołuje się go za pomocą start() """

    def __init__(self, ytdl_config, url, vid_name,  cause_inst, save_as_last_track=False, **kwargs):
        super(DownloadThread, self).__init__(**kwargs)
        self.ytdl_config = ytdl_config
        self.url = url
        self.cause_inst = cause_inst
        self.video_name = vid_name
        self.save_as_last_track = save_as_last_track

    def run(self):
        try:
            ytdl_object = youtube_dl.YoutubeDL(self.ytdl_config)
            print("downloading url: %s" % self.url)
            ytdl_object.download([self.url])
        except ConnectionError:
            print('DownloadThread: Error: ConnectionError')
            self.cause_inst.download_error('ConnectionError')
        except youtube_dl.utils.ExtractorError as e:
            print('DownloadThread: Error: youtube_dl.utils.ExtractorError: %s' % e)
            self.cause_inst.download_error(e)
        except AttributeError as e:
            print('DownloadThread: Error: AttributeError %s' % e)
            self.cause_inst.download_error("This webpage is age-gated")
        else:
            if self.video_name is not None and self.save_as_last_track:
                JsonOperations().save_last_track(self.video_name)
            self.cause_inst.end_thread_download()
