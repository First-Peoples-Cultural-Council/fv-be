import logging
import os
import re
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger(__name__)

TIMESTAMP_REGEX_STRING = r"\d{4}-\d{2}-\d{2}-\d{2}:\d{2}:\d{2}.\d{6}"

EXPORT_STORAGE_DIRECTORY = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "export_data"
)


def get_client():
    """
    Gets a boto3 AWS client which can be used to access various AWS services.
    """

    if os.getenv("AWS_ACCESS_KEY_ID") is None:
        logger.error(
            'Please set the "AWS_ACCESS_KEY_ID" environment variable to access AWS.'
        )
        return False
    if os.getenv("AWS_SECRET_ACCESS_KEY") is None:
        logger.error(
            'Please set the "AWS_SECRET_ACCESS_KEY" environment variable to access AWS.'
        )
        return False

    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )


def get_aws_resource():
    """
    Gets a boto3 AWS session which can be used to access various AWS services.

    :return: A boto3 AWS sessions if the environment variables are set, else false.
    """

    if os.getenv("AWS_ACCESS_KEY_ID") is None:
        logger.error(
            'Please set the "AWS_ACCESS_KEY_ID" environment variable to access AWS.'
        )
        return False
    if os.getenv("AWS_SECRET_ACCESS_KEY") is None:
        logger.error(
            'Please set the "AWS_SECRET_ACCESS_KEY" environment variable to access AWS.'
        )
        return False

    if os.getenv("DATA_S3_BUCKET") is None:
        logger.error(
            'Please set the "DATA_S3_BUCKET" environment variable to access AWS.'
        )
        return False

    session = boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

    return session.resource("s3")


def get_bucket():
    s3 = get_aws_resource()
    if s3 is False:
        logger.error("Could not get AWS session.")
        return False

    bucket = s3.Bucket(os.getenv("DATA_S3_BUCKET"))
    if bucket is False:
        logger.error("Could not get AWS Bucket.")
        return False

    return bucket


def download_file_from_s3(key):
    """
    Downloads a single file from the S3 bucket specified by the DATA_S3_BUCKET environment variable given an
    object key. Files are stored in the "scripts/export_data/<timestamp for the file>/" directory.

    :param key: The object key string for the file.
    :return: True if the file was successfully downloaded, else False.
    """

    if key is None:
        logger.error("Missing key for file to download.")
        return False

    file_name = re.search(r"/(.{1,1024}\.csv)$", key).group(1)
    timestamp = re.search(TIMESTAMP_REGEX_STRING, file_name).group(0)

    client = get_aws_resource().meta.client
    if not client:
        logger.error(
            f"Could not get client. File ({file_name}) was not downloaded successfully."
        )
        return False

    storage_directory = os.path.join(EXPORT_STORAGE_DIRECTORY, timestamp)
    if not os.path.exists(storage_directory):
        os.makedirs(storage_directory)
    try:
        client.download_file(
            os.getenv("DATA_S3_BUCKET"), key, f"{storage_directory}/{file_name}"
        )
        logger.info(
            f"Downloaded file ({file_name}) to ({storage_directory}) successfully."
        )
    except ClientError as e:
        logger.error(f"Object ({key}) was not downloaded from AWS successfully. {e}")
        return False
    return True


def download_directory_from_s3(directory_name):
    """
    Downloads all files from the S3 bucket given a directory name (the timestamp that the export was created at).
    Files are stored in the "scripts/export_data/<timestamp for the files>/" directory.

    :param directory_name: The name of the directory to download all files from (the directory name is a timestamp
    string in isoformat).
    :return: True if the files were successfully downloaded, else False.
    """

    bucket = get_bucket()

    objects = bucket.objects.filter(Prefix=directory_name)
    for file in objects:
        download_file_from_s3(file.key)
    return True


def download_exports_after_timestamp(timestamp):
    """
    Downloads all files from the S3 bucket that have a timestamp greater or equal to the input timestamp. Files are
    stored in the "scripts/export_data/<timestamp for the files>/" directory.

    :param timestamp: The timestamp in isoformat specifying the time cutoff. All files with a timestamp after this
    timestamp will be downloaded.
    :return: True if the files were successfully downloaded, else False.
    """

    bucket = get_bucket()

    objects = bucket.objects.all()

    objects_after_timestamp = [
        file
        for file in objects
        if datetime.fromisoformat(re.search(TIMESTAMP_REGEX_STRING, file.key).group(0))
        >= datetime.fromisoformat(timestamp)
    ]

    for file in objects_after_timestamp:
        download_file_from_s3(file.key)
    return True


def download_latest_exports():
    """
    Downloads all files from the S3 bucket that have the single latest timestamp in their key (directory). Files are
    stored in the "scripts/export_data/<timestamp for the files>/" directory.

    :return: True if the files were successfully downloaded, else False.
    """

    bucket = get_bucket()

    objects = bucket.objects.all()

    latest_timestamp = None
    output_keys = []
    for file in objects:
        timestamp = re.search(TIMESTAMP_REGEX_STRING, file.key).group(0)
        if latest_timestamp is None or datetime.fromisoformat(
            timestamp
        ) > datetime.fromisoformat(latest_timestamp):
            latest_timestamp = timestamp
            output_keys.clear()
            output_keys.append(file.key)
        elif timestamp == latest_timestamp:
            output_keys.append(file.key)

    for key in output_keys:
        download_file_from_s3(key)
    return True


def file_in_aws(path, bucket=settings.AWS_STORAGE_BUCKET_NAME):
    """
    Check if a file path exists in an S3 bucket

    :param path: AWS file path to check
    :param bucket: The name of the S3 bucket to check (defaults to the MEDIA_UPLOAD_S3_BUCKET environment variable)
    :return: True if file exists in the bucket, else false
    """
    if bucket is None:
        logger.error(
            'Please set the "MEDIA_UPLOAD_S3_BUCKET" environment variable to access AWS.'
        )

    try:
        client = get_client()
        if client is False:
            logger.error("Could not get AWS client.")
            return False

        client.get_object(Bucket=bucket, Key=path)
        logger.warning(f"File already exists in S3 bucket ({bucket}) at path ({path}).")
    except ClientError:
        return False
    return True
