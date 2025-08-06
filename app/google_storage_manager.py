from flask import current_app
from google.cloud import storage
from io import BytesIO
import re
import tarfile


class GoogleStorageManager(object):

    @classmethod
    def get_bucket(cls, bucket_name):
        if getattr(cls, 'client', None) is None:
            # for local development, make sure that your local gcloud config has access to the gcs bucket
            # optionally gcloud config configurations create <profile name>
            # gcloud config set account <user@org>
            # gcloud config set project <project>
            cls.client = storage.Client()
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

    @staticmethod
    def get_tar_buffer(path: str):
        # file is located in Google Cloud
        # file is expected to be a tar.gz of the contents of the model folder (not the folder itself)
        match = re.match(r"gs://([^/]+)/(.+)$", path)
        bucket_name = match.group(1)
        blob_name = match.group(2)
        model_buffer = GoogleStorageManager.get_filename(blob_name, bucket_name)
        return tarfile.open(fileobj=model_buffer)
