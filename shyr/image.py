import os
import shutil
import sys
from urllib.parse import quote_plus
import webbrowser

from PIL import Image
import requests

from . import excel, util


def download_image(site, dst):
  r = requests.get(site, stream=True)
  if not r.ok:
    raise RuntimeError(f'Unable to download file: {r.text}')
  r.raw.decode_content = True
  with open(dst, 'wb') as fp:
    shutil.copyfileobj(r.raw, fp)


def download_png(site, dst):
  if site[:4] == 'http':
    png = os.path.expanduser('~/Desktop/tmp.png')
    download_image(site, png)
  else:
    png = site
  im = Image.open(png).convert('RGBA')
  bg = Image.new('RGB', im.size, (255, 255, 255))
  bg.paste(im, mask=im)
  bg.save(dst)
  os.remove(png)


def download_jpg(site, dst):
  if site[:4] == 'http':
    download_image(site, dst)
  else:
    os.rename(site, dst)


def main():
  e = excel.Excel()
  missing = excel.Excel().missing()
  print('Out of {} wines, {} are missing images.'.format(len(e), len(missing)))

  start_sku = int(sys.argv[1]) if len(sys.argv) > 1 else 0
  for name, sku in filter(lambda t: t[1] >= start_sku, missing.itertuples(False, None)):
    print('Searching for {}, SKU number {}'.format(name, sku))
    if sku != start_sku:
      webbrowser.open('https://www.google.com/search?q=' + quote_plus(name))

    site = input('Enter site name ([Enter] to skip, q[uit]): ').strip()
    if not site:
      continue
    if site == 'q':
      return

    dst = util.IMAGE_PATH.format(sku)
    ext = os.path.splitext(site)[1]
    if ext == '.png':
      download_png(site, dst)
    elif ext in {'.jpg', '.jpeg'}:
      download_jpg(site, dst)
    else:
      print('Unrecognized file extension', ext)
      return
    print(util.color('Successfully downloaded ' + name, util.GREEN))


if __name__ == '__main__':
  main()
