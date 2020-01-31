from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.clock import Clock

from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.config import Config

import sys
from downloader_modul import DownloaderOperations, JsonOperations

Config.set('kivy', 'log_level', 'info')
# Config.set('kivy', 'log_level', 'critical')
Config.set('graphics', 'borderless', 0)
Config.set('graphics', 'window_state', 'maximized')
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
        """ Tworzy scrolowalną liste piosenek odblokowywuje inne opcje, jeśli opcje były już kiedyś ładowane czyści
        liste"""
        if instance.background_color == [0.81640625, 0.3125, 0.43359375, 1]:
            if self.is_song_loaded:
                self.clear_scroll()

            old_songs_dict = self.songs_dict
            self.songs_dict = DownloaderOperations.get_song_dict(self.inst_do)     # pobiera słownik utworów

            if old_songs_dict is not None:
                if len(old_songs_dict) != len(self.songs_dict):     # jeśli długość listy utworów została zmieniona to rozciąga najpierw box layout do wklejania utworów, aby poprawnie weszły
                    self.stretch_lay(self.songs_dict)
                else:
                    self.load_songs2()
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
                list_btn_to_block=[self.new_download_btn, self.select_songs_btn, self.load_btn, self.change_song_btn],
                block=True)
            self.make_chose_btn()

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

    def return_to_menu(self):
        window_manager.transition.direction = 'left'
        window_manager.current = 'menu_lay'

    @staticmethod
    def exit_app():
        sys.exit()

    def download_music(self, dwn_dict):
        """ odpowiada za całe pobieranie, tworzy pasek postępu, blokuje guziki na czas pobierania, pobiera piosenki z
        listy w pętli, opartej na odwoływaniu sie w zegarze """
        self.make_progress_bar()
        self.un_or_block_btn(list_btn_to_block=[self.new_download_btn, self.select_songs_btn, self.load_btn, self.change_song_btn], block=True)
        self.dwn_iter = 1
        self.len_dict = len(dwn_dict)
        self.dwn_dict = dwn_dict
        self.make_dwn_grphs()
        Clock.schedule_once(self.call_to_dwn_more, 0)

    def call_to_dwn_more(self, x):
        """ funkcja która pobiera dany kawałek, odpowiednio modyfikując pasek postępu, lub kończy pobieranie sprzątjąc
        layout"""
        if self.dwn_iter < self.len_dict+1:
            self.download_song_with_ytdl()
            self.dwn_iter += 1
            self.make_dwn_grphs()
            self.call_to_call_tdm()
        elif self.dwn_iter == self.len_dict+1:
            self.download_music_end()

    def call_to_call_tdm(self):
        Clock.schedule_once(self.call_to_dwn_more, 0.5)
        print(self.progress_text.text)

    def download_song_with_ytdl(self):
        """ funkcja która wysyła dany kawałek zgodnie z kolejnością pobierania do objektu pobierającego"""
        url = list(self.dwn_dict.values())[self.dwn_iter - 1]
        name = list(self.dwn_dict.keys())[self.dwn_iter - 1]
        DownloaderOperations.download_music(self.inst_do, name=name, url=url)

    def make_dwn_grphs(self):
        """ tworzy pasek pobierania zgodnie ze zmiennymi towarzyszącymi pobieraniu """
        self.progress_maked.size_hint = (0.6 / self.len_dict * (self.dwn_iter - 1), 0.58)
        if self.dwn_iter != self.len_dict+1:
            self.progress_text.text = 'Download %s of %s -> %s' % (self.dwn_iter, self.len_dict, list(self.dwn_dict.keys())[self.dwn_iter - 1])
            self.progress_current.size_hint = (0.6 / self.len_dict * self.dwn_iter, 0.58)

    def download_music_end(self):
        """ czyści pasek aktualnego pobrania, wyświetla napis i odwołuje sie do fukcji czyśczącej dolny pasek """
        self.progress_text.text = 'Downloaded'
        self.progress_current.size_hint = (0, 0)
        Clock.schedule_once(self.download_music_end1, 0.8)

    def download_music_end1(self, delta_time):
        """ Czyści pasek z pobieraniem, zdjemuje blokady na guzikach pobierania """
        self.progress_text.text = ''
        self.un_or_block_btn(
            list_btn_to_block=[self.load_btn, self.change_song_btn],
            block=False)
        self.progress_base.size_hint = (0, 0)
        self.progress_maked.size_hint = (0, 0)
        JsonOperations.save_last_track(self.inst_jo, self.make_last_track_from_dict())   # po pobieraniu zapisuje najnowszy utwór jako najnowszą ścieżkę
        self.clear_scroll()

    def stretch_lay(self, songs_dict):
        """ rozciąa grid layout na odpowiednią szerokość tak aby utwory po zmianie ilości do wczytania poprawnie weszły
         do layouta, w tym celu ładuje odpowiednią ilośc tabeli do tego layouta, aktualizuje go, a następnie czyści """
        self.scroll_float.add_widget(inst_scroll_viev)
        inst_songs_grid.fake_load(songs_dict)
        Clock.schedule_once(self.stretch_lay2, 0)

    def stretch_lay2(self, delta_time):
        """ po wyczyszczeniu czyni dalsze operacje do ładowania utworów """
        self.clear_scroll()
        self.load_songs2()

    def clear_scroll(self):
        """ czyści z ekranu scrolowalną liste """
        self.scroll_float.clear_widgets()
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
            self.download_music(inst_songs_grid.url_chose_dict)
            self.remove_widget(self.chose_btn_canel)
            self.remove_widget(self.chose_btn_accept)
            inst_songs_grid.url_chose_dict = {}

    def canel_chose(self, instance):
        """ czyści guziki i liste z wyborem, ustawia wartości domyślne """
        self.progress_text.text = ''
        self.remove_widget(self.chose_btn_canel)
        self.remove_widget(self.chose_btn_accept)
        self.un_or_block_btn(list_btn_to_block=[self.load_btn, self.change_song_btn], block=False)
        self.clear_scroll()
        inst_songs_grid.url_chose_dict = {}

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
            wid = Label(text=key, color=(1, 1, 1, 1), font_name='Arial')
            wid.font_size = self.width / 37
            if key == "↑ New, ↓ Old":
                wid.color = (0.8980392156862745, 0.6274509803921569, 0.8588235294117647, 1)
            self.add_widget(wid)

    def extended_dict_to_grid(self, songs_dict):
        """ wprowadza do grid layout 2kolumnowe lisy, gdzie jest guzik do zaznacznia odzanczania zapisujący url
         zaznaczonych utworów, jeśli trafi na rozdziałke to nie wprowadza guzika"""
        self.cols = 2
        self.size_hint = (1, len(songs_dict) / 10)
        for key in songs_dict:
            wid = Label(text=key, size_hint_x=0.9, color=(1, 1, 1, 1), font_name='Arial', font_size=self.width / 37)
            if key == "↑ New, ↓ Old" or songs_dict[key] == 'Error':
                but = Label(size_hint_x=0.1)
                wid.color = (0.8980392156862745, 0.6274509803921569, 0.8588235294117647, 1)
            else:
                but = Button(size_hint_x=0.1, background_normal=key, background_down=songs_dict[key], background_color=(0.8980392156862745, 0.6274509803921569, 0.8588235294117647, 1))
                but.bind(on_press=self.song_btn_press)
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
    file_type_input = ObjectProperty(None)
    channel_input = ObjectProperty(None)

    @staticmethod
    def go_return():
        window_manager.transition.direction = 'down'
        window_manager.current = 'menu_lay'

    def save_options(self):
        """ zapisuje opcje, jeśli zmieniono kanał to czyści załadowne opcje i blokuje pobieranie, aby uniknąć błędów """
        options_dict = JsonOperations.load_json('config.json')

        options_dict['save_path'] = self.dir_input.text
        if self.check_file_type(self.file_type_input.text):
            options_dict['file_type'] = self.file_type_input.text
        else:
            self.notvalid_option_popup('Chose valid file type!\nSupported types: \naac, m4a, mp3, wav')

        self.check_channel_options(self.channel_input.text)
        if options_dict['channel'] != self.channel_input.text:
            self.block_on_change_channel()
            options_dict['channel'] = self.channel_input.text

        JsonOperations.save_json(options_dict, 'config.json')

        self.save_btn.text = 'Saved'
        Clock.schedule_once(self.change_text_save_btn, 0.8)

    def change_text_save_btn(self, delta_time):
        self.save_btn.text = 'Save'

    @staticmethod
    def check_file_type(text):
        if text in ['aac', 'm4a', 'mp3', 'wav']:
            return True
        else:
            return False

    def notvalid_option_popup(self, text):
        show = Label(text=text, font_size=self.height / 20 if self.width > self.height else self.width / 20)
        self.popup_window = Popup(title='Error', content=show, size_hint=(None, None), size=(self.width / 2, self.height / 1.5),
                             separator_color=[0.453125, 0.26953125, 0.67578125, 1])
        self.popup_window.open()
        Clock.schedule_once(self.notvalid_option_popup2, 1.5)

    def notvalid_option_popup2(self, delta_time):
        self.popup_window.dismiss()

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
        self.file_type_input.text = conf_dict['file_type']


class AddressDownloadLayout(Screen):
    """ umożliwia pobranie fimu z yt bezpośrednio po adresie, jeśli adres będzie nipoprawny to wyskoczy błąd """
    address_input = ObjectProperty(None)
    status_text = ObjectProperty(None)

    @staticmethod
    def go_return():
        window_manager.transition.direction = 'right'
        window_manager.current = 'menu_lay'

    def download_address(self):
        """ pobiera dany adres """
        self.status_text.size_hint = (0.6, 0.2)
        self.status_text.text = 'Status: Downloading'
        Clock.schedule_once(self.download_address1, 0)

    def download_address1(self, delta_time):
        """ pobiera dany adres w przypadku błędu zwraca błęd połączenia """
        status = DownloaderOperations.ytdl_download(DownloaderOperations(), self.address_input.text)
        self.status_text.text = status
        Clock.schedule_once(self.download_address2, 1)

    def download_address2(self, delta_time):
        self.status_text.size_hint = (0, 0)
        self.status_text.text = ""
        self.address_input.text = ""


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
            self.get_results_music()
            self.name_input.text = ''
            window_manager.transition.direction = 'left'
            window_manager.current = 'name_result_lay'

    def get_results_music(self):
        result_dict = DownloaderOperations().get_adress_dict_from_search(self.name_input.text)
        inst_name_result_layout.load_songs_to_grid(result_dict)


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

    @staticmethod
    def go_return():
        """ wraca do menu """
        window_manager.transition.direction = 'right'
        window_manager.current = 'name_dwn_lay'

    def load_songs_to_grid(self, result_dict):
        """ służy do załadowania nazw utworów do listy pobierania, z result_dict """
        self.result_dict = result_dict
        label_list = [self.song1_name, self.song2_name, self.song3_name, self.song4_name, self.song5_name]
        for x, y in enumerate(result_dict.keys()):
            label_list[x].text = y

    def download_music(self, instance):
        """ pobiera kawałek o takim numerze w słowniku jak instance czyli numer guzika """
        if self.result_dict != {"Error: Can't connect to this yt channel": 'Error'}:
            self.download_address = self.get_download_address(instance)
            self.status_label.text = 'Status: Downloading'
            self.download_music1()

    def get_download_address(self, btn_instance):
        return list(self.result_dict.values())[btn_instance]

    def download_music1(self):
        Clock.schedule_once(self.download_address1, 0)

    def download_address1(self, delta_time):
        """ pobiera dany adres w przypadku błędu zwraca błęd połączenia """
        status = DownloaderOperations.ytdl_download(DownloaderOperations(), self.download_address)
        self.status_label.text = status
        Clock.schedule_once(self.download_address2, 1)

    def download_address2(self, delta_time):
        Clock.schedule_once(self.download_address3, 1)
        self.status_label.text = "Status: Downloaded"

    def download_address3(self, delta_time):
        window_manager.transition.direction = 'right'
        window_manager.current = 'name_dwn_lay'
        self.status_label.text = 'Select Video:'


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

Window.maximize()


class ChillApp(App):
    def build(self):
        self.icon = 'CMDownloader_logo.png'
        self.title = 'Chill Music Downloader'
        return window_manager


if __name__ == '__main__':
    ChillApp().run()
