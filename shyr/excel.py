import os
import re
import unicodedata

import xlrd


STRINGS = {'Name', 'Vintage', 'Winery', 'Country', 'Region', 'Appellation', 'Varietal', 'Type', 'Description'}
RATERS = {'JH', 'JS', 'RP', 'ST', 'AG', 'D', 'WA', 'WE', 'WS', 'W&S', 'WW'}
COLUMNS = STRINGS | RATERS
NONALPHANUMERIC = re.compile(r'[^\w\s-]')
WHITESPACE = re.compile(r'[-\s]+')


def read(filename, image_path, factsheet_path):
  rows = xlrd.open_workbook(filename).sheet_by_index(0).get_rows()
  headers = [c.value for c in next(rows)]
  header_map = {h: headers.index(h) for h in headers}

  wines = {}
  for row in rows:
    if row[header_map['No-Adv']].value == 'N':
      continue

    sku = int(row[header_map['SKU']].value)
    wine = {
      'Count': 1 if row[header_map['Count']].ctype == xlrd.XL_CELL_EMPTY else 0,
      'Price': round(row[header_map['Price']].value * 100),
      'SKU': sku,
      'image': os.path.isfile(image_path.format(sku)),
      'factsheet': os.path.isfile(factsheet_path.format(sku))
    }
    for column in COLUMNS:
      cell = row[header_map[column]]
      if cell.ctype != xlrd.XL_CELL_EMPTY:
        wine[column] = cell.value if column in STRINGS else int(cell.value)

    wine_id = WHITESPACE.sub('-', NONALPHANUMERIC.sub('',
      unicodedata.normalize('NFKC', row[0].value).strip().lower()))
    wines[wine_id] = wine

  return wines
