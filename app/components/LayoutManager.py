from kivy.uix.screenmanager import ScreenManager

from components.layouts.MainChillLayout import MainChillLayout
from components.layouts.MainMenu import MainMenu
from components.layouts.OptionsLay import OptionsLay
from components.layouts.AddressDownloadLayout import AddressDownloadLayout
from components.layouts.NameResultLayout import NameResultLayout
from components.layouts.NameDownloadLayout import NameDownloadLayout
from components.layouts.LoadingLayout import LoadingLayout


class LayoutManager:
    def __init__(self):
        self.window_manager = ScreenManager()

        self.inst_main_menu = MainMenu(self, name='menu_lay')
        self.inst_options = OptionsLay(self, name='options_lay')
        self.inst_main_chill_layout = MainChillLayout(self, name='main_lay')
        self.inst_address_download_layout = AddressDownloadLayout(self, name='address_dwn_lay')
        self.inst_name_download_layout = NameDownloadLayout(self, name='name_dwn_lay')
        self.inst_name_result_layout = NameResultLayout(self, name='name_result_lay')
        self.inst_loading_layout = LoadingLayout(self, name='load_lay')
        self.add_widgets()

    def add_widgets(self):
        self.window_manager.add_widget(self.inst_main_menu)
        self.window_manager.add_widget(self.inst_options)
        self.window_manager.add_widget(self.inst_main_chill_layout)
        self.window_manager.add_widget(self.inst_address_download_layout)
        self.window_manager.add_widget(self.inst_name_download_layout)
        self.window_manager.add_widget(self.inst_name_result_layout)
        self.window_manager.add_widget(self.inst_loading_layout)
