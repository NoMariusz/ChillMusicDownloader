import googleapiclient.discovery
import datetime
import os
import html

import threading
import httplib2

from json_operations_modul import JsonOperations


class YtApiLoader(object):
    """ obiekt do którego się odwołuje aby zyskać słownik wyników uzyskanych z ładowania kanału z ytapi """
    def __init__(self, lay_inst, **kwargs):
        """ przy tworzeniu obiektu trzeba pddać instancję aby mówgł się do niej odwołać po skończeniu pracy wątku """
        super(YtApiLoader, self).__init__(**kwargs)
        self.lay_inst = lay_inst

    def get_yt_api_dict(self):
        """ tworzy wątek """
        inst_load_th = LoadThread(self)
        inst_load_th.start()

    def end_loading_thread(self, yta_dict):
        """ wywoływany po zdobyciu słownika utworów """
        self.lay_inst.end_yt_api_loader(yta_dict)


class LoadThread(threading.Thread):
    """ wątek ładowania utworów z yt_api, nie robi tego sam a odwołuje się do zewnętrznych funkcji, sprawdza również
    połączenie podcas pracy i wychwytuje błędy po pracy odwołuje się do odpowiedniej funcki w instancji wywołującej """
    def __init__(self, instance, **kwargs):
        super(LoadThread, self).__init__(**kwargs)
        self.instance = instance

    def run(self):
        """ zdobywa słownik yt_api, przechwytuje błędy połączenia """
        try:
            yta_dict = get_yt_api_dict()
        except ConnectionError:
            # print('Error 40 lth: ConnectionError')
            self.instance.end_loading_thread({})
        except httplib2.ServerNotFoundError:
            # print("Error 43 lth: httplib2.ServerNotFoundError")
            self.instance.end_loading_thread({})
        else:
            self.instance.end_loading_thread(yta_dict)


def get_yt_api_dict(tracks_limit=-1):
    """ zdobywa słownik z yt_api w zależności od id_kanału który jest zdobywany z nazwy zdobywanej z url kanału w
    konfiguracji, zapętlony w kółko zdobywa po 50 utworów sortowanych od najnowszych z czasem publikacji starszym niż
    ostatni załadowany element (dzięki czemu te 50 utworów są ładowane coraz starsze), jeśli element nie jest utworem
    nie dodaje go do słownika, jeśli poprzedni zdobyty rekord z egzekucji nie jest nowszy od aktualnego, (co powinno
    zostać spełnione) to znaczy że elementy się skonczyły więc zwraca słownik, jeśli dzienny token zapytań yt_api wygasł
     to zwraca odpowiedni słownik, w przypadku nie znalezienia id do nazwy zwraca słownik błędu,
     błędy: 0 - błąd nazwy kanału, -1 - błąd limitu tokena """

    def make_early_time(str_time):
        """ przekształaca aktualny string z datą na obiekt czasu dodaje do niego sekunde i przeształca ponownie na
        stringa daty w odpowiednim formacie """
        time = datetime.datetime.strptime(str_time, "%Y-%m-%dT%H:%M:%SZ")
        time = time - datetime.timedelta(seconds=1)
        return time.isoformat() + ".000Z"

    def get_channel_id():
        """ zdobywa id kanału z zewnętrznej funkcji tłumaczącej nazwe_kanału na id, nazwe zdobywa z funcji
        get_channel_name(), jeśli nazwa będzie błędna zwróci 0 zwracające błąd, jeśli zapisane jest w formacie channel
         to za pomocą check_is_config_id to zwraca od razu id"""
        x = check_is_config_id()
        # print("\t70 yt-api-modul: channel_id ", x)
        if x:       # sprawdza czy w konfiguracji jest url z id czy nazwą, jeśli z id to zwraca to id
            return x

        channel_name = get_channel_name()
        # print("\t74 yt-api-modul: channel_name ", channel_name)
        if channel_name == 0:
            return 0
        x = yta_get_channel_id_by_name(channel_name)
        # print("\t78 yt-api-modul: channel_id ", x)
        return x

    def make_video_url_by_id(video_id):
        return "https://www.youtube.com/watch?v=" + video_id

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = 'AIzaSyCBOTqSrSTFkspuoksjclT6U8LZPbT8pow' # dev key

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=DEVELOPER_KEY)

    pub_time = None
    iterate = 0

    dwn_dict = {}
    old_last_time = False

    channel_id = get_channel_id()
    # print("\t99 yt_api_modul channel id:", channel_id)

    if channel_id == 0:
        return {'Invalid channel name': None}
    elif channel_id == -1:
        return {'Your daily limit expires': None}

    old_last_time = datetime.datetime.now()

    last_track_name = JsonOperations().get_last_track()

    while True:
        request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            order="date",
            maxResults=50,
            publishedBefore=pub_time,
            type="video"
        )

        try:
            response = request.execute()
            print("\t\tresponse maked")
        except googleapiclient.errors.HttpError:
            dwn_dict['Your daily limit expires'] = None
            # print('Error yt_api_modul 122: daily limit expires, googleapiclient.errors.HttpError')
            break

        if not response['items']:
            # print('\t126 main No more items')
            break

        for xx in response['items']:
            last_time = datetime.datetime.strptime(xx['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%SZ")
            if old_last_time:
                if int((old_last_time - last_time).seconds) < -1:
                    # print('int((old_last_time - last_time).seconds) < -1')
                    return dwn_dict
            old_last_time = last_time

            if 'videoId' in xx['id'].keys() and 'title' in xx['snippet'].keys():
                # print(str(iterate) + " " + xx['id']['videoId'] + " --- " + xx['snippet']['title'])
                video_name = html.unescape(xx['snippet']['title'])
                if video_name == last_track_name:
                    dwn_dict["↑ New, ↓ Old"] = None
                dwn_dict[video_name] = make_video_url_by_id(xx['id']['videoId'])
                iterate += 1
            """else:
                print(xx)"""
        pub_time = xx['snippet']['publishedAt']
        pub_time = make_early_time(pub_time)

        if (tracks_limit != -1) and (len(dwn_dict) >= tracks_limit):
            return dwn_dict

    # print("\t146 yt_api_modul dict gived by yt-api: ", dwn_dict)
    return dwn_dict


def get_channel_name():
    """ zdobywa nazwę kanału z pliku konfiguracyjnego, w przypadku błędu zwraca 0 czyli błąd """
    x = JsonOperations()
    full_name = x.get_config("channel")
    namelist = full_name.split('/')
    # print(namelist)
    x = namelist.index('user')
    if x == -1:
        return 0
    return namelist[x+1]


def yta_get_channel_id_by_name(name):
    """ za pomocą yt_api zdobywa id kanału po jego nazwie, jeśli nie znalazło kanału to zwraca 0 czyli błąd """
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = "AIzaSyCBOTqSrSTFkspuoksjclT6U8LZPbT8pow"

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=DEVELOPER_KEY)

    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        forUsername=name
    )
    try:        # aby sprawdzić czy token jest aktualny
        response = request.execute()
    except googleapiclient.errors.HttpError:
        return -1
    # print("search id response: ", response)

    if 'items' not in response:
        return 0
    if 'id' not in response['items'][0]:
        return 0
    return response['items'][0]['id']


def check_is_config_id():
    """ sprawdza czy ścieżka jest zapisana w formacie z channel id , jeśli tak zwraca id jeśli nie to false """
    y = JsonOperations()
    conf = y.get_config("channel")
    if "channel" == conf.split("/")[3]:
        return conf.split("/")[4]
    return False
