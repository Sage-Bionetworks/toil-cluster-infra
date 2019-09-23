#! /usr/bin/env python3

import argparse
import boto3
import sys


def parse_args():
    parser = argparse.ArgumentParser(
        description='Empties and deletes a bucket')
    parser.add_argument(
        'bucket_name',
        help='The name of the bucket to remove')
    parser.add_argument(
        '-y', '--yes',
        action='store_true',
        help='Skip prompt to verify bucket deletion')
    parser.add_argument(
        '--aws-profile',
        help='AWS user profile to use when making boto3 requests')
    return parser.parse_args()


# Prompt the user to verify that the bucket should be deleted
def verify_bucket(bucket_name):
    verify = input(
        'Please confirm that you want to remove bucket {} (y/n)'
        .format(bucket_name))
    if verify != 'y':
        print('Exiting')
        sys.exit(1)


# S3 requires that we empty a bucket of all object versions before deleting it
def empty_bucket(session, bucket_name):
    client = session.client('s3')

    repeat_list = True
    while repeat_list:
        list_response = client.list_object_versions(Bucket=bucket_name)
        repeat_list = (
            True
            if 'isTruncated' in list_response
            and
            list_response.get('isTruncated') is True
            else False)
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
                    Bucket=bucket_name,
                    Delete={
                        'Objects': delete_objects
                    }
                )
                print(
                    'Number object versions deleted from bucket: {}'
                    .format(len(delete_objects_response.get('Deleted', []))))
                errors = delete_objects_response.get('Errors', [])
                if errors:
                    print('Delete versions errors: {}'.format(errors))
                    sys.exit(1)


def delete_bucket(session, bucket_name):
    client = session.client('s3')

    delete_bucket_response = client.delete_bucket(Bucket=bucket_name)
    print('\nDELETE BUCKET RESPONSE')
    print(delete_bucket_response)


def main():
    args = parse_args()
    bucket_name = args.bucket_name

    if not args.yes:
        verify_bucket(bucket_name)

    session = boto3.Session(profile_name=args.aws_profile)

    empty_bucket(session, bucket_name)

    delete_bucket(session, bucket_name)


main()
