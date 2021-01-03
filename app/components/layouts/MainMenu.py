import sys

from kivy.uix.screenmanager import Screen


class MainMenu(Screen):

    def __init__(self, layout_manager, **kw):
        self.layout_manager = layout_manager
        super().__init__(**kw)

    def go_to_chanel_dwn(self):
        self.layout_manager.window_manager.transition.direction = 'right'
        self.layout_manager.window_manager.current = 'main_lay'

    def go_to_address_dwn(self):
        self.layout_manager.window_manager.transition.direction = 'left'
        self.layout_manager.window_manager.current = 'address_dwn_lay'

    def go_to_name_dwn(self):
        self.layout_manager.window_manager.transition.direction = 'down'
        self.layout_manager.window_manager.current = 'name_dwn_lay'

    def go_to_options(self):
        self.layout_manager.window_manager.transition.direction = 'up'
        self.layout_manager.window_manager.current = 'options_lay'
        self.layout_manager.inst_options.make_options()

    @staticmethod
    def exit_app():
        sys.exit()
