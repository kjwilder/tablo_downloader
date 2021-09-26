PRIVATE_IP = '192.168.1.1'
PUBLIC_IP = '192.168.233.1'
SERVER_ID = 'SID_012345678901'


class MockResponse:
    def __init__(self, json, text):
        self._json = json
        self.text = text

    def json(self):
        return self._json


def local_server_info(url):
    return MockResponse(json={
        'cpes': [{
            'board': 'gii',
            'host': 'gii',
            'http': None,
            'inserted': '2021-01-01 22:17:59.000000+00:00',
            'last_seen': '2021-02-01 12:26:53.000000+00:00',
            'modified': '2021-02-01 12:26:53.000000+00:00',
            'name': 'Tablo',
            'private_ip': PRIVATE_IP,
            'public_ip': PUBLIC_IP,
            'roku': None,
            'server_version': '2.2.22rc0123456',
            'serverid': SERVER_ID,
            'slip': None,
            'ssl': None
        }],
        'success':
        True
    },
                        text='')


def server_settings(url):
    return MockResponse(json={
        'audio': 'ac3',
        'auto_delete_recordings': True,
        'exclude_duplicates': True,
        'extend_live_recordings': True,
        'fast_live_startup': True,
        'led': 'off',
        'livetv_quality': '/settings/recording_qualities/5',
        'recording_quality': '/settings/recording_qualities/5'
    },
                        text='')


def server_information(url):
    return MockResponse(json={
        'availability': 'ready',
        'build_number': 1234567,
        'cache_key': '01234567-89ab-cdef-0123-456789abcdef',
        'local_address': PRIVATE_IP,
        'model': {
            'device': 'gen2',
            'name': 'Tablo DUAL LITE',
            'tuners': 2,
            'type': 'gii',
            'wifi': True
        },
        'name': 'Tablo',
        'product': 'tablo',
        'server_id': SERVER_ID,
        'setup_completed': True,
        'timezone': '',
        'version': '2.2.22'
    },
                        text='')


def server_capabilities(url):
    return MockResponse(json={
        'capabilities': [
            'guide_recording_refs', 'recordings_keep', 'recording_options',
            'xSwup', 'search', 'subscription_services', 'ac3',
            'manual_programs_edit', 'airings_by_day', 'movie_ratings',
            'live_quality', 'genres', 'conflicts', 'cp', 'lc', 'rc', 'rf'
        ]
    },
                        text='')


def server_channels(url):
    return MockResponse(json=[
        '/guide/channels/212345', '/guide/channels/223456',
        '/guide/channels/234567'
    ],
                        text='')


def server_recordings(url):
    return MockResponse(json=[
        '/recordings/series/episodes/567890',
        '/recordings/movies/airings/548091', '/recordings/sports/events/548117'
    ],
                        text='')


def recording_details(url):
    return MockResponse(json={
        'airing_details': {
            'channel': {
                'channel': {
                    'call_sign': 'Channel',
                    'call_sign_src': 'Channel',
                    'major': 10,
                    'minor': 1,
                    'network': 'CHANNEL',
                    'resolution': 'sd'
                },
                'object_id': 234567,
                'path': '/recordings/channels/234567'
            },
            'channel_path': '/recordings/channels/234567',
            'datetime': '2021-01-01T00:00Z',
            'duration': 3600,
            'show_title': 'Show Title'
        },
        'episode': {
            'description': 'Episode Description',
            'number': 10,
            'orig_air_date': '2019-01-01',
            'season_number': 2,
            'title': 'Episode Title',
            'tms_id': 'EP003456789123'
        },
        'object_id': 567890,
        'path': '/recordings/series/episodes/567890',
        'qualifiers': ['cc'],
        'season_path': '/recordings/series/seasons/94567',
        'series_path': '/recordings/series/94566',
        'snapshot_image': {
            'has_title': False,
            'image_id': 567891
        },
        'user_info': {
            'position': 0,
            'protected': False,
            'watched': False
        },
        'video_details': {
            'airing_offsets': {
                'end': 0,
                'source': 'none',
                'start': 0
            },
            'audio': 'ac3',
            'clean': True,
            'cloud': False,
            'duration': 3456,
            'error': None,
            'height': 480,
            'recorded_offsets': {
                'end': 64,
                'start': -15
            },
            'schedule_offsets': {
                'deprecated': True,
                'end': 64,
                'start': -15
            },
            'seek': 15,
            'size': 869912576,
            'state': 'finished',
            'uploading': False,
            'warnings': [],
            'width': 720
        }
    },
                        text='')
