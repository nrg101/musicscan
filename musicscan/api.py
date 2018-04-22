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
    def torrent(self, torrent_id):
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


    # torrent search
    def torrent_search(self, max_search_results, **kwargs):
        logging.info("**** BEGIN torrent_search() *****")
        # initialise results
        results = []
        # search
        logging.info("searching with fields: %s", kwargs)
        search = self.request('browse', **kwargs)
        # get results from search
        results = self._get_results(search)
        # check for multiple pages
        pages = search["response"].get("pages", None)
        if pages and pages > 1:
            logging.info("Multiple pages of search response")
            # get remaining pages (range(2, pages+1) will do up to pages, not pages+1
            for page in range(2, pages+1):
                # change page number in search terms
                kwargs.update({'page': page})
                # search
                logging.info("searching with fields: %s", kwargs)
                search = self.request('browse', **kwargs)
                # get results from search and add to existing results
                try:
                    results.extend(self._get_results(search))
                except Exception as e:
                    logging.error("Could not combine subsequent search page results. %s", e)
                # check number of results against threshold
                if len(results) >= max_search_results:
                    # truncate results to max
                    del results[max_search_results:]
                    # break out of any more pages
                    break
        # return search
        logging.debug("Search results:\n%s", json.dumps(results, indent=4))
        return results


    # set torrent file save path
    def set_torrent_file_save_path(self, path):
        save_path_is_ok = True
        # check/create subdirectories
        for subdir in ['full', 'partial']:
            save_path_subdir = os.path.join(path, subdir)
            try:
                os.makedirs(save_path_subdir)
            except FileExistsError:
                logging.info("Save path '%s' already exists", save_path_subdir)
                # check if existing directory is not writeable
                if not os.access(save_path_subdir, os.W_OK | os.X_OK):
                    logging.error("Directory '%s' is not writeable", save_path_subdir)
                    save_path_is_ok = False
            except Exception as e:
                logging.error("Could not create directory: %s. %s", save_path_subdir, e)
                save_path_is_ok = False
        # if that went ok, set save path
        if save_path_is_ok:
            self.torrent_file_save_path = path
        # return success or not
        return save_path_is_ok

    
    # save torrent to file
    def save_torrent(self, torrent_id, torrent_filename, match_evaluation):
        # download torrent file (contents)
        torrent_file_contents = self.get_torrent(torrent_id)
        # save torrent to file
        saved_successfully = False
        try:
            with open(os.path.join(self.torrent_file_save_path, torrent_filename), 'wb') as torrent_file:
                torrent_file.write(torrent_file_contents)
            saved_successfully = True
        except Exception as e:
            logging.error('Saving %s failed. %s', torrent_filename, e)
        else:
            logging.info('Saving %s succeeded', torrent_filename)
            # increment count
            self.torrent_files_written += 1
        # return success (True or False)
        return saved_successfully


# parse config file (as whatapi configparser import is incorrect for Python 3)
def get_username_and_password(config_file):
    config = ConfigParser()
    config.read(config_file)
    username = config.get('login', 'username')
    password = config.get('login', 'password')
    return (username, password)
