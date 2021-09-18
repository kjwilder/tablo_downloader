#!/usr/bin/env python3

import argparse
import logging
# import subprocess
import sys
# import tempfile


from tablo_downloader import apis

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
# HANDLER = logging.StreamHandler()
HANDLER = logging.StreamHandler(sys.stdout)
HANDLER.setFormatter(logging.Formatter(
  '%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s'))
LOGGER.addHandler(HANDLER)


def local_ips():
  """Get a list of IPs of local Tablo servers."""
  info = apis.local_server_info()
  LOGGER.debug('Local server info [%s]', info)
  ips = [cpe['private_ip'] for cpe in info['cpes']]
  return ips


def recording_metadata(ip, recording):
  """Return metadata for a recording including an m3u download URL."""
  res = {}
  res['category'] = recording.split('/')[2]
  res['details'] = apis.recording_details(recording, ip)
  res['playlist'] = apis.recording_playlist_info(recording, ip)
  res['playlist_m3u'] = ''
  if not res['playlist'].get('error'):  # Recording succeeded.
    res['playlist_m3u'] = apis.playlist_m3u(res['playlist'])
  return res


def title_and_filename(metadata):
  category = metadata['category']
  details = metadata['details']

  show_title = details.get('airing_details', {}).get('show_title', '')
  if not show_title:
    # TODO: Give unique default.
    show_title = 'UNKNOWN'
  year = None
  file = show_title
  title = show_title
  if category == 'movies':
    year = details.get('movie_airing', {}).get('release_year')
    if isinstance(year, int):
      title += f'_({year})'
  elif category == 'series':
    season = details.get('episode', {}).get('season_number', 'XX')
    if isinstance(season, int):
      season = '%02d' % int(season)

    number = details.get('episode', {}).get('number', 'XX')
    if isinstance(number, int):
      number = '%02d' % int(number)

    file += f'_-_S{season}E{number}'

    episode_title = details.get('episode', {}).get('title')
    if episode_title:
      file += f'_-_{episode_title}'
      title += f' - {episode_title}'

    year = details.get('episode', {}).get('orig_air_date', '')[:4]
    if year.isdigit():
      file += f'_({year})'
  else:
    return None, None
  file = ('/Volumes/Files/%s.mp4' % file).replace(' ', '_')
  return title, file


def test_flow(args):
  recordings_by_ip = {}
  for ip in local_ips():
    recordings_by_ip[ip] = {}
    for recording in apis.server_recordings(ip):
      LOGGER.debug('[ip recording] = [%s %s]', ip, recording)
      recordings_by_ip[ip][recording] = recording_metadata(ip, recording)
      curr = recordings_by_ip[ip][recording]
      if not curr['playlist_m3u']:
        LOGGER.info('No playlist for [%s]', recording)
        continue

      title, filename = title_and_filename(curr)
      if not title:
        continue

      m3u_file = open('temp.m3u', 'w')
      m3u_file.write(curr['playlist_m3u'])
      m3u_file.close()

      cmd = ['ffmpeg',
             '-hide_banner', '-loglevel', 'warning',
             '-protocol_whitelist', 'file,http,https,tcp,tls,crypto',
             '-i', 'temp.m3u',
             '-c', 'copy',
             '-metadata', f'title={title}',
             filename]
      LOGGER.debug('Running [%s]', ' '.join(cmd))
      # subprocess.run(cmd, capture_output=True)
      # subprocess.run(cmd)


def parse_args():
  parser = argparse.ArgumentParser(description='Process some integers.')
  parser.add_argument(
    '-v',
    '--verbose',
    action='store_true',
  )
  return parser.parse_args()


def main():
  args = parse_args()
  if args.verbose:
    LOGGER.setLevel(logging.DEBUG)
  test_flow(args)


if __name__ == '__main__':
  main()
