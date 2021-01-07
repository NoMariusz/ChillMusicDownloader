from kivy.clock import Clock
from kivy.uix.screenmanager import NoTransition, SlideTransition
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.graphics import *

from components.utils.AnimateThread import AnimateThread


class LoadingLayout(Screen):
    """ Layout pokazujący obraz ładowania, za pomocą show aktywuje się go a hidem chowa, tworzy też element obracania
    dla logo_loading """
    logo_loading = ObjectProperty(None)
    loading_float_lay = ObjectProperty(None)

    def __init__(self, layout_manager, **kwargs):
        super(LoadingLayout, self).__init__(**kwargs)
        self.window_manager = layout_manager.window_manager
        with self.logo_loading.canvas.before:
            PushMatrix()
            self.rotation = Rotate(angle=0, origin=[1, 1])

        with self.logo_loading.canvas.after:
            PopMatrix()
        self.ath = AnimateThread(self)
        self.clock = Clock

    def show(self):
        """ pokazuje swoją klasę i włącza animacje """
        self.clock = Clock.schedule_once(self.animate_logo, 0)
        self.window_manager.transition = NoTransition()
        self.window_manager.current = 'load_lay'

    def animate_logo(self, _):
        """ włącza animacje w osobnym wątku """
        self.ath.start()

    def hide(self, cause_inst_name):
        """ chowa ekran wracjąc do tekgo który zdecydował sięschować, wyłącza animacje i zegary """
        self.clock.cancel()
        self.ath.stop()
        self.ath = AnimateThread(self)
        self.window_manager.current = cause_inst_name
        self.window_manager.transition = SlideTransition()
