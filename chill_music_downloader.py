from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.dropdown import DropDown
from kivy.clock import Clock

from kivy.uix.screenmanager import NoTransition, SlideTransition
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.config import Config

from kivy.animation import Animation

from kivy.graphics import *

import sys
import threading
from downloader_modul import DownloaderOperations, JsonOperations
from yt_api_modul import YtApiLoader
from parse_modul import parse_yt_channel_name

# Config.set('kivy', 'log_level', 'info')
Config.set('kivy', 'log_level', 'critical')
# Config.set('graphics', 'borderless', 0)
Config.set('graphics', 'window_state', 'minimized')
# Config.set('graphics', 'window_state',  "visible")
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.write()
kv_lay = Builder.load_file('chill_layout.kv')


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

    def __init__(self, **kwargs):
        super(MainChillLayout, self).__init__(**kwargs)
        self.is_song_loaded = False     # wzkaźnik sprawdzający czy są załadowane utwory, gdyż trzeba je mieć aby pobrać
        self.songs_dict = None      # lista z utworami
        self.last_track = 'To check load songs'     # wyświetlanie ostatniej ścieżki do change

        self.inst_jo = JsonOperations()   # wspólna instancja json operations
        self.inst_do = DownloaderOperations()   # wspólna instancja json operations

    def load_songs(self, instance):
        if instance.background_color == [0.81640625, 0.3125, 0.43359375, 1]:
            inst_loading_layout.show()
            Clock.schedule_once(self.load_songs1, 0.01)

    def load_songs1(self, delta_time):
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
        self.scroll_float.add_widget(inst_scroll_viev)

        inst_songs_grid.load_dict_to_grid(self.songs_dict)  # tworzy liste piosenek

        self.txt_list.text = 'List of Songs:'

        self.is_song_loaded = True

        if list(self.songs_dict.keys())[0] == '↑ New, ↓ Old':  # jeśli nie ma nowych utworów to nie można nic pobierać
            self.un_or_block_btn(list_btn_to_block=[self.select_songs_btn], block=False)
        elif list(self.songs_dict.values())[0] == 'Error':
            self.un_or_block_btn(list_btn_to_block=[self.new_download_btn, self.select_songs_btn], block=True)
        else:
            self.un_or_block_btn(list_btn_to_block=[self.new_download_btn, self.select_songs_btn], block=False)

        self.get_last_track()
        inst_loading_layout.hide('main_lay')

    def download_all_new(self, instance):
        """ pobiera wszystkie nowe utwory jeśli został klikniety guzik, tworzy słownik utworów do pobrania """
        if instance.background_color == [0.81640625, 0.3125, 0.43359375, 1]:
            dwn_dict = self.make_url_download_dict()
            self.download_music(dwn_dict)

    def start_selection_songs(self, instance):
        """ odpowiada za umożliwienie  wybierania utworów do pobrania """
        if instance.background_color == [0.81640625, 0.3125, 0.43359375, 1]:
            inst_songs_grid.clear_widgets()
            inst_songs_grid.extended_dict_to_grid(songs_dict=self.songs_dict)
            self.un_or_block_btn(
                list_btn_to_block=[self.new_download_btn, self.select_songs_btn, self.load_btn, self.change_song_btn,
                                   self.yt_api_btn],
                block=True)
            self.make_chose_btn()
            self.show_select_all_btn()

    def change_last_song(self, instance):
        """ otwiera popupa do zmiany lasttrack """
        if instance.background_color == [0.81640625, 0.3125, 0.43359375, 1]:
            inst_change = PopupChange()
            self.get_last_track()
            inst_change.txt_input_change.text = self.last_track
            inst_change.last_song_txt.text = self.last_track
            self.poopup_window = Popup(title="Change last download song", content=inst_change, size_hint=(None, None),
                                       size=(self.width / 1.5, self.height / 1.1), separator_color=[0.453125, 0.26953125, 0.67578125, 1])
            self.poopup_window.open()

    def return_to_menu(self, instance):
        if instance.background_color == [0.81640625, 0.3125, 0.43359375, 1]:
            window_manager.transition.direction = 'left'
            window_manager.current = 'menu_lay'

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
        Clock.schedule_once(self.download_music_end1, 0.8)

    def download_music_end1(self, delta_time):
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
        self.scroll_float.add_widget(inst_scroll_viev)
        inst_songs_grid.fake_load(songs_dict)
        if load_songs2:
            Clock.schedule_once(self.stretch_lay2, 0)
        else:
            self.clear_scroll()

    def stretch_lay2(self, delta_time):
        """ po wyczyszczeniu czyni dalsze operacje do ładowania utworów """
        self.clear_scroll()
        self.load_songs2()

    def clear_scroll(self):
        """ czyści z ekranu scrolowalną liste """
        self.scroll_float.clear_widgets()
        inst_scroll_viev.btn_extended_list = []
        inst_songs_grid.clear_widgets()
        self.txt_list.text = ''

    def make_progress_bar(self):
        """ tworzy tło paska pobierania """
        self.progress_text.text = 'Rozpoczynanie ...'
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
        if inst_songs_grid.url_chose_dict == {}:
            self.progress_text.text = 'None songs selected'
            Clock.schedule_once(self.canel_chose, 1)
        else:
            self.hide_select_all_btn()
            self.download_music(inst_songs_grid.url_chose_dict)
            self.remove_widget(self.chose_btn_canel)
            self.remove_widget(self.chose_btn_accept)
            inst_songs_grid.url_chose_dict = {}

    def canel_chose(self, instance):
        """ czyści guziki i liste z wyborem, ustawia wartości domyślne """
        self.progress_text.text = ''
        self.remove_widget(self.chose_btn_canel)
        self.remove_widget(self.chose_btn_accept)
        self.un_or_block_btn(list_btn_to_block=[self.load_btn, self.change_song_btn, self.yt_api_btn], block=False)
        self.clear_scroll()
        inst_songs_grid.url_chose_dict = {}
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
        for btn in inst_songs_grid.btn_extended_list:
            inst_songs_grid.url_chose_dict[btn.background_normal] = btn.background_down
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
            inst_loading_layout.show()
            Clock.schedule_once(self.yt_api_load1, 0)

    def yt_api_load1(self, delta_time):
        """ wysyła żądanie do loadera yt_api aby zdobyć słownik utworów """
        self.old_songs_dict = self.songs_dict
        x = YtApiLoader(self)
        x.get_yt_api_dict()

    def end_yt_api_loader(self, yta_dict):
        """ wywoływane po skończeniu yt_api_loadera jeśli słownik jest pusty to zwraca błąd """
        self.songs_dict = yta_dict
        if yta_dict != {}:
            self.yt_api_load_after_loader()
        else:
            self.download_music_end(text="Error: can't connect")
        inst_loading_layout.hide('main_lay')

    def yt_api_load_after_loader(self):
        """ ładuje słownik do scrollview, zaznacza że piosenki są załadowane, dodaje widget scrolview, rozszerza layout
         scrollview do rozmiarów słownika, czyści grid, ładuje go do grid layout, z możliwością zaznaczenia blokuje
         guziki tworzy guziki wyboru """
        self.is_song_loaded = True

        if self.old_songs_dict is not None:      # jeśli lista utworów nie jest pusta to rozciąga najpierw box layout do wklejania utworów, aby poprawnie weszły
            self.stretch_lay(self.songs_dict, load_songs2=False)

        self.scroll_float.add_widget(inst_scroll_viev)

        self.txt_list.text = 'List of Songs:'
        inst_songs_grid.clear_widgets()
        inst_songs_grid.extended_dict_to_grid(songs_dict=self.songs_dict)
        self.un_or_block_btn(
            list_btn_to_block=[self.new_download_btn, self.select_songs_btn, self.load_btn, self.change_song_btn,
                               self.yt_api_btn],
            block=True)
        self.make_chose_btn()
        self.show_select_all_btn()


class SongsGrid(GridLayout):
    """ Grid layout gdzie ładujemy utwory, aby je pokazać użytkownikowi, przed załadowaniem jest pusty, ta klasa jest
    dzieckiem inst_scroll_viev, posiada liste z url zaznaczonych"""

    def __init__(self, **kwargs):
        super(SongsGrid, self).__init__(**kwargs)
        self.url_chose_dict = {}       # domyślny słownik gdzie będą zapisywane url zaznaczonych utworów

    def load_dict_to_grid(self, songs_dict):
        """ wpisuje do grodlayout 1 kolumnową liste utworów """
        self.cols = 1
        self.size_hint = (1, 1 + (len(songs_dict) / 10))
        self.songs_dict = songs_dict
        Clock.schedule_once(self.load_dict_to_grid2, 0)

    def load_dict_to_grid2(self, delta_time):
        for key in self.songs_dict:
            wid = Label(text=key, color=(1, 1, 1, 1), font_name='Arial', font_size=int(inst_main_chill_layout.width / 40))
            wid.font_size = self.width / 37
            if key == "↑ New, ↓ Old":
                wid.color = (0.8980392156862745, 0.6274509803921569, 0.8588235294117647, 1)
            self.add_widget(wid)

    def extended_dict_to_grid(self, songs_dict):
        """ wprowadza do grid layout 2kolumnowe lisy, gdzie jest guzik do zaznacznia odzanczania zapisujący url
         zaznaczonych utworów, jeśli trafi na rozdziałke to nie wprowadza guzika"""
        # print(" 399 cmd.py: ", songs_dict)
        self.cols = 2
        self.size_hint = (1, 1 + (len(songs_dict) / 10))
        self.btn_extended_list = []
        for key in songs_dict:
            wid = Label(text=key, size_hint_x=0.9, color=(1, 1, 1, 1), font_name='Arial', font_size=int(inst_main_chill_layout.width / 55))
            if key == "↑ New, ↓ Old" or key == 'Error' or key == 'Your daily limit expires' or key == 'Invalid channel name':
                but = Label(size_hint_x=0.1)
                wid.color = (0.8980392156862745, 0.6274509803921569, 0.8588235294117647, 1)
            else:
                but = Button(size_hint_x=0.1, background_normal=key, background_down=songs_dict[key], background_color=(0.8980392156862745, 0.6274509803921569, 0.8588235294117647, 1))
                but.bind(on_press=self.song_btn_press)
                self.btn_extended_list.append(but)
            self.add_widget(but)
            self.add_widget(wid)

    def fake_load(self, work_dict):
        """ dodaje do layoutu taką ilość tabel, aby wysokość layoutu ustawiła się na taką jak po wczytaniu tego
        słownika """
        self.cols = 1
        self.size_hint = (1, 1 + (len(work_dict) / 10))
        for x in range(0, len(work_dict)):
            wid = Label()
            self.add_widget(wid)

    def song_btn_press(self, instance):
        """ zapisuje do listy addressy url zaznaczonych pisenek, działa w zależności od koloru
        (0.8980392156862745, 0.6274509803921569, 0.8588235294117647, 1) - niezaznaczony, [0.453125, 0.26953125, 0.67578125, 1] - zaznaczony
         """
        if instance.background_color == [0.8980392156862745, 0.6274509803921569, 0.8588235294117647, 1]:
            self.url_chose_dict[instance.background_normal] = instance.background_down
            instance.background_color = [0.453125, 0.26953125, 0.67578125, 1]
        elif instance.background_color == [0.453125, 0.26953125, 0.67578125, 1]:
            self.url_chose_dict.pop(instance.background_normal)
            instance.background_color = [0.8980392156862745, 0.6274509803921569, 0.8588235294117647, 1]


class PopupChange(Screen):
    """ popup do zmiany nowego utworu, wyświetla lasttrack i przez text input umożliwia jego zmiane """
    txt_input_change = ObjectProperty(None)
    last_song_txt = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(PopupChange, self).__init__(**kwargs)

    def if_yes(self):
        """ zapisuje input z popupa jako ostatnią ścierzkę """
        x = JsonOperations()
        JsonOperations.save_last_track(x, self.txt_input_change.text)
        inst_main_chill_layout.get_last_track()
        inst_main_chill_layout.un_or_block_btn(list_btn_to_block=[inst_main_chill_layout.new_download_btn, inst_main_chill_layout.select_songs_btn], block=True)
        inst_main_chill_layout.poopup_window.dismiss()

    @staticmethod
    def if_no():
        """ wyłącza okno """
        inst_main_chill_layout.poopup_window.dismiss()


class MainMenu(Screen):

    @staticmethod
    def go_to_chanel_dwn():
        window_manager.transition.direction = 'right'
        window_manager.current = 'main_lay'

    @staticmethod
    def go_to_address_dwn():
        window_manager.transition.direction = 'left'
        window_manager.current = 'address_dwn_lay'

    @staticmethod
    def go_to_name_dwn():
        window_manager.transition.direction = 'down'
        window_manager.current = 'name_dwn_lay'

    @staticmethod
    def go_to_options():
        window_manager.transition.direction = 'up'
        window_manager.current = 'options_lay'
        inst_options.make_options()

    @staticmethod
    def exit_app():
        sys.exit()


class OptionsLay(Screen):
    """ layout zawierający możliwość zmainy opcji, czyli ścieżki pobierania narazie """
    save_btn = ObjectProperty(None)
    dir_input = ObjectProperty(None)
    channel_input = ObjectProperty(None)
    change_file_type_dropdown_main_btn = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(OptionsLay, self).__init__(**kwargs)
        self.maked_dropdown = False

    @staticmethod
    def go_return():
        window_manager.transition.direction = 'down'
        window_manager.current = 'menu_lay'

    def save_options(self):
        """ zapisuje opcje, jeśli zmieniono kanał to czyści załadowne opcje i blokuje pobieranie, aby uniknąć błędów """
        options_dict = JsonOperations.load_json('config.json')

        options_dict['save_path'] = self.dir_input.text
        options_dict['file_type'] = self.change_file_type_dropdown_main_btn.text

        if self.parse_yt_channel_name():
            self.format_channel_input()
            self.check_channel_options(self.channel_input.text)
            if options_dict['channel'] != self.channel_input.text:
                self.block_on_change_channel()
                options_dict['channel'] = self.channel_input.text

            self.save_btn.text = 'Saved'
        else:
            self.save_btn.text = 'Bad channel'
        JsonOperations.save_json(options_dict, 'config.json')
        Clock.schedule_once(self.change_text_save_btn, 0.8)

    def change_text_save_btn(self, delta_time):
        self.save_btn.text = 'Save'

    def parse_yt_channel_name(self):
        """ za pomocą zewnętrznej funkcji sprawdza czy podany adres jest poprwany, czyli czy jest po  nazwie lub id """
        if parse_yt_channel_name(self.channel_input.text):
            return True
        return False

    def format_channel_input(self):
        """ odcina niepotrzebną końcówkę w adresie """
        txt = self.channel_input.text
        if len(txt.split("/")) != 5:
            self.channel_input.text = "/".join(txt.split("/")[:5])

    @staticmethod
    def check_channel_options(new_channel):
        """ jeśli nowego kanału nie ma w bazie ostanich utworów to go dodaje """
        last_track_dict = JsonOperations.load_json('last_track.json')
        if new_channel not in last_track_dict.keys():
            last_track_dict[new_channel] = ''
            JsonOperations.save_json(last_track_dict, 'last_track.json')

    @staticmethod
    def block_on_change_channel():
        """ czyści liste utworów w layoucie i blokuje pobieranie przy zmianie kanału w opcjach """
        inst_main_chill_layout.clear_scroll()
        inst_main_chill_layout.un_or_block_btn(list_btn_to_block=[inst_main_chill_layout.new_download_btn, inst_main_chill_layout.select_songs_btn], block=True)

    def make_options(self):
        conf_dict = DownloaderOperations.get_all_config()
        self.dir_input.text = conf_dict['save_path']
        self.channel_input.text = conf_dict['channel']
        self.change_file_type_dropdown_main_btn.text = conf_dict['file_type']
        if not self.maked_dropdown:
            self.make_dropdown()

    def make_dropdown(self):
        self.dropdown = DropDown()
        self.dropdown.dismiss_on_select = False
        for ft_name in ['aac', 'm4a', 'mp3', 'wav']:
            dd_btn = Button(text=ft_name, size_hint_y=None, height=50, background_normal='', border=(16, 16, 16, 16),
                            background_color=[0.81640625, 0.3125, 0.43359375, 1])
            dd_btn.bind(on_release=self.release_dropdown_button)
            self.dropdown.add_widget(dd_btn)
        self.change_file_type_dropdown_main_btn.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select=lambda instance, dd_main_text: setattr(self.change_file_type_dropdown_main_btn, 'text', dd_main_text))
        self.maked_dropdown = True

    def release_dropdown_button(self, instance):
        self.dropdown.select(instance.text)
        self.dropdown.dismiss()


class AddressDownloadLayout(Screen):
    """ umożliwia pobranie fimu z yt bezpośrednio po adresie, jeśli adres będzie nipoprawny to wyskoczy błąd """
    address_input = ObjectProperty(None)
    status_text = ObjectProperty(None)
    download_btn = ObjectProperty(None)
    return_btn = ObjectProperty(None)
    dwn_lock = False

    def go_return(self):
        if not self.dwn_lock:
            window_manager.transition.direction = 'right'
            window_manager.current = 'menu_lay'

    def download_address(self):
        """ pobiera dany adres """
        if not self.dwn_lock:
            self.edit_lock_dwn(True)
            self.status_text.size_hint = (0.6, 0.2)
            self.make_extend_status()
            Clock.schedule_once(self.download_address1, 0)

    def download_address1(self, delta_time):
        """ pobiera dany adres w przypadku błędu zwraca błęd połączenia """
        DownloaderOperations.ytdl_download(DownloaderOperations(), self.address_input.text, self)

    def end_thread_download(self, *args):
        self.status_text.size_hint = (0, 0)
        self.status_text.text = ""
        self.address_input.text = ""
        self.edit_lock_dwn(False)

    def download_error(self):
        self.status_text.text = 'Error'
        Clock.schedule_once(self.end_thread_download, 1)

    def edit_lock_dwn(self, lock):
        if lock:
            self.dwn_lock = True
            self.return_btn.background_color = [0.6640625, 0.59765625, 0.6171875, 1]
            self.download_btn.background_color = [0.6640625, 0.59765625, 0.6171875, 1]
        else:
            self.dwn_lock = False
            self.return_btn.background_color = [0.81640625, 0.3125, 0.43359375, 1]
            self.download_btn.background_color = [0.81640625, 0.3125, 0.43359375, 1]

    def make_extend_status(self):
        x = DownloaderOperations().get_video_title(self.address_input.text, self)
        self.status_text.text = "Status: Downloading \n" + x


class NameDownloadLayout(Screen):
    """ pobiera piosenke po nazwie, w menu ten layout ustawiny jest u góry, po wpisaniu nazwy w pole tekstowe i
    zatwierdzeniu czyści input, zabiera słownik z utworami linkami otrzymanymi po wyszukaniu podanej frazy w yt i za
    jego pomocą tworzy zawartość NameResultLayout po czym tam się przełącza """
    name_input = ObjectProperty(None)
    text_label = ObjectProperty(None)
    check_btn = ObjectProperty(None)
    name_results_float = ObjectProperty(None)
    status_text = ObjectProperty(None)

    @staticmethod
    def go_return():
        window_manager.transition.direction = 'up'
        window_manager.current = 'menu_lay'

    def download_by_name(self):
        if self.name_input.text != '':
            inst_loading_layout.show()
            Clock.schedule_once(self.download_by_name1, 0.1)

    def download_by_name1(self, delta_time):
        self.get_results_music()

    def get_results_music(self):
        """ wywołuje wątek pobierający wyniki wyszukiwania, który po zrobieniu swojej roboty wywołuje
        internet_thread_end który zajmuje się załadowaniem wyników do drugiego okna i zmianom grafiki """
        DownloaderOperations().get_adress_dict_from_search(self.name_input.text, self)

    def internet_thread_end(self, result_dict):
        """ wywoływane po załadowaniu słownika adresów przez InternetSearchThread zajmuje się załadowaniem następnego
        okna i przygotowaniem grafiki """
        inst_name_result_layout.load_songs_to_grid(result_dict)
        self.name_input.text = ''
        inst_loading_layout.hide('name_dwn_lay')
        window_manager.transition.direction = 'left'
        window_manager.current = 'name_result_lay'


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

    def go_return(self):
        """ wraca do menu """
        if not self.dwn_lock:
            window_manager.transition.direction = 'right'
            window_manager.current = 'name_dwn_lay'

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
            self.status_label.text = 'Status: Downloading %s' % (self.get_download_name(instance))
            self.download_music1()

    def get_download_address(self, btn_instance):
        return list(self.result_dict.values())[btn_instance]

    def get_download_name(self, btn_instance):
        return list(self.result_dict.keys())[btn_instance]

    def download_music1(self):
        Clock.schedule_once(self.download_address1, 0)

    def download_address1(self, delta_time):
        """ pobiera dany adres w przypadku błędu zwraca błąd połączenia """
        DownloaderOperations.ytdl_download(DownloaderOperations(), self.download_address, self)

    def end_thread_download(self):
        """ wywoływane z wątku pobierania po skończeniu pracy """
        Clock.schedule_once(self.download_address2, 1)

    def download_error(self):
        """ wywoływane z wątku pobierania w przypadku błędu """
        Clock.schedule_once(self.download_address3, 1.5)
        self.status_label.text = "Status: Error"

    def download_address2(self, delta_time):
        Clock.schedule_once(self.download_address3, 1.5)
        self.status_label.text = "Status: Downloaded"

    def download_address3(self, delta_time):
        window_manager.transition.direction = 'right'
        window_manager.current = 'name_dwn_lay'
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


class LoadingLayout(Screen):
    """ Layout pokazujący obraz ładowania, za pomocą show aktywuje się go a hidem chowa, tworzy też element obracania
    dla logo_loading """
    logo_loading = ObjectProperty(None)
    loading_float_lay = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(LoadingLayout, self).__init__(**kwargs)
        with self.logo_loading.canvas.before:
            PushMatrix()
            self.rotation = Rotate(angle=0, origin=[1, 1])

        with self.logo_loading.canvas.after:
            PopMatrix()

    def show(self):
        """ pokazuje swoją klasę i włącza animacje """
        window_manager.transition = NoTransition()
        window_manager.current = 'load_lay'
        self.clock = Clock.schedule_once(self.animate_logo, 0)

    def animate_logo(self, delta_time):
        """ włącza animacje w osobnym wątku """
        self.ath = AnimateThread(self)
        self.ath.start()

    def hide(self, cause_inst_name):
        """ chowa ekran wracjąc do tekgo który zdecydował sięschować, wyłącza animacje i zegary """
        self.clock.cancel()
        self.ath.stop()
        window_manager.current = cause_inst_name
        window_manager.transition = SlideTransition()


class AnimateThread(threading.Thread, LoadingLayout):
    """ Kręci tłem loga w oparciu o instancję wywołującą """
    def __init__(self, instance, **kwargs):
        super(AnimateThread, self).__init__(**kwargs)
        self.instance = instance

    def run(self):
        """ rozpoczyna zapętloną animacje """
        self.instance.rotation.origin = [self.instance.width/2, self.instance.height/2]
        anim = Animation(angle=360, duration=1.5, t='in_cubic') + Animation(angle=0, duration=0)
        anim.start(self.instance.rotation)
        anim.repeat = True

    def stop(self):
        """ kończy animacje """
        Animation.cancel_all(self.instance.rotation, 'angle')


""" objekt ScrollViev odpowiadający za scrolowanie Songs grid, jest dzieckiem głownego layoutu """
inst_scroll_viev = ScrollView(size_hint=(1, 1), size=(Window.width, Window.height), pos_hint={'x': 0, 'y': 0})
inst_songs_grid = SongsGrid()
inst_songs_grid.bind(minimum_height=inst_songs_grid.setter('height'))
inst_scroll_viev.add_widget(inst_songs_grid)

window_manager = ScreenManager()

inst_main_menu = MainMenu(name='menu_lay')
window_manager.add_widget(inst_main_menu)

inst_options = OptionsLay(name='options_lay')
window_manager.add_widget(inst_options)

inst_main_chill_layout = MainChillLayout(name='main_lay')
window_manager.add_widget(inst_main_chill_layout)

inst_address_download_layout = AddressDownloadLayout(name='address_dwn_lay')
window_manager.add_widget(inst_address_download_layout)

inst_name_download_layout = NameDownloadLayout(name='name_dwn_lay')
window_manager.add_widget(inst_name_download_layout)

inst_name_result_layout = NameResultLayout(name='name_result_lay')
window_manager.add_widget(inst_name_result_layout)

inst_loading_layout = LoadingLayout(name='load_lay')
window_manager.add_widget(inst_loading_layout)

Clock.max_iteration = 5000       # określa maksymalną liczbę zagniżdżonych zegarów

Window.maximize()


class ChillApp(App):
    def build(self):
        self.icon = 'CMDownloader_logo.png'
        self.title = 'Chill Music Downloader'
        return window_manager


if __name__ == '__main__':
    ChillApp().run()
