from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.uix.dropdown import DropDown
from kivy.clock import Clock
from kivy.uix.button import Button

from app.modules.downloader_modul import DownloaderOperations
from app.modules.json_operations_modul import JsonOperations
from app.modules.parse_modul import parse_yt_channel_name


class OptionsLay(Screen):
    """ layout zawierający możliwość zmainy opcji, czyli ścieżki pobierania narazie """
    save_btn = ObjectProperty(None)
    dir_input = ObjectProperty(None)
    channel_input = ObjectProperty(None)
    change_file_type_dropdown_main_btn = ObjectProperty(None)

    def __init__(self, layout_manager, **kwargs):
        super(OptionsLay, self).__init__(**kwargs)
        self.maked_dropdown = False
        self.layout_manager = layout_manager

    def go_return(self):
        self.layout_manager.window_manager.transition.direction = 'down'
        self.layout_manager.window_manager.current = 'menu_lay'

    def save_options(self):
        """ zapisuje opcje, jeśli zmieniono kanał to czyści załadowne opcje i blokuje pobieranie, aby uniknąć błędów """
        options_dict = JsonOperations.load_json('../data/config.json')

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
        JsonOperations.save_json(options_dict, '../data/config.json')
        Clock.schedule_once(self.change_text_save_btn, 0.8)

    def change_text_save_btn(self, _):
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
        last_track_dict = JsonOperations.load_json('../data/last_track.json')
        if new_channel not in last_track_dict.keys():
            last_track_dict[new_channel] = ''
            JsonOperations.save_json(last_track_dict, '../data/last_track.json')

    def block_on_change_channel(self):
        """ czyści liste utworów w layoucie i blokuje pobieranie przy zmianie kanału w opcjach """
        self.layout_manager.inst_main_chill_layout.clear_scroll()
        self.layout_manager.inst_main_chill_layout.un_or_block_btn(
            list_btn_to_block=[
                self.layout_manager.inst_main_chill_layout.new_download_btn,
                self.layout_manager.inst_main_chill_layout.select_songs_btn
            ], block=True
        )

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
