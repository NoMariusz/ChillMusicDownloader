import requests
from bs4 import BeautifulSoup
import youtube_dl
import threading

from modules.json_operations_modul import JsonOperations
from modules.yt_api_modul import get_yt_api_dict


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

    def download_music(self, url, name=None, cause_inst=None):
        """ Kompleksowo pobiera utwór i zapisuje go do bazy jako ostatnio pobrany """
        self.ytdl_download(url, name, cause_inst)

    def ytdl_download(self, url, name, cause_inst=None):
        """ pobiera jeden utwór o podanym url """
        ydl = self.get_download_object()
        dwn_thread = DownloadThread(ydl, url, name, cause_inst)
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
        config_dict = JsonOperations.load_json('../data/config.json')
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
        elem = pagebs.find("meta", {"name": "title"})
        return elem.get_attribute_list("content")[0].strip()


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
        # zdobywa stronę
        try:
            page = requests.get('https://www.youtube.com/results?search_query=%s' % self.search_str)
        except requests.exceptions.ConnectionError:
            self.lay_inst.internet_thread_end({"Error: Can't connect": 'Error', "Error 1": 'Error',
                                               "Error 2": 'Error', "Error 3": 'Error',
                                               "Error 4": 'Error'})
        else:
            pagebs = BeautifulSoup(page.content, "html.parser")
            url_dict = {}

            # znajduję odpowiedni element script zawierający informację o wyszukanych video
            scripts_list = []
            for script in pagebs.find_all("script"):
                scripts_list.append(str(script))

            found_initial_data_script = list(filter(lambda x: -1 < x.find("ytInitialData") < 70, scripts_list))[0]

            # formatuje ten tag script do słownika
            formatted_script = found_initial_data_script[59:]
            formatted_script = formatted_script[:-10]

            info_dict = JsonOperations.get_dict_from_json_str(formatted_script)

            video_data_dict = info_dict["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"].get(
                "sectionListRenderer")["contents"][0]["itemSectionRenderer"]["contents"]

            # wypełna 5 pól słownika url_dict w oparciu o informację z tego słownika
            counter = 0
            for video_info in video_data_dict:
                if 'videoRenderer' in video_info.keys():
                    url_dict[video_info["videoRenderer"]["title"]["runs"][0]["text"]] = \
                        DownloaderOperations.make_video_url_by_id(video_info['videoRenderer']['videoId'])
                    counter += 1
                    if counter >= 5:
                        break

            self.lay_inst.internet_thread_end(url_dict)


class DownloadThread(threading.Thread):
    """ Oddzielny wątek do pobierania muzyki, odciąża layout, wywołuje się go za pomocą start() """
    def __init__(self, ytdl_config, url, vid_name,  cause_inst, **kwargs):
        super(DownloadThread, self).__init__(**kwargs)
        self.ytdl_config = ytdl_config
        self.url = url
        self.cause_inst = cause_inst
        self.video_name = vid_name

    def run(self):
        try:
            ytdl_object = youtube_dl.YoutubeDL(self.ytdl_config)
            print("downloading url: %s" % self.url)
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
            if self.video_name is not None:
                JsonOperations().save_last_track(self.video_name)
            self.cause_inst.end_thread_download()
