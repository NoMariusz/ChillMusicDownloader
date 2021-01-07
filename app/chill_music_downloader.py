from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.config import Config

from components.LayoutManager import LayoutManager

# Config.set('kivy', 'log_level', 'info')
Config.set('kivy', 'log_level', 'critical')
Config.set('graphics', 'borderless', 0)
Config.set('graphics', 'width', 1080)
Config.set('graphics', 'height', 720)
# Config.set('graphics', 'window_state', 'minimized')
Config.set('graphics', 'window_state',  "visible")
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.write()
kv_lay = Builder.load_file('../data/chill_layout.kv')

Clock.max_iteration = 5000       # określa maksymalną liczbę zagniżdżonych zegarów

Window.restore()

layout_manager = LayoutManager()


class ChillApp(App):
    def build(self):
        self.icon = '../data/graphics/CMDownloader_logo.png'
        self.title = 'Chill Music Downloader'
        return layout_manager.window_manager


if __name__ == '__main__':
    ChillApp().run()
    print('App started')
