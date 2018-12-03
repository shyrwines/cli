import json
import logging
import os
import uuid

import requests
import squareconnect
from squareconnect.apis.catalog_api import CatalogApi
from squareconnect.models.batch_upsert_catalog_objects_request import BatchUpsertCatalogObjectsRequest
from squareconnect.models.catalog_item import CatalogItem
from squareconnect.models.catalog_item_variation import CatalogItemVariation
from squareconnect.models.catalog_object import CatalogObject
from squareconnect.models.catalog_object_batch import CatalogObjectBatch
from squareconnect.models.money import Money
from squareconnect.rest import ApiException

from . import util


env = util.load(util.ENV_FILE)
SQUARE_ACCESS_TOKEN = env['SQUARE_ACCESS_TOKEN']
LOCATION_ID = env['SQUARE_LOCATION_ID']
TAX_ID = env['SQUARE_TAX_ID']
IMAGE_URL = 'https://connect.squareup.com/v1/' + LOCATION_ID + '/items/{}/image'
HEADERS = {'Authorization': 'Bearer ' + SQUARE_ACCESS_TOKEN}


def make_catalog_objects(new_wines):
  square_wines = util.load(util.SQUARE_FILE)
  objects = []
  for sku, new in sorted(new_wines.items()):
    if sku in square_wines:
      if util.print_diff(square_wines[sku], new, {'Name', 'Description', 'Price'}):
        objects.append(make_catalog_object(new, sku, square_wines[sku]))
    else:
      logging.info('New wine:', new['Name'])
      objects.append(make_catalog_object(new, sku))
  return objects


def make_catalog_object(wine, sku, square_wine={}):
  return CatalogObject(
    id=square_wine.get('item_id', '#{}'.format(sku)),
    version=square_wine.get('item_version'),
    type='ITEM',
    present_at_all_locations=True,
    item_data=CatalogItem(
      name=wine['Name'],
      description=wine.get('Description', ''),
      tax_ids=[TAX_ID],
      variations=[CatalogObject(
        id=square_wine.get('variation_id', '#{}Variation'.format(sku)),
        version=square_wine.get('variation_version'),
        type='ITEM_VARIATION',
        present_at_all_locations=True,
        item_variation_data=CatalogItemVariation(
          sku=sku,
          price_money=Money(wine['Price'], 'USD'),
          pricing_type='FIXED_PRICING'
        )
      )]
    )
  )


def update(objects):
  api = CatalogApi()
  api.api_client.configuration.access_token = SQUARE_ACCESS_TOKEN
  idempotency_key = str(uuid.uuid4())
  try:
    response = api.batch_upsert_catalog_objects(
      BatchUpsertCatalogObjectsRequest(
        idempotency_key=idempotency_key,
        batches=[CatalogObjectBatch(objects)]
      )
    )
  except ApiException as e:
    logging.error(f'Error while upserting catalog objects to Square: {e}')
    raise RuntimeError('Error while syncing with Square.')


def sync_images():
  square_wines = util.load(util.SQUARE_FILE)
  local = {os.path.splitext(f)[0] for f in os.listdir(util.BASE_DIR + util.IMAGES_DIR)}
  no_square = {sku for sku, w in square_wines.items() if not w['image_exists']}
  skus_to_upload = local & no_square
  for sku in skus_to_upload:
    logging.info(f'[Square] Uploading {sku}.jpg')
    r = upload_image(util.IMAGE_PATH.format(sku), square_wines[sku]['item_id_image'])
    if not r.ok:
      logging.error(f'Error while uploading image to Square: {r.text}')
      raise RuntimeError('Error while syncing wine images with Square.')
  logging.info(f'[Square] {util.IMAGES_DIR} synced.')
  return len(skus_to_upload) != 0


def upload_image(image, item_id):
  files = [('image_data', (image, open(image, 'rb'), 'image/jpeg'))]
  return requests.post(IMAGE_URL.format(item_id), headers=HEADERS, files=files)


def download_wines():
  wines = {}
  api = CatalogApi()
  api.api_client.configuration.access_token = SQUARE_ACCESS_TOKEN
  response = api.list_catalog(types='ITEM')
  while True:
    for wine in response.objects:
      variation = wine.item_data.variations[0]
      if not variation.item_variation_data.price_money:
        # Exclude Shipping & Handling, which has no price
        continue
      wines[variation.item_variation_data.sku] = {
        'image_exists': wine.item_data.image_url != None,
        'item_id': wine.id,
        'item_id_image': wine.catalog_v1_ids[0].catalog_v1_id if wine.catalog_v1_ids else wine.id,
        'item_version': wine.version,
        'variation_id': variation.id,
        'variation_version': variation.version,
        'Name': wine.item_data.name,
        'Price': variation.item_variation_data.price_money.amount,
        'Description': wine.item_data.description or '',
      }
    if not response.cursor:
      break
    response = api.list_catalog(cursor=response.cursor, types='ITEM')
  util.save(wines, util.SQUARE_FILE)
  logging.info(f'Downloaded {len(wines)} wines from Square')
