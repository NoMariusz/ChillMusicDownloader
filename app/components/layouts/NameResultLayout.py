from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.clock import Clock

from app.modules.downloader_modul import DownloaderOperations


class NameResultLayout(Screen):
    """ Zawiera grid layout który po wypełnieniu przez NameDownloadLayout zawiera nazwy znalezionych utworów przez
    tamten obiekt wywoływane jest tylko przez tamten obiekt więc zawsze posiada liste z nazwami linkami do pobrania
     o góry zawiera odpowiednio zmieniającą się tabele status, po kliknięciu w guzik pobierz, guzik przsyła jako
     instancje swój numer, przez który wiemy co pobrać z lisy, po pobraniu wraca do NameDownloadLayout """
    song1_name = ObjectProperty(None)
    song2_name = ObjectProperty(None)
    song3_name = ObjectProperty(None)
    song4_name = ObjectProperty(None)
    song5_name = ObjectProperty(None)
    status_label = ObjectProperty(None)

    return_btn = ObjectProperty(None)
    download_button1 = ObjectProperty(None)
    download_button2 = ObjectProperty(None)
    download_button3 = ObjectProperty(None)
    download_button4 = ObjectProperty(None)
    download_button5 = ObjectProperty(None)
    dwn_lock = False

    def __init__(self, layout_manager, **kw):
        super().__init__(**kw)
        self.layout_manager = layout_manager

    def go_return(self):
        """ wraca do menu """
        if not self.dwn_lock:
            self.layout_manager.window_manager.transition.direction = 'right'
            self.layout_manager.window_manager.current = 'name_dwn_lay'

    def load_songs_to_grid(self, result_dict):
        """ służy do załadowania nazw utworów do listy pobierania, z result_dict """
        self.edit_dwn_lock(False)
        self.result_dict = result_dict
        label_list = [self.song1_name, self.song2_name, self.song3_name, self.song4_name, self.song5_name]
        for x, y in enumerate(result_dict.keys()):
            label_list[x].text = y

    def download_music(self, instance):
        """ pobiera kawałek o takim numerze w słowniku jak instance czyli numer guzika """
        if (self.result_dict != {"Error: Can't connect": 'Error', "Error 1": 'Error',
                                 "Error 2": 'Error', "Error 3": 'Error',
                                 "Error 4": 'Error'}) and (not self.dwn_lock):
            self.edit_dwn_lock(True)
            self.download_address = self.get_download_address(instance)
            if self.download_address != "":
                self.status_label.text = 'Status: Downloading %s' % (self.get_download_name(instance))
                self.download_music1()

    def get_download_address(self, btn_instance):
        try:
            return list(self.result_dict.values())[btn_instance]
        except IndexError:
            print("NameDownloadLayout: get_download_address - IndexError, self.result_dict: %s , btn_instance: %s" % (self.result_dict, btn_instance))
            return ""

    def get_download_name(self, btn_instance):
        return list(self.result_dict.keys())[btn_instance]

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
            self.download_button1.background_color = [0.6640625, 0.59765625, 0.6171875, 1]
            self.download_button2.background_color = [0.6640625, 0.59765625, 0.6171875, 1]
            self.download_button3.background_color = [0.6640625, 0.59765625, 0.6171875, 1]
            self.download_button4.background_color = [0.6640625, 0.59765625, 0.6171875, 1]
            self.download_button5.background_color = [0.6640625, 0.59765625, 0.6171875, 1]
        else:
            self.dwn_lock = False
            self.return_btn.background_color = [0.81640625, 0.3125, 0.43359375, 1]
            self.download_button1.background_color = [0.81640625, 0.3125, 0.43359375, 1]
            self.download_button2.background_color = [0.81640625, 0.3125, 0.43359375, 1]
            self.download_button3.background_color = [0.81640625, 0.3125, 0.43359375, 1]
            self.download_button4.background_color = [0.81640625, 0.3125, 0.43359375, 1]
            self.download_button5.background_color = [0.81640625, 0.3125, 0.43359375, 1]
