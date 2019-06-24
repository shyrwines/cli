import os

import pandas as pd

from . import util


DROP = ['Cost', 'Rev Margin', 'Margin']
INTEGERS = ['Count', 'JH', 'JS', 'RP', 'ST', 'AG', 'D', 'WA', 'WE', 'WS', 'W&S', 'WW']
DTYPE = {i: object for i in INTEGERS}


class Excel(object):
  def __init__(self):
    self.df = pd.read_excel(util.EXCEL_FILE, dtype=DTYPE).drop(DROP, axis=1)
    self.validate()
    self.df['Price'] = self.df['Price'].apply(lambda x: round(x * 100))

  def __len__(self):
    return len(self.df)

  def validate(self):
    duplicates = self.df.duplicated('SKU')
    if any(duplicates):
      sku = self.df[duplicates].iloc[0]['SKU']
      wines = self.df[self.df['SKU'] == sku]['Name'].tolist()
      util.log_error(f'Duplicate SKU {sku} for wines: {wines}')
      raise RuntimeError('Duplicate SKU')

  def square(self):
    df = self.df.set_index('SKU')[['Name', 'Description', 'Price']]
    df.index = df.index.astype(str)
    df['Description'].fillna('', inplace=True)
    return df.to_dict('index')

  def firebase(self, square):
    df = self.df[self.df['No-Adv'] != 'N'].copy()
    df['Count'].fillna(1, inplace=True)
    df.loc[:,'factsheet'] = df['SKU'].apply(lambda x: os.path.isfile(util.FACTSHEET_PATH.format(x)))
    df.loc[:,'variation_id'] = df['SKU'].apply(lambda x: square[str(x)]['variation_id'])
    df.index = df['Name'].apply(lambda x: util.tokenize(x))
    return {i: {k:v for k,v in d.items() if pd.notnull(v)} for i,d in df.to_dict('index').items()}

  def missing(self):
    return self.df[self.df['SKU'].apply(lambda x: not os.path.isfile(util.IMAGE_PATH.format(x)))][['Name', 'SKU']].copy()
