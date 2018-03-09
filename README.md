# music-scan
Scan music collection for comparison to online databases

## Requirements

### Python
Developed with Python 3.6.4

### Python third-party modules
Install the following modules with pip:
* mutagen
* python-dateutil
* whatapi
* colorama
```
pip install -r requirements.txt
```

## Help
```
usage: musicscan-cli [-h] [-l LOGLEVEL] [-o PATH] [-r] [-s URL] [-t PCT]
                     [-c FILE] [-p PASSWORD] [-u USERNAME]
                     inputpath

Scan directories for music folders and compare to WhatAPI

positional arguments:
  inputpath                path to scan

optional arguments:
  -h, --help               show this help message and exit
  -l, --loglevel LOGLEVEL  loglevel for log file (default: info)
  -o, --output PATH        output path for .torrent files (default: .)
  -r, --reset              scan all rather than skipping previously scanned
  -s, --server URL         server URL (default: https://redacted.ch)
  -t, --threshold PCT      matching local music threshold (default: 80)

config file:
  -c, --config FILE        config file with login details (default: server.conf)

login details:
  -p, --password PASSWORD  your password
  -u, --username USERNAME  your username
```

## Log
Currently logs to `musicscan.log`
