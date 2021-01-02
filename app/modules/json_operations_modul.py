import json


class JsonOperations(object):
    @staticmethod
    def load_json(file_name):
        """ wczytuje słownik """
        scores_file = open(file_name, "r")
        json_scores = scores_file.read()
        dict_last_track = json.loads(json_scores)
        scores_file.close()
        return dict_last_track

    @staticmethod
    def save_json(dict_last_track, file_name):
        """ zapisuje słownik """
        json_scores = json.dumps(dict_last_track)
        scores_file = open(file_name, "w")
        scores_file.write(json_scores)
        scores_file.close()

    def get_last_track(self):
        """ wczytuje ostatnią ścieżkę """
        channel = self.get_config("channel")
        dict_last_track = self.load_json("../data/last_track.json")
        return dict_last_track[channel].strip()

    def save_last_track(self, last_track):
        """ zapisuje ostanią ścieżkę, lasttrack to json """
        dict_last_track = self.load_json('../data/last_track.json')
        channel = self.get_config('channel')
        dict_last_track[channel] = last_track
        self.save_json(dict_last_track, "../data/last_track.json")

    def get_config(self, what):
        conf_dict = self.load_json('../data/config.json')
        return conf_dict[what].strip()

    @staticmethod
    def get_dict_from_json_str(json_str):
        return json.loads(json_str)
