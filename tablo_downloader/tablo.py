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
    """Load settings from JSON file /home_directory/{TABLO_SETTINGS_FILE}."""
    settings = {}
    sfile = os.path.join(os.path.expanduser("~"), TABLO_SETTINGS_FILE)
    if os.path.exists(sfile) and os.path.getsize(sfile) > 0:
        LOGGER.debug('Loading settings from [%s]', sfile)
        with open(sfile) as f:
            settings = json.load(f)
    return settings


def load_recordings_db():
    recordings = {}
    rfile = os.path.join(os.path.expanduser("~"), TABLO_DATABASE_FILE)
    if os.path.exists(rfile) and os.path.getsize(rfile) > 0:
        with open(rfile) as f:
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


def recording_summary(metadata):
    dtls = metadata['details']
    res = {
        'category': metadata['category'],
        'episode_date': None,
        'episode_description': None,
        'episode_number': None,
        'episode_season': None,
        'episode_title': None,
        'event_description': None,
        'event_season': None,
        'event_title': None,
        'movie_year': None,
        'path': dtls.get('path'),
        'show_time': dtls.get('airing_details', {}).get('datetime'),
        'show_title': dtls.get('airing_details', {}).get('show_title'),
    }
    if metadata['category'] == 'movies':
        res['movie_year'] = dtls.get('movie_airing', {}).get('release_year')
    elif metadata['category'] == 'series':
        res['episode_title'] = dtls.get('episode', {}).get('title')
        res['episode_date'] = dtls.get('episode', {}).get('orig_air_date')
        res['episode_description'] = dtls.get('episode', {}).get('description')
        res['episode_season'] = dtls.get('episode', {}).get('season_number')
        res['episode_number'] = dtls.get('episode', {}).get('number')
    elif metadata['category'] == 'sports':
        res['event_title'] = dtls.get('event', {}).get('title')
        res['event_description'] = dtls.get('event', {}).get('description')
        res['event_season'] = dtls.get('event', {}).get('season')
    return res


def title_and_filename(summary):
    show_title = summary['show_title']
    if not show_title:
        show_title = 'UNKNOWN'  # TODO: Give better default?
    filename, title = show_title, show_title
    if summary['category'] == 'movies':
        year = summary['movie_year']
        if isinstance(year, int):
            filename += f' ({year})'
    elif summary['category'] == 'series':
        episode_title = summary['episode_title']
        if episode_title:
            filename += f'_-_{episode_title}'
            title += f' - {episode_title}'

        season = summary['episode_season']
        if isinstance(season, int) and season > 0:
            season = '%02d' % int(season)
        number = summary['episode_number']
        if isinstance(number, int) and number > 0:
            number = '%02d' % int(number)
            if not season:
                season = '00'
        if season:
            filename += f'_-_S{season}E{number}'
            title += f' - S{season}E{number}'
    elif summary['category'] == 'sports':
        event_title = summary['event_title']
        if event_title:
            filename += f'_-_{event_title}'
            title += f' - {event_title}'
        show_time = summary['show_time']
        if show_time:
            filename += f'_-_{show_time[:10]}'
            title += f' - {show_time[:10]}'
    else:
        return None, None
    filename = ('%s.mp4' % filename).replace(' ', '_')
    return title, filename


def test_flow(args):
    recordings = load_recordings_db()
    if not recordings:
        LOGGER.error('No recordings database.')
        return

    for ip in recordings:
        for recording in recordings[ip]:
            LOGGER.debug('[ip recording] = [%s %s]', ip, recording)
            curr = recordings[ip][recording]
            if curr['playlist'].get('error'):  # Recording failed.
                continue

            playlist_m3u = apis.playlist_m3u(curr['playlist'])

            title, filename = title_and_filename(recording_summary(curr))
            if not title:
                continue

            filename = os.path.join(args.recordings_directory, filename)
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
            LOGGER.debug('Removing deleted recording [%s %s]', ip, recording)
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


def dump_recordings(recordings):
    summaries = {ip: {} for ip in recordings}
    for ip, recs in recordings.items():
        summaries[ip] = {r: recording_summary(recs[r]) for r in recs}
    for ip in sorted(summaries):
        for smry in sorted(summaries[ip].values(),
                           key=lambda k: (k['show_title'],
                                          k['episode_season'],
                                          k['episode_number'],
                                          k['show_time'])):
            title = smry['show_title']
            if not title:
                title = 'UNKNOWN'
            if smry['episode_season'] or smry['episode_number']:
                title += ' ['
                if smry['episode_season']:
                    title += 'Season: %s' % smry['episode_season']
                if smry['episode_number']:
                    title += ' Number: %s' % smry['episode_number']
                title += ']'
            print('Title:   %s' % title)

            if smry['movie_year']:
                print('Year:    %s' % smry['movie_year'])
            if smry['episode_title']:
                print('Episode: %s' % smry['episode_title'])
            if smry['episode_description']:
                print('Desc:    %s' % smry['episode_description'][:70])
            if smry['episode_date']:
                print('Airing:  %s' % smry['episode_date'])
            if smry['event_title']:
                print('Event:   %s' % smry['episode_title'])
            if smry['event_description']:
                print('Desc:    %s' % smry['event_description'][:70])
            if smry['event_season']:
                print('Season:  %s' % smry['event_season'])
            print('Path:    %s' % smry['path'])
            titletag, filename = title_and_filename(smry)
            print('Title Tag: %s' % titletag)
            print('Filename : %s' % filename)
            print('\n')


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
        '--recordings_directory',
        help='A directory to store Tablo recordings',
    )
    parser.add_argument(
        '--delete_originals_after_downloading',
        action='store_true',
        help='Delete Tablo recordings after downloading them',
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
        pprint.pprint(apis.recording_details(recording_id=args.recording_id, ip=args.tablo_ips))

    if args.dump:
        recordings = load_recordings_db()
        dump_recordings(recordings)

    if args.test_flow:
        test_flow(args)
        return


if __name__ == '__main__':
    main()
