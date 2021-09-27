# tablo-downloader
Query one or more Tablo devices to get and manage a list of recordings and
then download the recordings to local MPEG4 files using `ffmpeg`.

### Install
- `git clone https://github.com/kjwilder/tablo_downloader`
- `pip install ./tablo_downloader`

Running the install will create two programs, `tldl` (Tablo downloader) and
`tldlapis` (Tablo downloader APIs).

### Preliminaries.
- You can provide default values for any flags in `~/.tablodlrc`. The format is
  json. If you have a Tablo device whose IP is `192.168.1.25` and you want to
  copy Tablo recordings to /Volume/Recordings, you should create a config
  like the following:
  ```
  {
    "tablo_ips": "192.168.1.25",
    "recordings_directory": "/Volume/Recordings"
  }
  ```
  If you do not specify an IP (or IPs), either via a flag or in your
  `~/.tablodlrc` file, the programs in this package will try to discover the
  IPs of your Tablo device(s) automatically.

### Typical Usage
- `tldl --local_ips` - Print the IPs of any local Tablo devices.
- `tldl --tablo_ips 192.168.1.25 --updatedb` - Create/update a database of
  current tablo recordings. This takes several minutes to run initially
  but afterwards it runs quickly.
- `tldl --tablo_ips 192.168.1.25 --dump` - Print out a readable summary of
  every Tablo recording, including recording IDs.
- `tldl --download_recording --recording_id /recordings/sports/events/464898
  --recordings_directory /some/directory --tablo_ips 192.168.1.25` - Download a
  Tablo recording.

### Notes
- Local discovery may not work if connected to a VPN.

