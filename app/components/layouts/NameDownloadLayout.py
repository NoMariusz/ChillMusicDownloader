from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.clock import Clock

from modules.downloader_modul import DownloaderOperations


class NameDownloadLayout(Screen):
    """ pobiera piosenke po nazwie, w menu ten layout ustawiny jest u góry, po wpisaniu nazwy w pole tekstowe i
    zatwierdzeniu czyści input, zabiera słownik z utworami linkami otrzymanymi po wyszukaniu podanej frazy w yt i za
    jego pomocą tworzy zawartość NameResultLayout po czym tam się przełącza """
    name_input = ObjectProperty(None)
    text_label = ObjectProperty(None)
    check_btn = ObjectProperty(None)
    name_results_float = ObjectProperty(None)
    status_text = ObjectProperty(None)

    def __init__(self, layout_manager, **kw):
        super().__init__(**kw)
        self.layout_manager = layout_manager

    def go_return(self):
        self.layout_manager.window_manager.transition.direction = 'up'
        self.layout_manager.window_manager.current = 'menu_lay'

    def download_by_name(self):
        if self.name_input.text != '':
            self.layout_manager.inst_loading_layout.show()
            Clock.schedule_once(self.download_by_name1, 0.1)

    def download_by_name1(self, _):
        self.get_results_music()

    def get_results_music(self):
        """ wywołuje wątek pobierający wyniki wyszukiwania, który po zrobieniu swojej roboty wywołuje
        internet_thread_end który zajmuje się załadowaniem wyników do drugiego okna i zmianom grafiki """
        DownloaderOperations().get_adress_dict_from_search(self.name_input.text, self)

    def internet_thread_end(self, result_dict):
        """ wywoływane po załadowaniu słownika adresów przez InternetSearchThread zajmuje się załadowaniem następnego
        okna i przygotowaniem grafiki """
        self.layout_manager.inst_name_result_layout.load_songs_to_grid(result_dict)
        self.name_input.text = ''
        self.layout_manager.inst_loading_layout.hide('name_dwn_lay')
        self.layout_manager.window_manager.transition.direction = 'left'
        self.layout_manager.window_manager.current = 'name_result_lay'
