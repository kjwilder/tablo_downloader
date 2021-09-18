import requests
import urllib

TABLO_SERVERS_URL = 'https://api.tablotv.com/assocserver/getipinfo/'
TABLO_INFO_PORT = 8885

CHANNELS_URL = 'http://{ip}:{port}/guide/channels'
CHANNEL_DETAILS_URL = 'http://{ip}:{port}{channel_id}'

PLAYLIST_URL = 'http://{ip}:{port}{id}/watch'

RECORDINGS_URL = 'http://{ip}:{port}/recordings/airings'
RECORDING_DETAILS_URL = 'http://{ip}:{port}{recording_id}'

SETTINGS_URL = 'http://{ip}:{port}/settings/info'
SERVER_INFORMATION_URL = 'http://{ip}:{port}/server/info'
SERVER_CAPABILITIES_URL = 'http://{ip}:{port}/server/capabilities'


def call_api(url, method="GET", output="json"):
  try:
    if method == "GET":
      req = requests.get(url)
    elif method == "POST":
      req = requests.post(url)
    else:
      return {'error': 'call_api unknown method [%s]' % method}
  except Exception:
    return {'error': 'call_api API [%s] call failed' % url}

  try:
    if output == "json":
      res = req.json()
    elif output == "text":
      res = req.text
    else:
      return {'error': 'call_api unknown output [%s]' % output}
  except Exception:
    return {'error':
            'call_api API [%s] invalid value [%s]' % (url, req.text)}
  return res


def local_server_info():
  """Get server information for local Tablo servers."""
  return call_api(TABLO_SERVERS_URL)


def server_settings(ip=None, port=TABLO_INFO_PORT):
  """Return the system settings for a Tablo server."""
  if not ip:  # Get IP of first local server.
    ip = local_server_info()['cpes'][0]['private_ip']
  url = SETTINGS_URL.format(ip=ip, port=port)
  return call_api(url)


def server_information(ip=None, port=TABLO_INFO_PORT):
  """Return system information about a Tablo server."""
  if not ip:  # Get IP of first local server.
    ip = local_server_info()['cpes'][0]['private_ip']
  url = SERVER_INFORMATION_URL.format(ip=ip, port=port)
  return call_api(url)


def server_capabilities(ip=None, port=TABLO_INFO_PORT):
  """Return the capabilities of a Tablo server."""
  if not ip:  # Get IP of first local server.
    ip = local_server_info()['cpes'][0]['private_ip']
  url = SERVER_CAPABILITIES_URL.format(ip=ip, port=port)
  return call_api(url)


def server_channels(ip=None, port=TABLO_INFO_PORT):
  """Return the available channels for a Tablo server."""
  if not ip:  # Get IP of first local server.
    ip = local_server_info()['cpes'][0]['private_ip']
  url = CHANNELS_URL.format(ip=ip, port=port)
  return call_api(url)


def server_recordings(ip=None, port=TABLO_INFO_PORT):
  """Get a list of recording identifiers for a Tablo server."""
  if not ip:  # Get IP of first local server.
    ip = local_server_info()['cpes'][0]['private_ip']
  url = RECORDINGS_URL.format(ip=ip, port=port)
  return call_api(url)


def recording_details(recording_id=None, ip=None, port=TABLO_INFO_PORT):
  if not ip:  # Get IP of first local server.
    ip = local_server_info()['cpes'][0]['private_ip']
  if not recording_id:  # Get an arbitrary recording ID.
    recording_id = server_recordings(ip)[0]
  url = RECORDING_DETAILS_URL.format(
    ip=ip, port=port, recording_id=recording_id)
  return call_api(url)


def channel_details(channel_id=None, ip=None, port=TABLO_INFO_PORT):
  if not ip:  # Get IP of first local server.
    ip = local_server_info()['cpes'][0]['private_ip']
  if not channel_id:  # Get an arbitrary channel ID.
    channel_id = server_channels(ip)[0]
  url = CHANNEL_DETAILS_URL.format(
    ip=ip, port=port, channel_id=channel_id)
  return call_api(url)


def playlist_info(id, ip, port):
  """This is a stub used by specific playlist calls."""
  url = PLAYLIST_URL.format(ip=ip, port=port, id=id)
  return call_api(url, method="POST")


def recording_playlist_info(recording_id=None, ip=None, port=TABLO_INFO_PORT):
  if not ip:  # Get IP of first local server.
    ip = local_server_info()['cpes'][0]['private_ip']
  if not recording_id:  # Get an arbitrary recording ID.
    recording_id = server_recordings(ip)[0]
  return playlist_info(recording_id, ip, port)


# TODO: Grab hd version if available?
def playlist_m3u(playlist_info=None, full_urls=True):
  if not playlist_info:
    playlist_info = recording_playlist_info()
  if 'playlist_url' not in playlist_info:
    raise Exception(playlist_info)
  playlist_url = playlist_info['playlist_url']
  playlist_m3u = call_api(playlist_url, output="text")
  if full_urls:
    # The m3u contains relative urls, add the host.
    playlist_host = '://'.join(urllib.parse.urlsplit(playlist_url)[:2])
    playlist_m3u = playlist_m3u.replace(
      '/stream', playlist_host + '/stream')
  return playlist_m3u



def parse_args():
  import argparse
  parser = argparse.ArgumentParser(description='Call a Tablo API.')

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
  api.set_defaults(func=recording_playlist_info)

  api = apis.add_parser(
    'playlist_m3u',
    help=('Get a playlist m3u string'),
  )
  api.set_defaults(func=playlist_m3u)

  return parser.parse_args()


def main():
  import pprint
  args = parse_args()
  if not args.api:
    print('Missing API. Run with "-h" for details')
    return
  pprint.pprint(args.func())


if __name__ == '__main__':
  main(parse_args())
