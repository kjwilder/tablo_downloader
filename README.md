# tablo-downloader
Query one or more Tablo devices to get and manage a list of recordings and
then download the recordings to local MPEG4 files using `ffmpeg`. This
is an actively developed project. Feel free to create issues.

### Install
- `git clone https://github.com/kjwilder/tablo_downloader`
- `pip install ./tablo_downloader`

Running the install will create two programs, `tldl` (Tablo downloader) and
`tldlapis` (Tablo downloader APIs).

### Preliminaries.
- You can provide default values for any flags in `~/.tablodlrc`. The format is
  json. If you have a Tablo device whose IP is `192.168.1.25`, a bare-bones config
  might look like the following:
  ```
  {
    "tablo_ips": "192.168.1.25"
  }
  ```
  If you do not specify an IP (or IPs), either via a flag or in your
  `~/.tablodlrc` file, the programs in this package will try to discover the
  IPs of your Tablo device(s) automatically.

### Usage
- `tldl --createdb` - Create a database of tablo recordings in `~/.tablodldb`.
  This can take several minutes to complete.
- `tldl --updatedb` - Update your database of tablo recordings. This can be
  run anytime and is quick if you have previously created the db.
- `tldl --dump` - Displays a summary of every recording.
- `tldl --recording_details --recording_id /recordings/series/episodes/422108`
  - Displays all the information available about a recording.
- `tldlapis -h` - See a list of all the API calls you can make directly to
  your Tablo devices using this program.  

### Notes
- Local discovery may not work if connected to a VPN.

