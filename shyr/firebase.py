from datetime import datetime
import os
from pytz import timezone

import firebase_admin
from firebase_admin import storage

from . import util


cred = firebase_admin.credentials.Certificate(util.BASE_DIR + 'cli/firebase-adminsdk.json')
firebase_admin.initialize_app(cred, {'storageBucket': 'shyrwines.appspot.com'})
bucket = storage.bucket()


def upload(src, dst):
  print('[Website] Uploading', os.path.basename(src), end='', flush=True)
  bucket.blob(dst).upload_from_filename(src)
  print(util.CHECKMARK)


def sync(directory):
  blobs = {b.name: b.updated for b in bucket.list_blobs(prefix=directory)}
  for filename in os.listdir(util.BASE_DIR + directory):
    # TODO: Sanity check filename
    remote_path = directory + filename
    local_path = util.BASE_DIR + remote_path
    mtime = datetime.fromtimestamp(os.path.getmtime(local_path), timezone('US/Pacific'))
    if remote_path not in blobs or mtime > blobs[remote_path]:
      upload(local_path, remote_path)
  print('[Website]', directory, 'synced.')