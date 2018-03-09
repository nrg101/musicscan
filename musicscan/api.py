# imports: standard
import logging
import os
import json
from configparser import ConfigParser

# imports: third party
import whatapi

# imports: custom
import musicscan.cookies


class WhatAPIExtended(whatapi.WhatAPI):
    # constructor
    def __init__(self, config_file=None, username=None, password=None, cookies=None, server=None):
        super().__init__(config_file, username, password, cookies, server)
        # save cookies
        musicscan.cookies.save_cookies(self.session.cookies)
        # reset counters
        self.torrent_files_written = 0
    
    # get results from search
    def _get_results(self, search):
        # initialise results
        results = []
        logging.info("Getting results from search")
        # log search status
        search_status = search.get('status', None)
        if search_status == 'success':
            logging.debug("API search status: success")
            logging.debug("search: %s", search)
            results = search["response"]["results"]
        else:
            logging.warning("Search status: %s", search_status)
        # log results count
        logging.info("Search results: %s", len(results))
        return results

    # get torrent object by id
    def get_torrent_object(self, torrent_id):
        torrent_object = {}
        logging.info("Getting torrent by id: %s", torrent_id)
        torrent_lookup = self.request(
                'torrent',
                id=torrent_id
        )
        torrent_lookup_status = torrent_lookup.get('status', None)
        if torrent_lookup_status == "success":
            logging.info("Torrent lookup successful")
            torrent_object = torrent_lookup["response"]["torrent"]
        else:
            logging.error("Torrent lookup failed. status = %s", torrent_lookup_status)
        # return torrent object
        return torrent_object

    # search from release
    def search_from_release(self, release):
        logging.info("***** BEGIN search_from_release *****")
        logging.info("release: %s", release)
        # initialise results
        results = []
        # whatapi search
        # try searching for artist, album and year
        if release["tags"]["album"] != None:
            logging.info(
                    "Searching by Artist '%s'. Album name '%s'. Year = %s. Format = %s",
                    release["tags"]["artist"],
                    release["tags"]["album"],
                    release["tags"]["year"],
                    release["tags"]["audio_format"]
            )
            search = self.request(
                    'browse',
                    artistname=release["tags"]["artist"],
                    groupname=release["tags"]["album"],
                    year=release["tags"]["year"],
                    format=release["tags"]["audio_format"]
            )
            results = self._get_results(search)
        # if no results yet, search by album name (and year and format if present)
        logging.debug('release["tags"]["album"]: %s', release["tags"]["album"])
        if release["tags"]["album"] != None:
            logging.info(
                    "Searching by album name '%s'. Year = %s. Format = %s",
                    release["tags"]["album"],
                    release["tags"]["year"],
                    release["tags"]["audio_format"]
            )
            search = self.request(
                    'browse',
                    groupname=release["tags"]["album"],
                    year=release["tags"]["year"],
                    format=release["tags"]["audio_format"]
            )
            results = self._get_results(search)
        # if no results yet, search by artist and year (and format if present)
        if len(results) == 0:
            if release["tags"]["artist"] != None and release["tags"]["year"] != None:
                logging.info(
                        "Searching by artist '%s' and year '%s'. Format = %s",
                        release["tags"]["artist"],
                        release["tags"]["year"],
                        release["tags"]["audio_format"]
                )
                search = self.request(
                        'browse',
                        artistname=release["tags"]["artist"],
                        year=release["tags"]["year"],
                        format=release["tags"]["audio_format"]
                )
                results = self._get_results(search)
        # if no results yet, search by the folder name (simplified) (and year and format if present)
        if len(results) == 0:
            logging.info(
                    "Searching by folder name (simplified) '%s'. Year = %s. Format = %s",
                    release["dirpath_simplified"],
                    release["tags"]["year"],
                    release["tags"]["audio_format"]
            )
            search = self.request(
                    'browse',
                    searchstr=release["dirpath_simplified"],
                    year=release["tags"]["year"],
                    format=release["tags"]["audio_format"]
            )
            results = self._get_results(search)
        # return search
        logging.debug("Search results:\n%s", json.dumps(results, indent=4))
        return results
    
    # set torrent file save path
    def set_torrent_file_save_path(self, path):
        self.torrent_file_save_path = path
    
    # save torrent to file
    def save_torrent(self, torrent_id, torrent_filename):
        # download torrent file (contents)
        torrent_file_contents = self.get_torrent(torrent_id)
        # save torrent to file
        try:
            with open(os.path.join(self.torrent_file_save_path, torrent_filename), 'wb') as torrent_file:
                torrent_file.write(torrent_file_contents)
        except Exception as e:
            logging.error('Saving %s failed. %s', torrent_filename, e)
        else:
            logging.info('Saving %s succeeded', torrent_filename)
            # increment count
            self.torrent_files_written += 1


# parse config file (as whatapi configparser import is incorrect for Python 3)
def get_username_and_password(config_file):
    config = ConfigParser()
    config.read(config_file)
    username = config.get('login', 'username')
    password = config.get('login', 'password')
    return (username, password)
