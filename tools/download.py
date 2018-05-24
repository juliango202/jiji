import os
import time
import hashlib
import gzip
import shutil
from subprocess import run
from itertools import chain


CACHE_DIRECTORY = "downloads_cache"


def decompress_gzip_file(filepath):
    decompressed = filepath + ".decompressed"
    if not os.path.exists(decompressed):
        with gzip.open(filepath, 'rb') as f_in:
            with open(decompressed, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    return decompressed


def download_if_modified(url):
    """Download a file only if is has been modified via curl, see https://superuser.com/a/1159510"""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    filename = f'{curr_dir}/{CACHE_DIRECTORY}/{url_hash}'
    print(f'Download {url} if it has been modified, destination is {filename}')

    # If file exists and was modified today do not check for update
    check_for_update = True
    if os.path.exists(filename):
        file_stat = os.stat(filename)
        file_age_seconds = (time.time() - file_stat.st_mtime)
        if file_age_seconds < 60 * 60 * 24:
            check_for_update = False
            print('File on disk is less than a day old, do not check for update.')

    if check_for_update:
        run(chain(
            ('curl', '-s', url),
            ('-o', filename),
            ('-z', filename) if os.path.exists(filename) else (),
        ))

    filepath = os.path.abspath(filename)

    # Auto decompress gzip files
    if url.endswith('.gz'):
        return decompress_gzip_file(filepath)

    return filepath
