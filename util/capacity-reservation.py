#! /usr/bin/env python3

"""Capacity reservation management

Create or cancel AWS EC2 capacity reservations.
"""
import argparse
import boto3
import json
import sys


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        '--aws-profile',
        help='AWS user profile to use when making boto3 requests')
    parent_parser.add_argument(
        '--zone',
        default='us-east-1a',
        help='Availability zone to reserve in')
    parent_parser.add_argument(
        '--dry-run',
        help='Show the aws command that would be run, but don\'t run it',
        action='store_true')

    subparsers = parser.add_subparsers(title='Commands', dest='command')
    subparsers.required = True

    # Create Command
    create_parser = subparsers.add_parser(
        'create',
        parents=[parent_parser],
        help='Create a capacity reservation')
    create_parser.add_argument(
        '--instance-type',
        required=True,
        help='Instance type to reserve')
    create_parser.add_argument(
        '--count',
        required=True,
        type=int,
        help='Number of instances to reserve')
    tag_group = create_parser.add_mutually_exclusive_group(required=True)
    tag_group.add_argument(
        '--tags',
        help='Path to tag specification json')
    tag_group.add_argument(
        '--instance-id',
        help='AWS instance id for deriving tagsw')

    # Cancel Command
    cancel_parser = subparsers.add_parser(
        'cancel',
        parents=[parent_parser],
        help='Create a capacity reservation')
    cancel_parser.add_argument(
        'reservation_id',
        help='The id of the capacity reservation to be cancelled')

    return parser.parse_args()


def _retrieve_tags(client, instance_id):
    """Retrieve tags from an EC2 instance"""
    response = client.describe_tags(
        Filters=[
            {
                'Name': 'resource-id',
                'Values': [instance_id]
            }
        ]
    )
    if 'Tags' in response and len(response['Tags']) > 0:
        tags = [
            {'Value': tag['Value'], 'Key': tag['Key']}
            for tag in response['Tags']
            if tag['Key'] in ['Department', 'Name', 'Project', 'SubProject']
            ]
        return tags
    else:
        print(f'Problem retrieving tags: {response}')
        sys.exit(1)


def _resolve_tags(client, args):
    """If there's a tag file path in arguments, load it, otherwise,
    assume this is an EC2 instance and try to pull its tags"""
    if args.tags:
        with open(args.tags) as json_file:
            try:
                return json.load(json_file)
            except ValueError:
                print(f'Loading tags from {args.tags} failed')
                sys.exit(1)
    else:
        print('No tags supplied. Attempting to retrieve tags from EC2.')
        return _retrieve_tags(client, args.instance_id)


def create_reservation(client, instance_type, zone, count, tags, dry_run):
    """Create a reservation for on-demand AWS EC2 instances"""
    print(
        'Creating reservation for {} {} in {}'
        .format(count, instance_type, zone))

    response = client.create_capacity_reservation(
        InstancePlatform='Linux/UNIX',
        InstanceType=instance_type,
        AvailabilityZone=zone,
        InstanceCount=count,
        TagSpecifications=[
            {
                'ResourceType': 'capacity-reservation',
                'Tags': tags,
            }
        ],
        DryRun=dry_run
    )
    print(response)


def cancel_reservation(client, reservation_id, dry_run):
    """Cancel a reservation with a reservation id"""
    print('Canceling reservation {}'.format(reservation_id))
    response = client.cancel_capacity_reservation(
        CapacityReservationId=reservation_id,
        DryRun=dry_run
    )
    print(response)


def main():
    args = parse_args()

    region = args.zone[:-1]
    session = boto3.Session(profile_name=args.aws_profile)
    client = session.client('ec2', region_name=region)

    if args.command == 'create':
        tags = _resolve_tags(client, args)
        create_reservation(
            client,
            args.instance_type,
            args.zone,
            args.count,
            tags,
            args.dry_run)
    elif args.command == 'cancel':
        cancel_reservation(
            client,
            args.reservation_id,
            args.dry_run)
    else:
        print('Something when wrong: {}'.format(args))


main()
