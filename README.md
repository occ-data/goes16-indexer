# Lambda GOES-16 Indexer

For indexing the GOES-16 feed from the NOAA Big Data Project into the OCC Environmental Data Commons. This utilizies a lambda on AWS to process the SNS feed of the data being created in S3. It currently only processes the L2 files. The files are downloaded locally so md5 hashes can be computed, with easy options to extent to others in the future. The files are submitted as `spatiotemporal_file` nodes on EDC which automatically submits them to the EDC indexd instance as well.

## This code

This code has been adapted from https://github.com/perrygeo/lambda-rasterio. Thanks to them for figuring out the basic template of how to easily make, test, and package a python lambda function.

## Testing

You can test the main parts of the python code by using:
```
make test
```
Which utilizes `DockerfileTest` to load requirements.txt so they don't have to be reinstalled every time you want to test the app. This testing could be improved in the future to pass an actual example json to the lambda handler.

## Set Creds

The OCC EDC requires Gen3 credentials to submit nodes to the graph. Load them into `src/creds.py` like this:
```
CREDS = """
{ "api_key": "apikeyhere", "key_id": "keyuuid" }
"""
```
This could be improved in the future to download an encrypted blob from S3 and decrypt it using KMS.

## Deploying

First set up a lambda function on AWS using python 2.7. Give it a name such as `goes16`. Set SNS on the left side of the Lambda with `arn:aws:sns:us-east-1:123901341784:NewGOES16Object` as the appropriate arn for the GOES-16 feed. Make sure to set the `Handler` in the lambda function to `handler.lambda_handler` so that this will work.

Build the necessary zip file using:
```
make
```

Upload the zip file to the lambda function:
```
aws lambda update-function-code --function-name goes16 --zip-file fileb://dist.zip --profile edc
```
