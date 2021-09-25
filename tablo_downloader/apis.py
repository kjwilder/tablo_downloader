import requests
import urllib

TABLO_SERVERS_URL = 'https://api.tablotv.com/assocserver/getipinfo/'
TABLO_INFO_PORT = 8885

CHANNELS_URL = 'http://{ip}:%s/guide/channels' % TABLO_INFO_PORT
CHANNEL_DETAILS_URL = 'http://{ip}:%s{channel_id}' % TABLO_INFO_PORT

RCRDS_URL = 'http://{ip}:%s/recordings/airings' % TABLO_INFO_PORT
RCRD_DETAILS_URL = 'http://{ip}:%s{recording_id}' % TABLO_INFO_PORT

PLAYLIST_URL = 'http://{ip}:%s{id}/watch' % TABLO_INFO_PORT

SETTINGS_URL = 'http://{ip}:%s/settings/info' % TABLO_INFO_PORT
SRVR_INFORMATION_URL = 'http://{ip}:%s/server/info' % TABLO_INFO_PORT
SRVR_CAPABILITIES_URL = 'http://{ip}:%s/server/capabilities' % TABLO_INFO_PORT


def call_api(url, method="GET", output="json"):
    requestor = getattr(requests, method.lower())

    try:
        req = requestor(url)
    except Exception as e:
        return {
            'error': 'API call [%s] failed' % url,
            'exception': e
        }

    try:
        if output == "json":
            res = req.json()
        elif output == "text":
            res = req.text
        else:
            return {'error': 'call_api unknown output [%s]' % output}
    except Exception:
        return {
            'error': 'call_api API [%s] invalid value [%s]' % (url, req.text)
        }
    return res


def local_server_info():
    """Get server information for local Tablo servers."""
    return call_api(TABLO_SERVERS_URL)


def server_settings(ip):
    """Return the system settings for a Tablo server."""
    url = SETTINGS_URL.format(ip=ip)
    return call_api(url)


def server_information(ip):
    """Return system information about a Tablo server."""
    url = SRVR_INFORMATION_URL.format(ip=ip)
    return call_api(url)


def server_capabilities(ip):
    """Return the capabilities of a Tablo server."""
    url = SRVR_CAPABILITIES_URL.format(ip=ip)
    return call_api(url)


def server_channels(ip):
    """Return the available channels for a Tablo server."""
    url = CHANNELS_URL.format(ip=ip)
    return call_api(url)


def server_recordings(ip):
    """Get a list of recording identifiers for a Tablo server."""
    url = RCRDS_URL.format(ip=ip)
    return call_api(url)


def recording_details(ip, recording_id=None):
    if not recording_id:  # Get an arbitrary recording ID.
        recording_id = server_recordings(ip)[0]
    url = RCRD_DETAILS_URL.format(ip=ip, recording_id=recording_id)
    return call_api(url)


def channel_details(ip, channel_id=None):
    if not channel_id:  # Get an arbitrary channel ID.
        channel_id = server_channels(ip)[0]
    url = CHANNEL_DETAILS_URL.format(ip=ip, channel_id=channel_id)
    return call_api(url)


def playlist_info(ip, id):
    """id can be a recording ID or channel ID"""
    url = PLAYLIST_URL.format(ip=ip, id=id)
    return call_api(url, method="POST")


# TODO: Grab hd version if available?
def playlist_m3u(pl_info=None, full_urls=True):
    if not pl_info:
        pl_info = playlist_info()
    if 'playlist_url' not in pl_info:
        raise Exception(pl_info)
    playlist_url = pl_info['playlist_url']
    playlist_m3u = call_api(playlist_url, output="text")
    if not isinstance(playlist_m3u, str):
        return playlist_m3u

    if full_urls:
        # The m3u contains relative urls, add the host.
        playlist_host = '://'.join(urllib.parse.urlsplit(playlist_url)[:2])
        playlist_m3u = playlist_m3u.replace('/stream',
                                            playlist_host + '/stream')
    return playlist_m3u


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='Call a Tablo API.')

    parser.add_argument(
        '--tablo_ips',
        '--ips',
        '--ip',
        help='One or more IPs of Tablo device(s) separated by semicolons',
    )

    parser.add_argument(
        '--channel_id',
        help='A Tablo channel ID',
    )

    parser.add_argument(
        '--recording_id',
        help='A Tablo recording ID',
    )

    apis = parser.add_subparsers(dest='api')

    api = apis.add_parser(
        'capabilities',
        help=('Get system capabilities for a Tablo server'),
    )
    api.set_defaults(func=server_capabilities)

    api = apis.add_parser(
        'channels',
        help=('Get available channels for a Tablo server'),
    )
    api.set_defaults(func=server_channels)

    api = apis.add_parser(
        'channel_details',
        help=('Get details about a Tablo server channel'),
    )
    api.set_defaults(func=channel_details)

    api = apis.add_parser(
        'servers',
        help=('Get information about Tablo servers on a local network'),
    )
    api.set_defaults(func=local_server_info)

    api = apis.add_parser(
        'settings',
        help=('Get system settings for a Tablo server'),
    )
    api.set_defaults(func=server_settings)

    api = apis.add_parser(
        'information',
        help=('Get system information for a Tablo server'),
    )
    api.set_defaults(func=server_information)

    api = apis.add_parser(
        'recordings',
        help=('Get recording identifiers for a Tablo server'),
    )
    api.set_defaults(func=server_recordings)

    api = apis.add_parser(
        'recording_details',
        help=('Get details about a recording'),
    )
    api.set_defaults(func=recording_details)

    api = apis.add_parser(
        'recording_playlist',
        help=('Get playlist information for a recording'),
    )
    api.set_defaults(func=playlist_info)

    api = apis.add_parser(
        'playlist_m3u',
        help=('Get a playlist m3u string'),
    )
    api.set_defaults(func=playlist_m3u)

    return parser.parse_args()


def main():
    """Only for testing of Tablo APIs."""
    import inspect
    import pprint
    args = parse_args()
    if not args.api:
        print('Missing API. Run with "-h" for details')
        return

    api_func = args.func
    api_args = {x: None for x in inspect.getfullargspec(api_func).args}

    if 'ip' in api_args:
        if args.tablo_ips:
            tablo_ips = args.tablo_ips.split(',')
        else:
            tablo_ips = {x['private_ip'] for x in local_server_info()['cpes']}
        for ip in tablo_ips:
            api_args['ip'] = ip
            print('Tablo device [%s]' % ip)
            pprint.pprint(args.func(**api_args))
            print()
        return

    pprint.pprint(args.func(**api_args))


if __name__ == '__main__':
    main()
