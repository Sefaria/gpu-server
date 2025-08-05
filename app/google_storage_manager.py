from flask import current_app
from google.cloud import storage
from io import BytesIO


class GoogleStorageManager(object):

    @classmethod
    def get_bucket(cls, bucket_name):
        if getattr(cls, 'client', None) is None:
            # for local development, change below line to cls.client = storage.Client(project="production-deployment")
            cls.client = storage.Client.from_service_account_json()
        bucket = cls.client.get_bucket(bucket_name)
        return bucket

    @classmethod
    def get_filename(cls, filename, bucket_name):
        """
        Downloads `filename` and returns a file-like object with the data
        @param filename: name of file in `bucket_name`
        @param bucket_name: name of bucket
        @return: file-like object with the data
        """
        bucket = cls.get_bucket(bucket_name)
        blob = bucket.blob(filename)
        return BytesIO(blob.download_as_bytes())
