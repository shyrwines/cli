import json
import logging
import os
import re
import unicodedata

BASE_DIR = os.path.expanduser('~/Dropbox/Shyr/')
EXCEL_FILE = BASE_DIR + 'ShyrWineList.xlsx'
ENV_FILE = BASE_DIR + 'cli/env.json'
SQUARE_FILE = BASE_DIR + 'cli/square.json'
FIREBASE_FILE = BASE_DIR + 'cli/wines.json'
LOG_FILE = BASE_DIR + 'cli/log.txt'
IMAGES_DIR = 'wine-images/'
IMAGE_PATH = BASE_DIR + IMAGES_DIR + '{}.jpg'
FACTSHEETS_DIR = 'factsheets/'
FACTSHEET_PATH = BASE_DIR + FACTSHEETS_DIR + '{}.pdf'
RED, GREEN, BLUE, RESET = '\u001b[31m', '\u001b[32m', '\u001b[34m', '\u001b[0m'
NONALPHANUMERIC = re.compile(r'[^\w\s-]')
WHITESPACE = re.compile(r'[-\s]+')
CHECKMARK = u' \u2714'

dry_run = True
sid = None
sio = None

class LogFormatter(logging.Formatter):
  def format(self, record):
    location = '{0.module}.{0.funcName}:{0.lineno}'.format(record)
    return '{0} {1:25} {2.levelname:>5}: {2.msg}'.format(self.formatTime(record), location, record)


def initialize_logger():
  for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

  handler = logging.StreamHandler() if dry_run else logging.FileHandler(LOG_FILE)
  handler.setFormatter(LogFormatter())
  logging.root.addHandler(handler)
  logging.root.setLevel(logging.INFO)


def log(msg):
  logging.info(msg)
  if sio:
    sio.emit('reply', msg, sid)


def log_warning(msg):
  logging.warning(msg)
  if sio:
    sio.emit('reply', msg, sid)


def save(obj, filename):
  if not dry_run:
    with open(filename, 'w') as fp:
      json.dump(obj, fp, separators=(',', ':'))
  log(f'Saved {filename}')


def load(filename):
  with open(filename) as fp:
    return json.load(fp)


def tokenize(s):
  return WHITESPACE.sub('-', NONALPHANUMERIC.sub('',
    unicodedata.normalize('NFKC', s).strip().lower()))


def color(s, c, key=None):
  s = str(s)
  if key == 'Price':
    s = '$' + s[:-2] + '.' + s[-2:]
  return c + s + RESET


def print_diff(old, new, keys=None):
  # TODO: Add docstrings everywhere
  old_keys, new_keys = set(old.keys()), set(new.keys())
  if keys:
    old_keys, new_keys = old_keys & keys, new_keys & keys

  added_keys = new_keys - old_keys
  removed_keys = old_keys - new_keys
  diff_keys = {k for k in old_keys.intersection(new_keys) if new[k] != old[k]}

  all_keys = added_keys | removed_keys | diff_keys
  if all_keys:
    log(f'Changed {new["Name"]}:')
    for key in added_keys:
      log(f'  Added {key} = {new[key]}')
    for key in removed_keys:
      log(f'  Removed {key} = {old[key]}')
    for key in diff_keys:
      log(f'  Changed {key} from {old[key]} to {new[key]}')
    return True
  return False


def diff_firebase(new_wines):
  old_wines = load(FIREBASE_FILE)
  old_keys, new_keys = old_wines.keys(), new_wines.keys()

  added_wines = new_keys - old_keys
  removed_wines = old_keys - new_keys
  both_wines = old_keys & new_keys

  for wine_id in both_wines:
    print_diff(old_wines[wine_id], new_wines[wine_id])
  for wine_id in removed_wines:
    log('Removed ' + old_wines[wine_id]['Name'])
  for wine_id in added_wines:
    log('Added ' + new_wines[wine_id]['Name'])

  return old_wines != new_wines
