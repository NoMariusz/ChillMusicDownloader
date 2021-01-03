from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.clock import Clock

from app.modules.downloader_modul import DownloaderOperations


class AddressDownloadLayout(Screen):
    """ umożliwia pobranie fimu z yt bezpośrednio po adresie, jeśli adres będzie nipoprawny to wyskoczy błąd """
    address_input = ObjectProperty(None)
    status_text = ObjectProperty(None)
    download_btn = ObjectProperty(None)
    return_btn = ObjectProperty(None)
    dwn_lock = False

    def __init__(self, layout_manager, **kw):
        self.layout_manager = layout_manager
        super().__init__(**kw)

    def go_return(self):
        if not self.dwn_lock:
            self.layout_manager.window_manager.transition.direction = 'right'
            self.layout_manager.window_manager.current = 'menu_lay'

    def download_address(self):
        """ pobiera dany adres """
        if not self.dwn_lock:
            self.edit_lock_dwn(True)
            self.status_text.size_hint = (0.6, 0.2)
            self.make_extend_status()
            Clock.schedule_once(self.download_address1, 0)

    def download_address1(self, _):
        """ pobiera dany adres w przypadku błędu zwraca błęd połączenia """
        DownloaderOperations().ytdl_download(self.address_input.text, name=None, cause_inst=self)

    def end_thread_download(self, *args):
        self.status_text.size_hint = (0, 0)
        self.status_text.text = ""
        self.address_input.text = ""
        self.edit_lock_dwn(False)

    def download_error(self):
        self.status_text.text = 'Error'
        Clock.schedule_once(self.end_thread_download, 1.2)

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
