import vk_api
from vk_api import audio


class VkAudio:
    def __init__(self, login=None, password=None, vk=None):
        self.vk = vk_api.VkApi(login=login, password=password) if (login and password) else vk if vk else None
        self.vk.auth()

    @staticmethod
    def link_parser(link: str):
        link = link.replace(
            'https://vk.com/music/album/' and 'https://vk.com/music/playlist/' and 'https://vk.com/audios', '')
        args = link.split('_')
        for arg in args:
            yield arg

    def get_iter(self, owner_id=None, album_id=None, access_hash=None):
        tracks_per_user_page = 2000
        tracks_per_album_page = 2000

        vk_cl = self.vk

        user_id = vk_cl.method('users.get')[0]['id']

        if owner_id is None:
            owner_id = user_id

        if album_id is not None:
            offset_diff = tracks_per_album_page
        else:
            offset_diff = tracks_per_user_page

        offset = 1
        while True:
            response = vk_cl.http.post(
                'https://m.vk.com/audio',
                data={
                    'act': 'load_section',
                    'owner_id': owner_id,
                    'playlist_id': album_id if album_id else -1,
                    'offset': offset,
                    'type': 'playlist',
                    'access_hash': access_hash,
                    'is_loading_all': 1
                },
                allow_redirects=False
            ).json()

            if not response['data'][0]:
                raise audio.AccessDenied(
                    'You don\'t have permissions to browse {}\'s albums'.format(
                        owner_id
                    )
                )

            ids = audio.scrap_ids(
                response['data'][0]['list']
            )

            tracks = audio.scrap_tracks(
                ids,
                user_id,
                vk_cl.http,
                convert_m3u8_links=True
            )

            if not tracks:
                break

            for i in tracks:
                yield i

            if response['data'][0]['hasMore']:
                offset += offset_diff
            else:
                break

    def get_vk_playlist_with_link(self, link, count=None):
        link_args = list(self.link_parser(link))
        data = self.get_iter(album_id=link_args[1] if len(link_args) > 1 else None,
                             owner_id=link_args[0] if len(link_args) > 0 else None,
                             access_hash=link_args[2] if len(link_args) > 2 else None)

        i = 0
        while True:
            song = next(data, None)
            if song:
                title = f'{song["artist"]} - {song["title"]}'
                url = song['url']
                i += 1
                print(i, count)
                if count and i == int(count):
                    break
                yield title, url

