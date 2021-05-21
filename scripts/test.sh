#!/bin/bash
/opt/python/cp37-cp37m/bin/pip install -r /app/requirements.txt

cd /app/
mkdir -p /tmp
cp /app/test/OR_ABI-L2-CMIPC-M3C15_G16_s20171921937189_e20171921939568_c20171921940027.nc /tmp/tmp.nc
/opt/python/cp37-cp37m/bin/python src/handler.py
