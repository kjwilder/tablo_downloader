#!/usr/bin/env python3

import argparse
import json
import logging
import os
import pprint
# import subprocess
import sys
# import tempfile

from tablo_downloader import apis

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
HANDLER = logging.StreamHandler()
# HANDLER = logging.StreamHandler(sys.stdout)
HANDLER.setFormatter(
    logging.Formatter(
        '%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s'))
LOGGER.addHandler(HANDLER)

TABLO_SETTINGS_FILE = '.tablodlrc'
TABLO_DATABASE_FILE = '.tablodldb'


def load_settings():
    settings = {}
    settings_file = os.path.join(os.path.expanduser("~"), TABLO_SETTINGS_FILE)
    if os.path.exists(settings_file):
        LOGGER.debug('Loading settings from [%s]', settings_file)
        with open(settings_file) as f:
            settings = json.load(f)
    return settings


def load_recordings_db():
    recordings = {}
    recordings_file = os.path.join(os.path.expanduser("~"), TABLO_DATABASE_FILE)
    if os.path.exists(recordings_file):
        with open(recordings_file) as f:
            recordings = json.load(f)
    return recordings


def save_recordings_db(recordings):
    recordings_file = os.path.join(os.path.expanduser("~"), TABLO_DATABASE_FILE)
    with open(recordings_file, 'w') as f:
        f.write(json.dumps(recordings))


def local_ips():
    """Get a list of IPs of local Tablo servers."""
    info = apis.local_server_info()
    LOGGER.debug('Local server info [%s]', info)
    ips = {cpe['private_ip'] for cpe in info['cpes']}
    return ips


def recording_metadata(ip, recording):
    """Return metadata for a recording."""
    res = {}
    res['category'] = recording.split('/')[2]
    res['details'] = apis.recording_details(ip, recording)
    res['playlist'] = apis.playlist_info(ip, recording)
    return res


def title_and_filename(metadata):
    category = metadata['category']
    details = metadata['details']

    show_title = details.get('airing_details', {}).get('show_title', '')
    if not show_title:
        # TODO: Give unique default.
        show_title = 'UNKNOWN'
    year = None
    filename = show_title
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

        filename += f'_-_S{season}E{number}'

        episode_title = details.get('episode', {}).get('title')
        if episode_title:
            filename += f'_-_{episode_title}'
            title += f' - {episode_title}'

        year = details.get('episode', {}).get('orig_air_date', '')[:4]
        if year.isdigit():
            filename += f'_({year})'
    else:
        return None, None
    filename = ('/Volumes/Files/%s.mp4' % filename).replace(' ', '_')
    return title, filename


def test_flow(args):
    if args.tablo_ip:
        tablo_ips = {x for x in args.tablo_ip.split(',') if x}
    else:
        tablo_ips = local_ips()
    for ip in tablo_ips:
        for recording in apis.server_recordings(ip):
            LOGGER.debug('[ip recording] = [%s %s]', ip, recording)
            curr = recording_metadata(ip, recording)
            if curr['playlist'].get('error'):  # Recording failed.
                LOGGER.info('No playlist for [%s]', recording)
                continue

            playlist_m3u = apis.playlist_m3u(curr['playlist'])

            title, filename = title_and_filename(curr)
            if not title:
                continue

            m3u_file = open('temp.m3u', 'w')
            m3u_file.write(playlist_m3u)
            m3u_file.close()

            cmd = [
                'ffmpeg', '-hide_banner', '-loglevel', 'warning',
                '-protocol_whitelist', 'file,http,https,tcp,tls,crypto', '-i',
                'temp.m3u', '-c', 'copy', '-metadata', f'title={title}',
                filename
            ]
            LOGGER.debug('Running [%s]', ' '.join(cmd))
            # subprocess.run(cmd)
            break


def create_or_update_recordings_database(args):
    recordings_by_ip = {}
    if args.updatedb:
        recordings_by_ip = load_recordings_db()

    tablo_ips = {ip for ip in recordings_by_ip}
    if args.tablo_ips:
        tablo_ips |= {x for x in args.tablo_ips.split(',') if x}
    elif tablo_ips:
        tablo_ips |= local_ips()
    LOGGER.info('Creating/Updating recording database for Tablo IPs [%s]',
                ' '.join(tablo_ips))

    for ip in tablo_ips:
        LOGGER.info('Getting recordings for IP [%s]', ip)
        if ip not in recordings_by_ip:
            recordings_by_ip[ip] = {}
        server_recordings = apis.server_recordings(ip)
        # Remove any items no longer present on the Tablo device.
        obsolete_db_recordings = {
                r for r in recordings_by_ip[ip] if r not in server_recordings}
        for recording in obsolete_db_recordings:
            LOGGER.debug('Removing recording [%s %s]', ip, recording)
            del recordings_by_ip[ip][recording]
        # Add new recordings.
        for recording in server_recordings:
            if recording not in recordings_by_ip[ip]:
                LOGGER.info('Getting metadata for recording [%s]', recording)
                recordings_by_ip[ip][recording] = recording_metadata(
                    ip, recording)
            else:
                LOGGER.debug('Skipping known recording [%s %s]', ip, recording)
    save_recordings_db(recordings_by_ip)


def recording_details(metadata):
    dtls = metadata['details']
    res = {}
    res['show_title'] = dtls.get('airing_details',
                                 {}).get('show_title', 'UNKNOWN')

    res['year'] = dtls.get('movie_airing', {}).get('release_year')

    res['episode_title'] = dtls.get('episode', {}).get('title')
    res['episode_date'] = dtls.get('episode', {}).get('orig_air_date')
    res['episode_description'] = dtls.get('episode', {}).get('description')
    res['episode_season'] = dtls.get('episode', {}).get('season_number')
    res['episode_number'] = dtls.get('episode', {}).get('number')

    res['event_title'] = dtls.get('event', {}).get('title')
    res['event_description'] = dtls.get('event', {}).get('description')
    res['event_season'] = dtls.get('event', {}).get('season')

    res['path'] = dtls.get('path')
    return res


def dump_recordings(recordings):
    details = {}
    for ip in recordings:
        if ip not in details:
            details[ip] = {}
        for recording in recordings[ip]:
            details[ip][recording] = recording_details(
                recordings[ip][recording])
    for ip in sorted(details):
        for dtls in sorted(details[ip].values(), key=lambda k: k['show_title']):
            # dtls = details[ip][recording]
            print('Title:   %s' % dtls.get('show_title', 'UNKNOWN'))
            if dtls['year']:
                print('Year:    %s' % dtls['year'])
            if dtls['episode_title']:
                print('Episode: %s' % dtls['episode_title'])
            if dtls['episode_description']:
                print('Desc:    %s' % dtls['episode_description'])
            if dtls['episode_date']:
                print('Airing:  %s' % dtls['episode_date'])
            if dtls['episode_season']:
                print('Season:  %s' % dtls['episode_season'])
            if dtls['episode_number']:
                print('Number:  %s' % dtls['episode_number'])
            if dtls['event_title']:
                print('Event:   %s' % dtls['episode_title'])
            if dtls['event_description']:
                print('Desc:    %s' % dtls['event_description'])
            if dtls['event_season']:
                print('Season:  %s' % dtls['event_season'])
            print('Path:    %s\n' % dtls['path'])
            # :w 'category': 'sports', 'details': {'object_id': 60505, 'path': '/recordings/sports/events/60505', 'sport_path': '/recordings/sports/17652', 'snapshot_image': {'image_id': 63247, 'has_title': False}, 'airing_details': {'datetime': '2020-12-07T01:20Z', 'duration': 11400, 'channel_path': '/recordings/channels/60506', 'channel': {'object_id': 60506, 'path': '/recordings/channels/60506', 'channel': {'call_sign': 'WKYC-HD', 'call_sign_src': 'WKYC-HD', 'major': 3, 'minor': 1, 'network': 'NBC', 'resolution': 'hd_1080'}}, 'show_title': 'NFL Football'}, 'video_details': {'state': 'finished', 'clean': True, 'cloud': False, 'uploading': False, 'audio': 'aac', 'size': 9388068864, 'duration': 17115, 'width': 1280, 'height': 720, 'schedule_offsets': {'start': -15, 'end': 5704, 'deprecated': True}, 'recorded_offsets': {'start': -15, 'end': 5704}, 'airing_offsets': {'start': 0, 'end': 0, 'source': 'none'}, 'seek': 15, 'error': None, 'warnings': []}, 'user_info': {'position': 1882, 'watched': False, 'protected': False}, 'event': {'title': 'Denver Broncos at Kansas City Chiefs', 'description': 'The Chiefs (10-1) try for their 11th straight victory over the Broncos (4-7). Kansas City continued to roll against AFC West rival Denver with a 43-16 Week 7 victory. The Chiefs have won six in a row after holding off the Buccaneers 27-24 last week.', 'season': '2020-2021', 'season_type': 'regular', 'venue': None, 'teams': [{'name': 'Denver Broncos', 'team_id': 40}, {'name': 'Kansas City Chiefs', 'team_id': 46}], 'home_team_id': 46, 'tms_id': 'EP000031282618'}, 'qualifiers': ['cc']}, 'playlist': {'token': '9201e306-a673-43fd-a13d-a2a7145566e3', 'expires': '2021-09-19T06:28:26Z', 'playlist_url': 'http://192.168.10.49:80/stream/pl.m3u8?Ser1_cMhzMf6zBHpB2-l6A', 'bif_url_sd': 'http://192.168.10.49:80/stream/bif?Ser1_cMhzMf6zBHpB2-l6A', 'bif_url_hd': 'http://192.168.10.49:80/stream/bif?Ser1_cMhzMf6zBHpB2-l6A&hd', 'video_details': {'width': 0, 'height': 0}}}


def parse_args_and_settings():
    parser = argparse.ArgumentParser(
        description='Manage recordings Tablo devices.')
    parser.add_argument(
        '--log_level',
        default='info',
        help='More verbose logging',
    )
    parser.add_argument(
        '--tablo_ips',
        '--ips',
        '--ip',
        help='One or more IPs of Tablo device(s) separated by commas',
    )
    parser.add_argument(
        '--recording_id',
        help='A Tablo recording ID',
    )
    parser.add_argument(
        '--updatedb',
        action='store_true',
        help='Update Tablo recordings DB. This may take a while.',
    )
    parser.add_argument(
        '--createdb',
        action='store_true',
        help='Create/update Tablo recordings DB. This may take a while.',
    )
    parser.add_argument(
        '--dump',
        action='store_true',
        help='Dump Tablo recordings DB.',
    )
    parser.add_argument(
        '--recording_details',
        action='store_true',
        help='Display details of a Tablo recording.',
    )
    parser.add_argument(
        '--test_flow',
        action='store_true',
        help='Try downloading from a Tablo server',
    )
    args = parser.parse_args()
    args_dict = vars(args)
    settings = load_settings()
    for setting in settings:
        if setting in args_dict and args_dict[setting] is None:
            args_dict[setting] = settings[setting]
    return args


def main():
    args = parse_args_and_settings()
    LOGGER.setLevel(getattr(logging, args.log_level.upper()))
    LOGGER.debug('Log level [%s]', args.log_level.upper())

    if args.createdb or args.updatedb:
        create_or_update_recordings_database(args)

    if args.recording_details:
        pprint.pprint(apis.recording_details(args.recording_id, args.tablo_ips))

    if args.dump:
        recordings = load_recordings_db()
        dump_recordings(recordings)

    if args.test_flow:
        test_flow(args)
        return


if __name__ == '__main__':
    main()
