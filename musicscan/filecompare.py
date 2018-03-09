# imports: standard
import logging
import os
import html
import re

# imports: custom
import musicscan.findmusiclocal

# parse fileList string into a list of files (name and size)
def parse_torrent_files(file_list):
    # split string into list of strings: "FILENAME{{{FILESIZE}}}"
    list_filenamesize = file_list.split("|||")
    logging.debug("list_filenamesize: %s", list_filenamesize)
    files = []
    for filenamesize in list_filenamesize:
        # strip out weird Atilde
        filenamesize = re.sub(r'\ *&Atilde{{{', '{{{', filenamesize)
        # pick out filename and filesize
        filename, filesize = filenamesize.split("{{{")
        # html unescape the filename
        filename = html.unescape(filename)
        # pick out filesize
        filesize = filesize[:-3]
        logging.debug("filename = {0}, filesize = {1}".format(filename, filesize))
        files.append({
                "name": filename,
                "size": filesize
        })
    return files

# get local file sizes
def get_local_file_sizes(files):
    # return list of file sizes
    return [ os.path.getsize(filepath) for filepath in files if os.access(filepath, os.R_OK) ]

# get local file names
def get_local_file_names(files):
    # return list of file names
    return [ os.path.basename(os.path.normpath(filepath)) for filepath in files ]

# get torrent file sizes
def get_torrent_file_sizes(torrent_files):
    # return list of file sizes
    return [ int(torrent_file["size"]) for torrent_file in torrent_files ]

# get torrent music file sizes
def get_torrent_audio_file_sizes(torrent_files):
    # return list of file sizes (music/audio only)
    return [ int(torrent_file["size"]) for torrent_file in torrent_files \
                if musicscan.findmusiclocal.is_audio_file(torrent_file["name"]) ]

# get torrent file names
def get_torrent_file_names(torrent_files):
    # return list of file names
    return [ torrent_file["name"] for torrent_file in torrent_files ]

# compare torrent files to local files
def match_torrent_files(torrent_files, release):
    logging.info("**** BEGIN match_torrent_files() *****")
    # get file sizes
    torrent_file_sizes = get_torrent_file_sizes(torrent_files)
    logging.debug("torrent_file_sizes = %s", torrent_file_sizes)
    torrent_audio_file_sizes = get_torrent_audio_file_sizes(torrent_files)
    logging.debug("torrent_audio_file_sizes = %s", torrent_audio_file_sizes)
    local_file_sizes = get_local_file_sizes(release["all_files"])
    logging.debug("local_file_sizes = %s", local_file_sizes)
    local_audio_file_sizes = get_local_file_sizes(release["audio_files"])
    logging.debug("local_audio_file_sizes = %s", local_audio_file_sizes)
    # get file names
    torrent_file_names = get_torrent_file_names(torrent_files)
    logging.debug("torrent_file_names = %s", torrent_file_names)
    local_file_names = get_local_file_names(release["all_files"])
    logging.debug("local_file_names = %s", local_file_names)

    # calculate matches
    audio_filesize_matches = list(set(torrent_audio_file_sizes).intersection(set(local_audio_file_sizes)))
    filesize_matches = list(set(torrent_file_sizes).intersection(set(local_file_sizes)))
    filename_matches = list(set(torrent_file_names).intersection(set(local_file_names)))
    # calculate matches percentage
    try:
        audio_filesize_matches_pct = round(100 * len(audio_filesize_matches) / len(torrent_audio_file_sizes), 2)
    except Exception as e:
        logging.error("failed calculating percentage. %s", e)
        audio_filesize_matches_pct = 0
    try:
        filesize_matches_pct = round(100 * len(filesize_matches) / len(torrent_files), 2)
    except Exception as e:
        logging.error("failed calculating percentage. %s", e)
        filesize_matches_pct = 0
    try:
        filename_matches_pct = round(100 * len(filename_matches) / len(torrent_files), 2)
    except Exception as e:
        logging.error("failed calculating percentage. %s", e)
        filename_matches_pct = 0
    
    matches = {
            "audio_filesize_matches_pct": audio_filesize_matches_pct,
            "filesize_matches_pct": filesize_matches_pct,
            "filename_matches_pct": filename_matches_pct
    }
    logging.info("***** END match_torrent_files() *****")
    return matches


# evaluate the match results
def evaluate_match(matches, music_threshold):
    # if everything was a full match
    if matches["audio_filesize_matches_pct"] == 100 and \
            matches["filesize_matches_pct"] == 100 and \
            matches["filename_matches_pct"] == 100:
        evaluation = "full"
    # otherwise if at least the music files match was above threshold
    elif matches["audio_filesize_matches_pct"] >= music_threshold:
        evaluation = "partial"
    # otherwise, no match, or below threshold
    else:
        evaluation = None
    # log evaluation outcome
    logging.info("match evaluation = %s", evaluation)
    return evaluation