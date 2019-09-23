#! /usr/bin/env python3

"""Capacity reservation management

Create or cancel AWS EC2 capacity reservations.
"""
import argparse
import boto3


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

    # Cancel Command
    cancel_parser = subparsers.add_parser(
        'cancel',
        parents=[parent_parser],
        help='Create a capacity reservation')
    cancel_parser.add_argument(
        'reservation_id',
        help='The id of the capacity reservation to be cancelled')

    return parser.parse_args()


def create_reservation(client, instance_type, zone, count, dry_run):
    """Create a reservation for on-demand AWS EC2 instances"""
    print(
        'Creating reservation for {} {} in {}'
        .format(count, instance_type, zone))
    response = client.create_capacity_reservation(
        InstancePlatform='Linux/UNIX',
        InstanceType=instance_type,
        AvailabilityZone=zone,
        InstanceCount=count,
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
        create_reservation(
            client,
            args.instance_type,
            args.zone,
            args.count,
            args.dry_run)
    elif args.command == 'cancel':
        cancel_reservation(
            client,
            args.reservation_id,
            args.dry_run)
    else:
        print('Something when wrong: {}'.format(args))


main()
