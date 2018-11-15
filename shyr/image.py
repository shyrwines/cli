import os
from urllib.parse import quote_plus
from urllib.request import urlretrieve
import webbrowser

from PIL import Image

from . import excel, util


def download_png(site, dst):
  if site[:4] == 'http':
    png = os.path.expanduser('~/Desktop/tmp.png')
    urlretrieve(site, png)
  else:
    png = site
  im = Image.open(png).convert('RGBA')
  bg = Image.new('RGB', im.size, (255, 255, 255))
  bg.paste(im, mask=im)
  bg.save(dst)
  os.remove(png)


def download_jpg(site, dst):
  if site[:4] == 'http':
    urlretrieve(site, dst)
  else:
    os.rename(site, dst)


def main():
  e = excel.Excel()
  missing = excel.Excel().missing()
  print('Out of {} wines, {} are missing images.'.format(len(e), len(missing)))

  for name, sku in missing.itertuples(False, None):
    dst = util.IMAGE_PATH.format(sku)

    print('Searching for {}, SKU number {}'.format(name, sku))
    webbrowser.open('https://www.google.com/search?q=' + quote_plus(name))

    site = input('Enter site name ([Enter] to skip, q[uit]): ')
    if not site:
      continue
    if site == 'q':
      break

    if site[-4:] == '.png':
      download_png(site, dst)
    elif site[-4:] == '.jpg' or site[-5:] == '.jpeg':
      download_jpg(site, dst)
    print(util.color('Successfully downloaded ' + name, util.GREEN))


if __name__ == '__main__':
  main()
