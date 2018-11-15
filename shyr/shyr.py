import argparse
import json
import os
import sys

from . import excel, firebase, square, util


def sync_square(catalog_objects):
  square.update(catalog_objects)
  print('Updated Square.')


def sync_firebase(firebase_wines):
  util.save(firebase_wines, util.FIREBASE_FILE)
  firebase.upload(util.FIREBASE_FILE, os.path.basename(util.FIREBASE_FILE))
  print('Updated website.')


def prompt_and_sync(diffs, sync_function):
  if diffs:
    u = input('\nOK with these changes? (y/n) ')
    if u == 'y' or u == 'yes':
      sync_function()
      return True
    else:
      print('Aborted.')
  else:
    print('No sync required.')
  return False


def sync_wines():
  e = excel.Excel()
  print('Firebase:')
  firebase_wines = e.firebase()
  prompt_and_sync(util.diff_firebase(firebase_wines), lambda: sync_firebase(firebase_wines))
  print('Square:')
  catalog_objects = square.make_catalog_objects(e.square())
  return prompt_and_sync(catalog_objects, lambda: sync_square(catalog_objects))


def main():
  parser = argparse.ArgumentParser(
    description='Shyr Wine List wines, images, and factsheet utilities.')

  group = parser.add_mutually_exclusive_group()
  group.add_argument('-s', '--sync', action='store_true',
    help='Sync ShyrWineList.xlsx, images, and factsheets with website and Square.')
  group.add_argument('-w', '--wines', action='store_true',
    help='Sync only ShyrWineList.xlsx with website and Square.')
  group.add_argument('-i', '--images', action='store_true',
    help='Sync only images with website and Square.')
  group.add_argument('-f', '--factsheets', action='store_true',
    help='Sync only factsheets with website.')
  group.add_argument('-d', '--download', action='store_true',
    help=argparse.SUPPRESS)

  if len(sys.argv) == 1:
    parser.print_help()
    return

  args = parser.parse_args()
  wines_synced = images_uploaded = False
  if args.sync or args.wines:
    wines_synced = sync_wines()
  if args.sync or args.images:
    firebase.sync(util.IMAGES_DIR)
    images_uploaded = square.sync_images()
  if args.sync or args.factsheets:
    firebase.sync(util.FACTSHEETS_DIR)
  if wines_synced or images_uploaded or args.download:
    square.download_wines()


if __name__ == '__main__':
  main()
