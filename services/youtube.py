import datetime
import time

import requests as requests
from services import time_manager
import youtube_dl


class Youtube:

    format_options = {
            'format': 'bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0'
    }

    @staticmethod
    def search_youtube(query, count):
        with youtube_dl.YoutubeDL(Youtube.format_options) as ydl:
            try:
                requests.get(query)
            except Exception as e:
                result = ydl.extract_info(f"ytsearch{count}:{query}", download=False)
                elements = result['entries']
                single_element_url = elements[0]['formats'][0]['url']
            else:
                elements = ydl.extract_info(query, download=False)
                single_element_url = elements['formats'][0]['url']
        return elements, single_element_url

    @staticmethod
    def get_playlist(link, count):
        with youtube_dl.YoutubeDL(Youtube.format_options) as ydl:
            elements = ydl.extract_info(link, download=False)
            elements = elements[:count]

    @staticmethod
    def get_with_names(query, count=10, only_names=False):
        elements, single_element_url = Youtube.search_youtube(query, count=count)
        duration = None
        try:
            names = [elements[i]['title'] for i in range(len(elements))]
            try:
                duration = [time_manager.TimeManager.get_formatted_time(elements[i]['duration']) for i in range(len(elements))]
            except KeyError:
                pass
            elements = [elements[i]['formats'][0]['url'] for i in range(len(elements))]
        except KeyError:
            names = [elements['title']]
            elements = [elements['formats'][0]['url']]
            try:
                duration = [time_manager.TimeManager.get_formatted_time(elements['duration'])]
            except KeyError:
                pass
        return names if only_names else (names, elements, duration)
