#!/bin/bash
/opt/python/cp37-cp37m/bin/pip install -r /app/requirements.txt

mkdir -p /app/build
cp -r /opt/python/cp37-cp37m/lib/python3.7/site-packages/* /app/build
