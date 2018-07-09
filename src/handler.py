#from __future__ import print_function
import json
import os
import datetime
import requests

import hashlib
import boto3
from netCDF4 import Dataset

from creds import CREDS

s3_client = boto3.client('s3')


SUBMIT = """
{
  "type": "spatiotemporal_file",
  "data_category": "Observation",
  "data_format": "NETCDF",
  "data_type": "Single Band Image",
  "datetime": "%s",
  "file_name": "%s",
  "file_size": %i,
  "bounding_box_east": %f,
  "bounding_box_north": %f,
  "bounding_box_south": %f,
  "bounding_box_west": %f,
  "submitter_id": "%s",
  "passive_instruments": [
    {
      "submitter_id": "%s"
    }
  ],
  "geo_orbits": [
    {
      "submitter_id": "GOES16_750W"
    }
  ],
  "core_metadata_collections": [
    {
      "submitter_id": "GOES16_CMC"
    }
  ],
  "md5sum": "%s",
  "urls": "%s"
}
"""

def get_api_auth(api_url):
  
  access_url = api_url + 'user/credentials/cdis/access_token'
  keys = json.loads(CREDS)
  t = requests.post(access_url, json=keys)
  return t

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def parse_s3_event(event):
    sns_message = json.loads(event['Records'][0]['Sns']['Message'])
    s3_event = sns_message['Records'][0]['s3']

    bucket = s3_event['bucket']['name']
    key = s3_event['object']['key']
    return bucket, key

def process_key(key):
    dl_file = 'tmp.nc'

    md5sum = md5('/tmp/' + dl_file)

    nc = Dataset('/tmp/' + dl_file, 'r')
    if nc.variables['geospatial_lat_lon_extent'].geospatial_lon_nadir != -75.0:
        print("Satellite has nadir not -75.0!!!")
        return

    bbox_left = nc.variables['geospatial_lat_lon_extent'].geospatial_westbound_longitude
    bbox_right = nc.variables['geospatial_lat_lon_extent'].geospatial_eastbound_longitude
    bbox_top = nc.variables['geospatial_lat_lon_extent'].geospatial_northbound_latitude
    bbox_bottom = nc.variables['geospatial_lat_lon_extent'].geospatial_southbound_latitude

    nc.close()
    nc = None

    filename = os.path.basename(key)

    NAME = ""
    if filename.startswith('OR_ABI-L2-CMIPF'):
        NAME = "GOES16_FD"
    elif filename.startswith('OR_ABI-L2-CMIPC'):
       NAME = "GOES16_CONUS"
    elif filename.startswith('OR_ABI-L2-CMIPM1'):
       NAME = "GOES16_M1"
    elif filename.startswith('OR_ABI-L2-CMIPM2'):
       NAME = "GOES16_M2"

    print(filename)
    parts = filename.split("_")
    product = 'CH' + parts[1][-2:]
    year = parts[3][1:][:4]
    julian_day = parts[3][5:][:3]
    time = parts[3][-7:][:4]
    hour = time[:2]
    minute = time[-2:]
    second = parts[3][-3:][:2]
    date = datetime.datetime(int(year), 1, 1) + datetime.timedelta(int(julian_day)-1)
    day = date.strftime('%d')
    month = date.strftime('%m')
    filesize = os.path.getsize('/tmp/' + dl_file)
    data_datetime = "%s-%s-%sT%s:%s:%sZ" % (year, month, day, hour, minute, second)
    submitter_id = NAME + "_%s_%s%s%s%s%s%s" % (product, year, month, day, hour, minute, second)
    urls = "s3://noaa-goes16/%s,gs://gcp-public-data-goes-16/%s,https://osdc.rcc.uchicago.edu/noaa-goes16/%s" % (key, key, key)
    submit_data = SUBMIT % (data_datetime, filename, filesize, bbox_right, bbox_top, bbox_bottom, bbox_left, submitter_id, product, md5sum, urls)
    print submit_data
    auth = get_api_auth('https://portal.occ-data.org/')
    response = requests.put('https://portal.occ-data.org/api/v0/submission/edc/data', headers={'Authorization': 'bearer '+ auth.json()['access_token']}, data=submit_data)
    print(response.text)

def lambda_handler(event, context):
    bucket, key = parse_s3_event(event)
    print('INPUT', bucket, key)

    if not (key.startswith('ABI-L2-CMIPF') or key.startswith('ABI-L2-CMIPC') or key.startswith('ABI-L2-CMIPM')):
       return

    s3_client.download_file(bucket, key, '/tmp/tmp.nc')
    process_key(key)


if __name__ == "__main__":
    process_key('ABI-L2-CMIPC/2017/192/19/OR_ABI-L2-CMIPC-M3C15_G16_s20171921937189_e20171921939568_c20171921940027.nc')
