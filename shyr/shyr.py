import argparse
import json
import os
import sys

from . import excel, image, s3, square


BASE_DIR = os.path.expanduser('~/Dropbox/Shyr/')
EXCEL_FILE = BASE_DIR + 'ShyrWineList.xlsx'
JSON_FILE = BASE_DIR + 'wines.json'
SQUARE_FILE = BASE_DIR + 'square.json'
IMAGES_DIR = BASE_DIR + 'images/'
FACTSHEETS_DIR = BASE_DIR + 'factsheets/'

IMAGE_PATH = IMAGES_DIR + '{}.jpg'
FACTSHEET_PATH = FACTSHEETS_DIR + '{}.pdf'


def load_new_wines():
  return excel.read(EXCEL_FILE, IMAGE_PATH, FACTSHEET_PATH)


def sync_wines():
  with open(JSON_FILE) as fp:
    old_wines = json.load(fp)
  new_wines = load_new_wines()

  # Load SKU -> Square ID mapping
  with open(SQUARE_FILE) as fp:
    square_map = json.load(fp)

  catalog_objects = square.make_catalog_objects(old_wines, new_wines, square_map)

  if not catalog_objects:
    print('No differences.')
    return

  u = input('\nOK with these changes? (y/n) ')
  if u != 'y' and u != 'yes':
    print('Aborted.')
    sys.exit()

  square_map = square.update(catalog_objects, square_map)
  if not square_map:
    print('Upload to Square failed.')
    return

  with open(SQUARE_FILE, 'w') as fp:
    json.dump(square_map, fp)
  with open(JSON_FILE, 'w') as fp:
    json.dump(new_wines, fp, separators=(',', ':'))
  s3.upload(JSON_FILE)


def main():
  parser = argparse.ArgumentParser(
    description='Shyr Wine List wines, images, and factsheet utilities.')

  group = parser.add_mutually_exclusive_group()
  group.add_argument('-s', '--sync', action='store_true',
    help='Sync ShyrWineList.xlsx, images, and factsheets with S3 and Square.')
  group.add_argument('-w', '--wines', action='store_true',
    help='Sync only ShyrWineList.xlsx with S3 and Square.')
  group.add_argument('-i', '--images', action='store_true',
    help='Sync only images with S3 and Square.')
  group.add_argument('-f', '--factsheets', action='store_true',
    help='Sync only factsheets with S3.')
  group.add_argument('-p', '--program', action='store_true',
    help=argparse.SUPPRESS)

  args = parser.parse_args()

  if args.program:
    image.find(load_new_wines(), IMAGE_PATH)
  if args.sync or args.wines:
    sync_wines()
  if args.sync or args.images:
    s3.sync(IMAGES_DIR, 'images/wines')
    square.sync_images(IMAGE_PATH)
  if args.sync or args.factsheets:
    s3.sync(FACTSHEETS_DIR, 'factsheets')
  if len(sys.argv) == 1:
    parser.print_help()


if __name__ == '__main__':
  main()
