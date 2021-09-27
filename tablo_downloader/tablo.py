#!/usr/bin/env python3

import argparse
import json
import logging
import os
import pprint
import subprocess
import sys
import tempfile

from tablo_downloader import apis

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
HANDLER = logging.StreamHandler()
HANDLER.setFormatter(
    logging.Formatter(
        '%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s'))
LOGGER.addHandler(HANDLER)

SETTINGS_FILE = '.tablodlrc'
DATABASE_FILE = '.tablodldb'


def load_settings():
    """Load settings from JSON file /home_directory/{SETTINGS_FILE}."""
    settings = {}
    sfile = os.path.join(os.path.expanduser("~"), SETTINGS_FILE)
    if os.path.exists(sfile) and os.path.getsize(sfile) > 0:
        LOGGER.debug('Loading settings from [%s]', sfile)
        with open(sfile) as f:
            settings = json.load(f)
    return settings


def load_recordings_db():
    recordings = {}
    rfile = os.path.join(os.path.expanduser("~"), DATABASE_FILE)
    if os.path.exists(rfile) and os.path.getsize(rfile) > 0:
        with open(rfile) as f:
            recordings = json.load(f)
    return recordings


def save_recordings_db(recordings):
    recordings_file = os.path.join(os.path.expanduser("~"), DATABASE_FILE)
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
            if not episode_title:
                title += f' - S{season}E{number}'

        if not episode_title and not season:
            filename += ' %s' % summary['show_time'][:10]

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


def download_recording(args):
    ip = args.tablo_ips.split(',')[0]
    recording_id = args.recording_id

    recordings = load_recordings_db()
    if not recordings:
        LOGGER.error('No recordings database. Run with --updatedb to create.')
        return

    recording = recordings.get(ip, {}).get(recording_id)
    if not recording:
        LOGGER.error(
                'Recording [%s] on device [%s] not found', recording_id, ip)
        return

    playlist = apis.playlist_info(ip, recording_id)
    if playlist.get('error'):
        LOGGER.error('Recording [%s] on device [%s] failed', recording_id, ip)
        return

    title, filename = title_and_filename(recording_summary(recording))
    if not title:
        LOGGER.error('Unable to generate title for recording [%s] on '
                     'device [%s]', ip, recording_id)
        return

    mp4_filename = os.path.join(args.recordings_directory, filename)
    if args.dry_run:
        if os.path.exists(mp4_filename):
            if args.overwrite:
                LOGGER.info('Dry run - Would overwrite existing download [%s]',
                            mp4_filename)
            else:
                LOGGER.info('Dry run - Would skip existing download [%s]',
                            mp4_filename)
        if args.delete_originals_after_downloading:
            LOGGER.info('Dry run - Would delete Tablo recording after '
                        'successful download of [%s]', mp4_filename)
        return

    if os.path.exists(mp4_filename):
        if args.overwrite:
            os.remove(mp4_filename)
        else:
            LOGGER.info('Cannot create destination [%s] exists.',
                        mp4_filename)
            return

    m3u_data = apis.playlist_m3u(playlist)
    if not isinstance(m3u_data, str):  # Some error occurred.
        LOGGER.error(m3u_data)
        return

    m3u_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
    m3u_filename = m3u_file.name
    m3u_file.write(m3u_data)
    m3u_file.close()

    cmd = [
        'ffmpeg', '-hide_banner', '-loglevel', 'warning',
        '-protocol_whitelist', 'file,http,https,tcp,tls,crypto', '-i',
        m3u_filename, '-c', 'copy', '-metadata', f'title={title}',
        mp4_filename
    ]
    LOGGER.debug('Running [%s]', ' '.join(cmd))

    status = subprocess.run(cmd)
    if status.returncode == 0:
        LOGGER.info('Successfully Downloaded [%s]', mp4_filename)
        if args.delete_originals_after_downloading:
            LOGGER.info('Deleting Tablo recording [%s] on device [%s]',
                        recording_id, ip)
            apis.delete_recording(ip, recording_id)
    else:
        LOGGER.info('Failed to download [%s]', mp4_filename)
    os.remove(m3u_filename)


def create_or_update_recordings_database(args):
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
                LOGGER.info('Getting metadata for new recording [%s]', recording)
                recordings_by_ip[ip][recording] = recording_metadata(
                    ip, recording)
    save_recordings_db(recordings_by_ip)


def truncate_string(s, length):
    if len(s) < length:
        return s
    sp = s[:length - 4].rfind(' ')
    return s[:sp] + ' ...'


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
            titletag, filename = title_and_filename(smry)
            print('Filename : %s' % filename)
            print('Title Tag: %s' % titletag)

            if smry['episode_description']:
                print('Desc:      %s' % truncate_string(smry['episode_description'], 70))
            if smry['event_description']:
                print('Desc:      %s' % truncate_string(smry['event_description'], 70))
            print('Path:      %s' % smry['path'])
            print()


def parse_args_and_settings():
    parser = argparse.ArgumentParser(
        description='Manage recordings Tablo devices.')
    parser.add_argument(
        '--log_level',
        default='info',
        help='More verbose logging',
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Equivalent to --log_level=debug',
    )
    parser.add_argument(
        '--local_ips',
        action='store_true',
        help='Display the IPs of Tablo devices on a local network')
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
        '--updatedb',
        action='store_true',
        help='Create/Update Tablo recordings DB.',
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
        '--download_recording',
        '--download',
        action='store_true',
        help='Download a Tablo recording.',
    )
    parser.add_argument(
        '--dry_run',
        action='store_true',
        help='Display what would be done without updating anything.',
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing downloads.',
    )
    parser.add_argument(
        '--delete_originals_after_downloading',
        action='store_true',
        help='Delete Tablo recordings after successfully downloading them',
    )
    args = parser.parse_args()
    args_dict = vars(args)
    settings = load_settings()
    for setting in settings:
        if setting in args_dict:
            args_dict[setting] = settings[setting]
    return args


def main():
    args = parse_args_and_settings()
    if args.dry_run or args.verbose:
        vars(args)['log_level'] = 'debug'
    LOGGER.setLevel(getattr(logging, args.log_level.upper()))
    LOGGER.debug('Log level [%s]', args.log_level)

    if args.local_ips:
        print(','.join(local_ips()))

    if args.updatedb:
        create_or_update_recordings_database(args)

    if args.recording_details:
        pprint.pprint(apis.recording_details(
                recording_id=args.recording_id, ip=args.tablo_ips))

    if args.dump:
        recordings = load_recordings_db()
        dump_recordings(recordings)

    if args.download_recording:
        download_recording(args)
        return


if __name__ == '__main__':
    main()
