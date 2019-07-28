import os
from traceback import format_exc

from . import excel, firebase, square, util

def sync():
  util.initialize()
  util.log(f'Starting sync with dry_run = {util.dry_run}')

  e = excel.Excel()

  firebase.sync(util.FACTSHEETS_DIR)
  firebase.sync(util.IMAGES_DIR)
  images_uploaded = square.sync_images()

  catalog_objects = square.make_catalog_objects(e.square())
  if catalog_objects:
    square.update(catalog_objects)
  if catalog_objects or images_uploaded:
    square.download_wines()

  firebase_wines = e.firebase(util.load(util.SQUARE_FILE))
  if util.diff_firebase(firebase_wines):
    util.save(firebase_wines, util.FIREBASE_FILE)
    firebase.upload(util.FIREBASE_FILE, os.path.basename(util.FIREBASE_FILE))

  util.log('Sync complete')


def main():
  try:
    sync()
  except Exception:
    util.log_error('Encountered exception:\n' + format_exc())


if __name__ == '__main__':
  main()
