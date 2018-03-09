#!/usr/bin/env python

# imports: standard
import os
import re
import logging
from collections import Counter

# imports: third party
import mutagen                                  # pip install mutagen
from mutagen.easyid3 import EasyID3             # pip install mutagen
from dateutil.parser import parse as dtparse    # pip install python-dateutil

# constants
EXTENSIONS = ('.flac', '.mp3', '.aac', '.ac3', '.dts')
DISC_SUBFOLDER_REGEX = re.compile(r"(?<![A-Za-z0-9])(cd|disc|disk)[-_\ ]?\d{1,2}(?![A-Za-z0-9]+)", flags=re.IGNORECASE)


def simplify_album(album):
    # remove (), [], cd x, disc x, and resulting whitespace at ends
    return re.sub(
            r'(\([^\)]*\)|\[[^\]]*\]|(cd|disc) ?\d+)', 
            '', 
            album, 
            flags=re.IGNORECASE
    ).strip()


def is_music_file(filename):
    # split filename to name (ignored) and extension
    _, extension = os.path.splitext(filename)
    # check if extension is in list of valid music types
    is_music_file = extension.lower() in EXTENSIONS
    logging.debug("%s %s a music file", filename, "is" if is_music_file else "isn't")
    return is_music_file


def find_music_files(path):
    music_files = []
    # traverse all files in path
    for dirpath, _, filenames in os.walk(path):
        # list comprehension of music files, extend music_files list
        music_files.extend([ os.path.join(dirpath, f) for f in filenames if is_music_file(f) ])
    return music_files


def find_all_files(path):
    all_files = []
    # traverse all files in path
    for dirpath, _, filenames in os.walk(path):
        # list comprehension of all files, extend all_files list
        all_files.extend([ os.path.join(dirpath, f) for f in filenames ])
    return all_files


def is_disc_subfolder(dirname):
    return DISC_SUBFOLDER_REGEX.search(dirname)


"""
Get a release's basic info by looking at the tags of each track
"""
def get_release_basics(music_files):
    logging.info("***** BEGIN get_release_basics() *****")
    artists = []
    album = None
    audio_format = None
    year = None
    for music_filepath in music_files:
        music_filename = os.path.basename(os.path.normpath(music_filepath))
        logging.info("checking %s", music_filename)
        tags = {}
        if music_filename.lower().endswith(".mp3"):
            logging.debug("extension is mp3")
            audio_format = 'MP3'
            logging.debug("getting mp3 tags")
            try:
                tags = EasyID3(music_filepath)
            except Exception as e:
                logging.warning("Failed to get mp3 tags for %s. %s", music_filename, e)
        else:
            logging.debug("extension is something other than mp3")
            logging.debug("getting tags")
            try:
                tags = mutagen.File(music_filepath)
            except Exception as e:
                logging.warning("Failed to get tags for %s. %s", music_filename, e)
            # if there's a mime tag and one of them is audio/flac
            if getattr(tags, "mime", None) and 'audio/flac' in tags.mime:
                logging.debug("audio/flac found in mime tag")
                audio_format = 'FLAC'
        if "albumartist" in tags:
            logging.debug("adding %s to artists", tags["albumartist"])
            artists += tags["albumartist"]
        elif "artist" in tags:
            logging.debug("adding %s to artists", tags["artist"])
            artists += tags["artist"]
        if "album" in tags:
            album = simplify_album(tags["album"][0])
            logging.debug("found album title: %s", album)
        if "date" in tags:
            logging.debug("parsing date from %s", tags["date"])
            try:
                year = dtparse(tags['date'][0][:7]).year
            except ValueError as e:
                logging.error("no date could be found. %s", e)
            except Exception as e:
                logging.error("error parsing year from %s. %s", tags["date"], e)
            else:
                logging.debug("found year: %s", year)
    # determine most common artist
    if len(artists) > 0:
        logging.debug("determining most common artist in %s", artists)
        most_common_artist, num_most_common = Counter(artists).most_common(1)[0]
        logging.debug("%s with a count of %s", most_common_artist, num_most_common)
    else:
        logging.debug("no artists found")
        most_common_artist = None
    logging.debug("most_common_artist: %s", most_common_artist)
    # replace non alpha-numeric characters with space to avoid search misses for symbols
    if album:
        album = re.sub('\W', ' ', album)
    if most_common_artist:
        most_common_artist = re.sub('\W', ' ', most_common_artist)
    # return the basic info
    basic_info = {
        "artist": most_common_artist,
        "album": album,
        "year": year,
        "audio_format": audio_format
    }
    logging.debug("basic_info: %s", basic_info)
    logging.info("***** END get_release_basics() *****")
    return basic_info


def find_releases(path):
    logging.info("***** BEGIN find_releases() *****")
    # traverse paths
    for dirpath, subdirs, _ in os.walk(path, topdown=True):
        logging.info("***** BEGIN processing for %s *****", dirpath)
        # only continue for paths that are not a disc subfolder
        path_tail = os.path.basename(os.path.normpath(dirpath))
        logging.debug("path_tail is '%s'", path_tail)
        if not is_disc_subfolder(path_tail):
            logging.debug("'%s' is deemed as not a disc subfolder", path_tail)
            # create list of subfolders that are disc subfolders
            disc_subfolders = [ s for s in subdirs if is_disc_subfolder(s) ]
            logging.debug("%s has the following disc subfolders: %s", path_tail, disc_subfolders)
            # if the current path is a leaf, or has disc subfolders
            if len(subdirs) == 0 or len(disc_subfolders) > 0:
                logging.debug("%s is a leaf or has disc subfolders", dirpath)
                # get all music files (recursively)
                music_files = find_music_files(dirpath)
                logging.info("%s music files found", len(music_files))
                if len(music_files) > 0:
                    logging.info("music files: %s", [ os.path.basename(os.path.normpath(m)) for m in music_files ])
                    yield {
                        "dirpath": dirpath,
                        "dirpath_simplified": simplify_album(os.path.basename(os.path.normpath(dirpath))),
                        "music_files": music_files,
                        "all_files": find_all_files(dirpath)
                    }
            else:
                logging.debug("%s has subfolders that aren't disc subfolders. Skipping individual processing", path_tail)
        else:
            logging.debug("%s is deemed as a disc subfolder. Skipping individiual processing", path_tail)
        logging.info("***** END processing for %s *****", dirpath)
    logging.info("***** END find_releases() *****")
