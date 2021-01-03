from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty

from app.modules.json_operations_modul import JsonOperations


class PopupChange(Screen):
    """ popup do zmiany nowego utworu, wyświetla lasttrack i przez text input umożliwia jego zmiane """
    txt_input_change = ObjectProperty(None)
    last_song_txt = ObjectProperty(None)

    def __init__(self, inst_main_chill_layout, **kwargs):
        self.inst_main_chill_layout = inst_main_chill_layout
        super(PopupChange, self).__init__(**kwargs)

    def if_yes(self):
        """ zapisuje input z popupa jako ostatnią ścierzkę """
        x = JsonOperations()
        JsonOperations.save_last_track(x, self.txt_input_change.text)
        self.inst_main_chill_layout.get_last_track()
        self.inst_main_chill_layout.un_or_block_btn(
            list_btn_to_block=[
                self.inst_main_chill_layout.new_download_btn, self.inst_main_chill_layout.select_songs_btn
            ],
            block=True
        )
        self.inst_main_chill_layout.poopup_window.dismiss()

    def if_no(self):
        """ wyłącza okno """
        self.inst_main_chill_layout.poopup_window.dismiss()
