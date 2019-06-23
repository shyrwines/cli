from datetime import datetime
import os
from os.path import basename, isdir, join, getmtime
from pytz import timezone
import re

import firebase_admin
from firebase_admin import storage

from . import util


FILE_REGEX = re.compile(r'\d{7}\.(jpg|pdf)', re.IGNORECASE)
EXTENSIONS = {
  util.IMAGES_DIR: 'jpg',
  util.FACTSHEETS_DIR: 'pdf',
}


cred = firebase_admin.credentials.Certificate(join(util.BASE_DIR, 'cli', 'firebase-adminsdk.json'))
firebase_admin.initialize_app(cred, {'storageBucket': 'shyrwines.appspot.com'})
bucket = storage.bucket()


def upload(src, dst):
  if not util.dry_run:
    bucket.blob(dst).upload_from_filename(src)
  util.log(f'Uploaded {basename(src)}')


def sync(directory):
  if directory not in EXTENSIONS:
    util.log_warning(f'{directory} is not one of: {set(EXTENSIONS.keys())}')
    return

  local_dir = join(util.BASE_DIR, directory)
  if not isdir(local_dir):
    util.log_warning(f'{local_dir} is not a directory or does not exist')
    return

  file_regex = re.compile(r'\d{7}\.' + EXTENSIONS[directory])
  blobs = {b.name: b.updated for b in bucket.list_blobs(prefix=directory)}
  for filename in os.listdir(local_dir):
    if filename == '.DS_Store':
      continue
    if not file_regex.match(filename):
      util.log_warning(f'{filename} is incorrectly formatted')
      continue
    remote_path = join(directory, filename)
    local_path = join(local_dir, filename)
    mtime = datetime.fromtimestamp(getmtime(local_path), timezone('US/Pacific'))
    if remote_path not in blobs or mtime > blobs[remote_path]:
      upload(local_path, remote_path)
  util.log(f'{directory} synced')
