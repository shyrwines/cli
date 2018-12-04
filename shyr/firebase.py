from datetime import datetime
import logging
import os
from pytz import timezone

import firebase_admin
from firebase_admin import storage

from . import util


cred = firebase_admin.credentials.Certificate(util.BASE_DIR + 'cli/firebase-adminsdk.json')
firebase_admin.initialize_app(cred, {'storageBucket': 'shyrwines.appspot.com'})
bucket = storage.bucket()


def upload(src, dst):
  if not util.dry_run:
    bucket.blob(dst).upload_from_filename(src)
  logging.info('[Firebase] Uploaded ' + os.path.basename(src))


def sync(directory):
  blobs = {b.name: b.updated for b in bucket.list_blobs(prefix=directory)}
  for filename in os.listdir(util.BASE_DIR + directory):
    # TODO: Sanity check filename
    remote_path = directory + filename
    local_path = util.BASE_DIR + remote_path
    mtime = datetime.fromtimestamp(os.path.getmtime(local_path), timezone('US/Pacific'))
    if remote_path not in blobs or mtime > blobs[remote_path]:
      upload(local_path, remote_path)
  logging.info(f'[Firebase] {directory} synced')
