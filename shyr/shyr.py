import os

from . import excel, firebase, square, util


def sync_square(catalog_objects):
  square.update(catalog_objects)


def sync_firebase(firebase_wines):
  util.save(firebase_wines, util.FIREBASE_FILE)
  firebase.upload(util.FIREBASE_FILE, os.path.basename(util.FIREBASE_FILE))


def main():
  util.initialize()
  util.log(f'Begin Shyr script with dry_run = {util.dry_run}')

  e = excel.Excel()

  firebase.sync(util.FACTSHEETS_DIR)
  firebase.sync(util.IMAGES_DIR)
  images_uploaded = square.sync_images()

  catalog_objects = square.make_catalog_objects(e.square())
  if catalog_objects:
    sync_square(catalog_objects)
  if catalog_objects or images_uploaded:
    square.download_wines()

  firebase_wines = e.firebase(util.load(util.SQUARE_FILE))
  if util.diff_firebase(firebase_wines):
    sync_firebase(firebase_wines)

  util.log('Sync complete')


if __name__ == '__main__':
  main()
