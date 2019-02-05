import logging
import os
import sys

from . import excel, firebase, square, util


def sync_square(catalog_objects):
  square.update(catalog_objects)


def sync_firebase(firebase_wines):
  util.save(firebase_wines, util.FIREBASE_FILE)
  firebase.upload(util.FIREBASE_FILE, os.path.basename(util.FIREBASE_FILE))


def prompt_and_sync(diffs, sync_function):
  if not diffs:
    return False
  sync_function()
  return True


def sync_wines():
  e = excel.Excel()
  firebase_wines = e.firebase()
  prompt_and_sync(util.diff_firebase(firebase_wines), lambda: sync_firebase(firebase_wines))
  catalog_objects = square.make_catalog_objects(e.square())
  return prompt_and_sync(catalog_objects, lambda: sync_square(catalog_objects))


def initialize_logger():
  for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

  handler = logging.StreamHandler() if util.dry_run else logging.FileHandler(util.LOG_FILE)
  handler.setFormatter(util.LogFormatter())
  logging.root.addHandler(handler)
  logging.root.setLevel(logging.INFO)


def main():
  util.dry_run = len(sys.argv) > 1 and sys.argv[1] == '--dry-run'
  if not util.dry_run:
    print('Syncing...')

  initialize_logger()
  logging.info(f'Begin Shyr script with dry_run = {util.dry_run}')

  wines_synced = sync_wines()
  firebase.sync(util.IMAGES_DIR)
  images_uploaded = square.sync_images()
  firebase.sync(util.FACTSHEETS_DIR)

  if wines_synced or images_uploaded:
    square.download_wines()
  logging.info('Sync complete')
  if not util.dry_run:
    print('Sync complete.')


if __name__ == '__main__':
  main()
