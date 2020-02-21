import re


def parse_yt_channel_name(text):
    """ za pomocą re sprawdza czy dany adres jest poprawny """
    if re.search("https://www.youtube.com/user/[a-zA-Z]", text) or re.search("https://www.youtube.com/channel/[a-zA-Z]", text):
        return True
    return False
