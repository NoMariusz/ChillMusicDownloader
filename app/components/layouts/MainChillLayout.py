from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window

from kivy.uix.label import Label
from kivy.uix.button import Button

from modules.downloader_modul import DownloaderOperations
from modules.json_operations_modul import JsonOperations
from modules.yt_api_modul import YtApiLoader

from components.utils.SongsGrid import SongsGrid
from components.utils.PopupChange import PopupChange


class MainChillLayout(Screen):
    """ główne okno aplikacji skład sie głownie z bocznych guzików, okna z listą i dolnego paska postępu """
    scroll_float = ObjectProperty(None)
    txt_list = ObjectProperty(None)

    load_btn = ObjectProperty(None)
    new_download_btn = ObjectProperty(None)
    select_songs_btn = ObjectProperty(None)
    change_song_btn = ObjectProperty(None)
    return_btn = ObjectProperty(None)
    yt_api_btn = ObjectProperty(None)
    select_all_btn = ObjectProperty(None)

    download_progress_float = ObjectProperty(None)
    progress_text = ObjectProperty(None)
    progress_base = ObjectProperty(None)
    progress_current = ObjectProperty(None)
    progress_maked = ObjectProperty(None)

    def __init__(self, layout_manager, **kwargs):
        super(MainChillLayout, self).__init__(**kwargs)
        self.layout_manager = layout_manager
        self.is_song_loaded = False     # wzkaźnik sprawdzający czy są załadowane utwory, gdyż trzeba je mieć aby pobrać
        self.songs_dict = None      # lista z utworami
        self.last_track = 'To check load songs'     # wyświetlanie ostatniej ścieżki do change

        self.inst_jo = JsonOperations()   # wspólna instancja json operations
        self.inst_do = DownloaderOperations()   # wspólna instancja json operations

        """ objekt ScrollViev odpowiadający za scrolowanie Songs grid, jest dzieckiem głownego layoutu """
        self.inst_scroll_viev = ScrollView(size_hint=(1, 1), size=(Window.width, Window.height), pos_hint={'x': 0, 'y': 0})
        self.inst_songs_grid = SongsGrid(self)
        self.inst_songs_grid.bind(minimum_height=self.inst_songs_grid.setter('height'))
        self.inst_scroll_viev.add_widget(self.inst_songs_grid)

    def load_songs(self, instance):
        if instance.background_color == [0.81640625, 0.3125, 0.43359375, 1]:
            self.layout_manager.inst_loading_layout.show()
            Clock.schedule_once(self.load_songs1, 0.01)

    def load_songs1(self, _):
        """ Tworzy scrolowalną liste piosenek odblokowywuje inne opcje, jeśli opcje były już kiedyś ładowane czyści
        liste"""
        if self.is_song_loaded:
            self.clear_scroll()

        self.old_songs_dict = self.songs_dict
        DownloaderOperations.get_song_dict(self.inst_do, self)     # pobiera słownik utworów

    def internet_thread_end(self, song_dict):
        self.songs_dict = song_dict
        if self.old_songs_dict is not None:     # jeśli długość listy utworów została zmieniona to rozciąga najpierw box layout do wklejania utworów, aby poprawnie weszły
            self.stretch_lay(self.songs_dict)
        else:
            self.load_songs2()

    def load_songs2(self):
        self.scroll_float.add_widget(self.inst_scroll_viev)

        self.inst_songs_grid.load_dict_to_grid(self.songs_dict)  # tworzy liste piosenek

        self.txt_list.text = 'List of Songs:'

        self.is_song_loaded = True

        if list(self.songs_dict.keys())[0] == '↑ New, ↓ Old':  # jeśli nie ma nowych utworów to nie można nic pobierać
            self.un_or_block_btn(list_btn_to_block=[self.select_songs_btn], block=False)
        elif list(self.songs_dict.values())[0] == 'Error':
            self.un_or_block_btn(list_btn_to_block=[self.new_download_btn, self.select_songs_btn], block=True)
        else:
            self.un_or_block_btn(list_btn_to_block=[self.new_download_btn, self.select_songs_btn], block=False)

        self.get_last_track()
        self.layout_manager.inst_loading_layout.hide('main_lay')

    def download_all_new(self, instance):
        """ pobiera wszystkie nowe utwory jeśli został klikniety guzik, tworzy słownik utworów do pobrania """
        if instance.background_color == [0.81640625, 0.3125, 0.43359375, 1]:
            dwn_dict = self.make_url_download_dict()
            self.download_music(dwn_dict)

    def start_selection_songs(self, instance):
        """ odpowiada za umożliwienie  wybierania utworów do pobrania """
        if instance.background_color == [0.81640625, 0.3125, 0.43359375, 1]:
            self.inst_songs_grid.clear_widgets()
            self.inst_songs_grid.extended_dict_to_grid(songs_dict=self.songs_dict)
            self.un_or_block_btn(
                list_btn_to_block=[self.new_download_btn, self.select_songs_btn, self.load_btn, self.change_song_btn,
                                   self.yt_api_btn],
                block=True)
            self.make_chose_btn()
            self.show_select_all_btn()

    def change_last_song(self, instance):
        """ otwiera popupa do zmiany lasttrack """
        if instance.background_color == [0.81640625, 0.3125, 0.43359375, 1]:
            inst_change = PopupChange(self)
            self.get_last_track()
            inst_change.txt_input_change.text = self.last_track
            inst_change.last_song_txt.text = self.last_track
            self.poopup_window = Popup(title="Change last download song", content=inst_change, size_hint=(None, None),
                                       size=(self.width / 1.5, self.height / 1.1), separator_color=[0.453125, 0.26953125, 0.67578125, 1])
            self.poopup_window.open()

    def return_to_menu(self, instance):
        if instance.background_color == [0.81640625, 0.3125, 0.43359375, 1]:
            self.layout_manager.window_manager.transition.direction = 'left'
            self.layout_manager.window_manager.current = 'menu_lay'

    def download_music(self, dwn_dict):
        """ odpowiada za całe pobieranie, tworzy pasek postępu, blokuje guziki na czas pobierania, pobiera piosenki z
        listy w pętli, opartej na odwoływaniu sie w zegarze """
        self.make_progress_bar()
        self.un_or_block_btn(list_btn_to_block=[self.new_download_btn, self.select_songs_btn, self.load_btn, self.change_song_btn, self.return_btn, self.yt_api_btn], block=True)
        self.dwn_iter = 1
        self.len_dict = len(dwn_dict)
        self.dwn_dict = dwn_dict
        self.clear_scroll()
        self.scroll_float.add_widget(Label(text="Please wait for end downloading",
                                           font_size=self.height / 29 if self.width > self.height else self.width / 29,
                                     pos_hint={"x": 0.2, "y": 0.4}, size_hint=(0.6, 0.2)))
        Clock.schedule_once(self.call_to_dwn_more, 0)

    def call_to_dwn_more(self, x):
        """ funkcja która pobiera dany kawałek, odpowiednio modyfikując pasek postępu, lub kończy pobieranie sprzątjąc
        layout"""
        if self.dwn_iter < self.len_dict+1:
            self.make_dwn_grphs()
            self.download_song_with_ytdl()
            self.dwn_iter += 1
        elif self.dwn_iter == self.len_dict+1:
            self.make_dwn_grphs()
            self.download_music_end()

    def end_thread_download(self):
        Clock.schedule_once(self.call_to_dwn_more, 0)

    def download_error(self):
        self.download_music_end(text='Error')

    def download_song_with_ytdl(self):
        """ funkcja która wysyła dany kawałek zgodnie z kolejnością pobierania do objektu pobierającego"""
        url = list(self.dwn_dict.values())[self.dwn_iter - 1]
        name = list(self.dwn_dict.keys())[self.dwn_iter - 1]
        DownloaderOperations.download_music(self.inst_do, name=name, url=url, cause_inst=self)

    def make_dwn_grphs(self):
        """ tworzy pasek pobierania zgodnie ze zmiennymi towarzyszącymi pobieraniu """
        self.progress_maked.size_hint = (0.6 / self.len_dict * (self.dwn_iter - 1), 0.58)
        if self.dwn_iter != self.len_dict+1:
            self.progress_text.text = 'Download %s of %s -> %s' % (self.dwn_iter, self.len_dict, list(self.dwn_dict.keys())[self.dwn_iter - 1])
            self.progress_current.size_hint = (0.6 / self.len_dict * self.dwn_iter, 0.58)

    def download_music_end(self, text='Downloaded'):
        """ czyści pasek aktualnego pobrania, wyświetla napis i odwołuje sie do fukcji czyśczącej dolny pasek """
        self.progress_text.text = text
        self.clear_scroll()
        self.progress_current.size_hint = (0, 0)

        self.status_download_end = None
        if text != 'Downloaded':
            self.status_download_end = 'Error'
        Clock.schedule_once(self.download_music_end1, 1.8)

    def download_music_end1(self, _):
        """ Czyści pasek z pobieraniem, zdjemuje blokady na guzikach pobierania """
        self.progress_text.text = ''
        self.un_or_block_btn(
            list_btn_to_block=[self.load_btn, self.change_song_btn, self.return_btn, self.yt_api_btn],
            block=False)
        self.progress_base.size_hint = (0, 0)
        self.progress_maked.size_hint = (0, 0)
        if self.status_download_end != 'Error':
            JsonOperations.save_last_track(self.inst_jo, self.make_last_track_from_dict())   # po pobieraniu zapisuje najnowszy utwór jako najnowszą ścieżkę
        self.clear_scroll()

    def stretch_lay(self, songs_dict, load_songs2=True):
        """ rozciąa grid layout na odpowiednią szerokość tak aby utwory po zmianie ilości do wczytania poprawnie weszły
         do layouta, w tym celu ładuje odpowiednią ilośc tabeli do tego layouta, aktualizuje go, a następnie czyści """
        self.scroll_float.clear_widgets()
        self.scroll_float.add_widget(self.inst_scroll_viev)
        self.inst_songs_grid.fake_load(songs_dict)
        if load_songs2:
            Clock.schedule_once(self.stretch_lay2, 0)
        else:
            self.clear_scroll()

    def stretch_lay2(self, _):
        """ po wyczyszczeniu czyni dalsze operacje do ładowania utworów """
        self.clear_scroll()
        self.load_songs2()

    def clear_scroll(self):
        """ czyści z ekranu scrolowalną liste """
        self.scroll_float.clear_widgets()
        self.inst_scroll_viev.btn_extended_list = []
        self.inst_songs_grid.clear_widgets()
        self.txt_list.text = ''

    def make_progress_bar(self):
        """ tworzy tło paska pobierania """
        self.progress_text.text = 'Starting ...'
        self.progress_base.size_hint = (0.6, 0.58)

    def make_url_download_dict(self):
        """ tworzy ze słownika utworów słownik do pobierania """
        dict_to_reverse = self.song_dist_without_old()
        dwn_dict = self.reverse_dict(dict_to_reverse)
        return dwn_dict

    def song_dist_without_old(self):
        """ tworzy słownik tylko z nowymi utworami """
        dwn_dict = {}
        for key, value in self.songs_dict.items():
            if key == "↑ New, ↓ Old":
                break
            dwn_dict[key] = value
        return dwn_dict

    def reverse_dict(self, dict_to_reverse):
        """ odwraca kolejość słowanika {'x': 1, 'y': 2} na {'y':2, 'x': 1} """
        dwn_dict = {}
        new_key_list = list(dict_to_reverse.keys())
        new_key_list.reverse()
        new_value_list = list(dict_to_reverse.values())
        new_value_list.reverse()
        for x in range(0, len(dict_to_reverse)):
            dwn_dict[new_key_list[x]] = new_value_list[x]
        return dwn_dict

    def make_last_track_from_dict(self):
        """ zwraca najnowszy kawałek na kanale """
        if list(self.songs_dict.keys())[0] == "↑ New, ↓ Old":
            return list(self.songs_dict.keys())[1]
        else:
            return list(self.songs_dict.keys())[0]

    def make_chose_btn(self):
        """ tworzy guziki do wybierania piosenek """
        self.chose_btn_accept = Button(text='Accept', pos_hint={'x': 0.31, 'y': 0.201}, size_hint=(0.33, 0.098),
                                       background_color=(0.81640625, 0.3125, 0.43359375, 1), background_normal='')
        self.chose_btn_accept.bind(on_release=self.download_chosen)
        self.add_widget(self.chose_btn_accept)
        self.chose_btn_canel = Button(text='Canel', pos_hint={'x': 0.66, 'y': 0.201}, size_hint=(0.33, 0.098),
                                      background_color=(0.81640625, 0.3125, 0.43359375, 1), background_normal='')
        self.chose_btn_canel.bind(on_release=self.canel_chose)
        self.add_widget(self.chose_btn_canel)

    def download_chosen(self, instance):
        """ pobiera zaznaczone kawałki jeśli to możliwe i usuwa guziki """
        if self.inst_songs_grid.url_chose_dict == {}:
            self.progress_text.text = 'None songs selected'
            Clock.schedule_once(self.canel_chose, 1)
        else:
            self.hide_select_all_btn()
            self.download_music(self.inst_songs_grid.url_chose_dict)
            self.remove_widget(self.chose_btn_canel)
            self.remove_widget(self.chose_btn_accept)
            self.inst_songs_grid.url_chose_dict = {}

    def canel_chose(self, instance):
        """ czyści guziki i liste z wyborem, ustawia wartości domyślne """
        self.progress_text.text = ''
        self.remove_widget(self.chose_btn_canel)
        self.remove_widget(self.chose_btn_accept)
        self.un_or_block_btn(list_btn_to_block=[self.load_btn, self.change_song_btn, self.yt_api_btn], block=False)
        self.clear_scroll()
        self.inst_songs_grid.url_chose_dict = {}
        self.hide_select_all_btn()

    def un_or_block_btn(self, list_btn_to_block, block):
        """ blokuje lub odblokowywuje przyciski """
        if block:
            for x in list_btn_to_block:
                x.background_color = [0.6640625, 0.59765625, 0.6171875, 1]  # blokuje guzik
        else:
            for x in list_btn_to_block:
                x.background_color = [0.81640625, 0.3125, 0.43359375, 1]    # odblokowywuje guzik

    def get_last_track(self):
        """ zczytuje ze słownika piosenek ostatni pobrany utwór """
        self.last_track = JsonOperations.get_last_track(self.inst_jo)

    def select_all(self):
        """ funkcja zaznaczająca wszystkie guziki w instancji gridlayautu scrollview """
        for btn in self.inst_songs_grid.btn_extended_list:
            self.inst_songs_grid.url_chose_dict[btn.background_normal] = btn.background_down
            btn.background_color = [0.453125, 0.26953125, 0.67578125, 1]

    def show_select_all_btn(self):
        self.select_all_btn.opacity = 1
        self.select_all_btn.size_hint = (0.10, 0.05)

    def hide_select_all_btn(self):
        self.select_all_btn.opacity = 0
        self.select_all_btn.size_hint = (0, 0)

    def yt_api_load(self, instance):
        """ jeśli guzik jest aktywny ładuje za pomocą yt_api nowy słownik i go wrzuca na scrollview z wyborem """
        if instance.background_color == [0.81640625, 0.3125, 0.43359375, 1]:
            self.layout_manager.inst_loading_layout.show()
            Clock.schedule_once(self.yt_api_load1, 0)

    def yt_api_load1(self, _):
        """ wysyła żądanie do loadera yt_api aby zdobyć słownik utworów """
        self.old_songs_dict = self.songs_dict
        x = YtApiLoader(self)
        x.get_yt_api_dict()

    def end_yt_api_loader(self, yta_dict):
        """ wywoływane po skończeniu yt_api_loadera jeśli słownik jest pusty to zwraca błąd """
        # print("\t341 main end yt_api thread dict in inst_main_lay: ", yta_dict)
        self.songs_dict = yta_dict
        if yta_dict != {}:
            self.yt_api_load_after_loader()
        else:
            self.download_music_end(text="Error: can't connect")
        self.layout_manager.inst_loading_layout.hide('main_lay')

    def yt_api_load_after_loader(self):
        """ ładuje słownik do scrollview, zaznacza że piosenki są załadowane, dodaje widget scrolview, rozszerza layout
         scrollview do rozmiarów słownika, czyści grid, ładuje go do grid layout, z możliwością zaznaczenia blokuje
         guziki tworzy guziki wyboru """
        self.is_song_loaded = True

        # print("\t355 main start stretch lay to yt_api dict")
        if self.old_songs_dict is not None:      # jeśli lista utworów nie jest pusta to rozciąga najpierw box layout do wklejania utworów, aby poprawnie weszły
            self.stretch_lay(self.songs_dict, load_songs2=False)

        self.scroll_float.add_widget(self.inst_scroll_viev)

        self.txt_list.text = 'List of Songs:'
        self.inst_songs_grid.clear_widgets()

        # print("\t364 main start load yt_api dict to grid")
        self.inst_songs_grid.extended_dict_to_grid(songs_dict=self.songs_dict)
        # print("\t366 main end load yt_api dict to grid")
        self.un_or_block_btn(
            list_btn_to_block=[self.new_download_btn, self.select_songs_btn, self.load_btn, self.change_song_btn,
                               self.yt_api_btn],
            block=True)
        self.make_chose_btn()
        self.show_select_all_btn()

