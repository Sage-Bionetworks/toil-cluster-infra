#! /usr/bin/env python2

import boto3
import sys

if len(sys.argv) < 2:
    print('Usage: {} bucket_name'.format(__file__))
    sys.exit(1)
bucket_name = sys.argv[1]

message = 'Please confirm that you want to remove bucket {} (y/n)'.format(bucket_name)
verify = raw_input(message)
if verify != 'y':
    print('Exiting')
    sys.exit(1)

region = "us-east-1"
client = boto3.client('s3', region_name=region)

repeat_list = True
while repeat_list:
    list_response = client.list_object_versions(Bucket=bucket_name)
    print(list_response)
    repeat_list = True if 'isTruncated' in list_response and list_response.get('isTruncated') is True else False
    print('\nLIST OBJECT VERSIONS')
    print('has isTruncated? {}'.format('isTruncated' in list_response))
    num_versions = len(list_response.get('Versions', []))
    print('num versions: {}'.format(num_versions))
    if 'Versions' in list_response:
        delete_objects = [
            {
                'Key': item.get('Key'),
                'VersionId': item.get('VersionId')
            }
            for item in list_response.get('Versions')]

        if delete_objects:
            delete_objects_response = client.delete_objects(
                Bucket = bucket_name,
                Delete = {
                    'Objects': delete_objects
                }
            )
            print('Number object versions deleted from bucket: {}'.format(len(delete_objects_response.get('Deleted',[]))))
            errors = delete_objects_response.get('Errors', [])
            if errors:
                print('Delete versions errors: {}'.format(errors))
                sys.exit(1)

delete_bucket_response = client.delete_bucket(Bucket=bucket_name)
print('\nDELETE BUCKET RESPONSE')
print(delete_bucket_response)
