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


SQUARE_ACCESS_TOKEN = os.environ['SQUARE_ACCESS_TOKEN']
LOCATION_ID = os.environ['SQUARE_LOCATION_ID']
TAX_ID = os.environ['SQUARE_TAX_ID']
RED, GREEN, BLUE, RESET = '\u001b[31m', '\u001b[32m', '\u001b[34m', '\u001b[0m'
IMAGE_URL = 'https://connect.squareup.com/v1/' + LOCATION_ID + '/items/{}/image'
HEADERS = {'Authorization': 'Bearer ' + SQUARE_ACCESS_TOKEN}
squareconnect.configuration.access_token = SQUARE_ACCESS_TOKEN


def make_catalog_objects(old_wines, new_wines, square_map):
  new_wines = sorted(new_wines.values(), key=lambda w: w['SKU'])
  old_wines = sorted(old_wines.values(), key=lambda w: w['SKU'])

  objects = []
  for i in range(len(old_wines)):
    old, new = old_wines[i], new_wines[i]
    old_keys, new_keys = set(old.keys()), set(new.keys())

    added_keys = new_keys - old_keys
    removed_keys = old_keys - new_keys
    diff_keys = {k for k in old_keys.intersection(new_keys) if new[k] != old[k]}

    all_keys = added_keys | removed_keys | diff_keys
    if all_keys:
      print('\n' + new['Name'])
      for key in added_keys:
        print('  Added {} = {}'.format(key, new[key]))
      for key in removed_keys:
        print('  Removed {} = {}'.format(key, old[key]))
      for key in diff_keys:
        print('  Changed {}{}{} from {}{}{} to {}{}{}'.format(
          BLUE, key, RESET, RED, old[key], RESET, GREEN, new[key], RESET))

      # Update Square only if Name, Description, or Price has changed
      if all_keys.intersection({'Name', 'Description', 'Price'}):
        objects.append(make_catalog_object(new, square_map[str(new['SKU'])]))

  for i in range(len(old_wines), len(new_wines)):
    print('\nNew wine:', new_wines[i]['Name'])
    objects.append(make_catalog_object(new_wines[i]))

  return objects


def make_catalog_object(wine, square_data={}):
  return CatalogObject(
    id=square_data.get('item_id', '#{}'.format(wine['SKU'])),
    version=square_data.get('item_version'),
    type='ITEM',
    present_at_all_locations=True,
    item_data=CatalogItem(
      name=wine['Name'],
      description=wine.get('Description', ''),
      tax_ids=[TAX_ID],
      variations=[CatalogObject(
        id=square_data.get('variation_id', '#{}Variation'.format(wine['SKU'])),
        version=square_data.get('variation_version'),
        type='ITEM_VARIATION',
        present_at_all_locations=True,
        item_variation_data=CatalogItemVariation(
          sku=str(wine['SKU']),
          price_money=Money(wine['Price'], 'USD'),
          pricing_type='FIXED_PRICING'
        )
      )]
    )
  )


def update(objects):
  api = CatalogApi()
  idempotency_key = str(uuid.uuid4())
  try:
    response = api.batch_upsert_catalog_objects(
      BatchUpsertCatalogObjectsRequest(
        idempotency_key=idempotency_key,
        batches=[CatalogObjectBatch(objects)]
      )
    )
  except ApiException as e:
    print('Encountered error(s):', e)


def sync_images(image_path, square_wines):
  for sku, wine in square_wines.items():
    image = image_path.format(sku)
    if not wine['image_exists'] and os.path.isfile(image):
      print('Uploading image for ' + wine['name'], end='', flush=True)
      r = upload_image(image, wine['item_id_image'])
      if not r.ok:
        raise RuntimeError(r.text)
      print(u' \u2714')


def upload_image(image, item_id):
  files = [('image_data', (image, open(image, 'rb'), 'image/jpeg'))]
  return requests.post(IMAGE_URL.format(item_id), headers=HEADERS, files=files)


def download_wines():
  wines = {}
  api = CatalogApi()
  response = api.list_catalog(types='ITEM')
  while True:
    for wine in response.objects:
      variation = wine.item_data.variations[0]
      wines[variation.item_variation_data.sku] = {
        'image_exists': wine.item_data.image_url != None,
        'item_id': wine.id,
        'item_id_image': wine.catalog_v1_ids[0].catalog_v1_id if wine.catalog_v1_ids else wine.id,
        'item_version': wine.version,
        'name': wine.item_data.name,
        'variation_id': variation.id,
        'variation_version': variation.version,
      }
    print('\rDownloaded {} wines'.format(len(wines)), end='')
    if not response.cursor:
      break
    response = api.list_catalog(cursor=response.cursor, types='ITEM')
  print(u' \u2714')
  return wines
