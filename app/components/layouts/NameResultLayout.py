from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.clock import Clock

from modules.downloader_modul import DownloaderOperations


class NameResultLayout(Screen):
    """ Zawiera grid layout który po wypełnieniu przez NameDownloadLayout zawiera nazwy znalezionych utworów przez
    tamten obiekt wywoływane jest tylko przez tamten obiekt więc zawsze posiada liste z nazwami linkami do pobrania
     o góry zawiera odpowiednio zmieniającą się tabele status, po kliknięciu w guzik pobierz, guzik przsyła jako
     instancje swój numer, przez który wiemy co pobrać z lisy, po pobraniu wraca do NameDownloadLayout """
    songs_labels = ObjectProperty(None)
    status_label = ObjectProperty(None)

    return_btn = ObjectProperty(None)
    download_buttons = ObjectProperty(None)

    song_images = ObjectProperty(None)
    channel_titles = ObjectProperty(None)

    dwn_lock = False

    def __init__(self, layout_manager, **kw):
        super().__init__(**kw)
        self.layout_manager = layout_manager

    def go_return(self):
        """ wraca do menu """
        if not self.dwn_lock:
            self.layout_manager.window_manager.transition.direction = 'right'
            self.layout_manager.window_manager.current = 'name_dwn_lay'

    def load_songs_to_grid(self, songs_data):
        """ służy do załadowania nazw utworów do listy pobierania """
        self.edit_dwn_lock(False)
        self.songs_data = songs_data

        if self.songs_data is None:
            self.load_songs_as_error()
            return

        # load data to ui
        for index in range(5):
            self.songs_labels[index].text = self.format_title(songs_data[index]["title"])
            self.channel_titles[index].text = songs_data[index]["channelTitle"]
            self.song_images[index].source = songs_data[index]["image"]["url"]

    def format_title(self, text):
        return text[0:25] + "..." if len(text) > 28 else text
    
    def load_songs_as_error(self):
        for label in self.songs_labels:
            label.text = "Error with connection"

    def download_music(self, btn_index):
        """ pobiera kawałek o takim numerze w słowniku jak instance czyli numer guzika """
        if (self.songs_data != None) and (not self.dwn_lock):
            self.edit_dwn_lock(True)
            self.download_address = self.songs_data[btn_index]["href"]
            if self.download_address:
                self.status_label.text = 'Status: Downloading %s' % (self.songs_data[btn_index]["title"])
                self.download_music1()

    def download_music1(self):
        Clock.schedule_once(self.download_address1, 0)

    def download_address1(self, _):
        """ pobiera dany adres w przypadku błędu zwraca błąd połączenia """
        DownloaderOperations().download_music(self.download_address, cause_inst=self)

    def end_thread_download(self):
        """ wywoływane z wątku pobierania po skończeniu pracy """
        Clock.schedule_once(self.download_address2, 1)

    def download_error(self):
        """ wywoływane z wątku pobierania w przypadku błędu """
        Clock.schedule_once(self.download_address3, 1.5)
        self.status_label.text = "Status: Error"

    def download_address2(self, _):
        Clock.schedule_once(self.download_address3, 1.5)
        self.status_label.text = "Status: Downloaded"

    def download_address3(self, _):
        self.layout_manager.window_manager.transition.direction = 'right'
        self.layout_manager.window_manager.current = 'name_dwn_lay'
        self.status_label.text = 'Select Video:'

    def edit_dwn_lock(self, lock):
        if lock:
            self.dwn_lock = True
            self.return_btn.background_color = [0.6640625, 0.59765625, 0.6171875, 1]
            for btn in self.download_buttons:
                btn.background_color = [0.6640625, 0.59765625, 0.6171875, 1]
        else:
            self.dwn_lock = False
            self.return_btn.background_color = [0.81640625, 0.3125, 0.43359375, 1]
            for btn in self.download_buttons:
                btn.background_color = [0.81640625, 0.3125, 0.43359375, 1]
