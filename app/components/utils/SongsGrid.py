from kivy.clock import Clock

from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button


class SongsGrid(GridLayout):
    """ Grid layout gdzie ładujemy utwory, aby je pokazać użytkownikowi, przed załadowaniem jest pusty, ta klasa jest
    dzieckiem inst_scroll_viev, posiada liste z url zaznaczonych"""

    def __init__(self, inst_main_chill_layout, **kwargs):
        super(SongsGrid, self).__init__(**kwargs)
        self.inst_main_chill_layout = inst_main_chill_layout
        self.url_chose_dict = {}       # domyślny słownik gdzie będą zapisywane url zaznaczonych utworów

    def load_dict_to_grid(self, songs_dict):
        """ wpisuje do grodlayout 1 kolumnową liste utworów """
        self.cols = 1
        self.size_hint = (1, 1 + (len(songs_dict) / 10))
        self.songs_dict = songs_dict
        Clock.schedule_once(self.load_dict_to_grid2, 0)

    def load_dict_to_grid2(self, _):
        for key in self.songs_dict:
            wid = Label(
                text=key, color=(1, 1, 1, 1), font_name='Arial', font_size=int(self.inst_main_chill_layout.width / 40)
            )
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
            wid = Label(
                text=key, size_hint_x=0.9, color=(1, 1, 1, 1), font_name='Arial',
                font_size=int(self.inst_main_chill_layout.width / 55)
            )
            if key == "↑ New, ↓ Old" or key == 'Error' or \
                    key == 'Your daily limit expires' or key == 'Invalid channel name':
                but = Label(size_hint_x=0.1)
                wid.color = (0.8980392156862745, 0.6274509803921569, 0.8588235294117647, 1)
            else:
                but = Button(
                    size_hint_x=0.1, background_normal=key, background_down=songs_dict[key],
                    background_color=(0.8980392156862745, 0.6274509803921569, 0.8588235294117647, 1)
                )
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
        (0.8980392156862745, 0.6274509803921569, 0.8588235294117647, 1) - niezaznaczony,
        [0.453125, 0.26953125, 0.67578125, 1] - zaznaczony
         """
        if instance.background_color == [0.8980392156862745, 0.6274509803921569, 0.8588235294117647, 1]:
            self.url_chose_dict[instance.background_normal] = instance.background_down
            instance.background_color = [0.453125, 0.26953125, 0.67578125, 1]
        elif instance.background_color == [0.453125, 0.26953125, 0.67578125, 1]:
            self.url_chose_dict.pop(instance.background_normal)
            instance.background_color = [0.8980392156862745, 0.6274509803921569, 0.8588235294117647, 1]
