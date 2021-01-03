import threading

from kivy.animation import Animation


class AnimateThread(threading.Thread):
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
