"""
AWS integration for S3 and other services used by the data lake pipeline.
"""
from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.config import Config


class AWSIntegration:
    """
    Centralizes AWS client creation and configuration for the pipeline
    (e.g. S3 for reading/writing datalake artifacts).
    """

    def __init__(
        self,
        region_name: str | None = None,
        config: Config | None = None,
    ) -> None:
        """
        Initialize AWS integration.

        Args:
            region_name: AWS region (defaults to session/default if not set).
            config: Optional botocore Config for timeouts, retries, etc.
        """
        self._region_name = region_name
        self._config = config or Config()
        self._session: boto3.Session | None = None

    @property
    def session(self) -> boto3.Session:
        """Lazy boto3 session."""
        if self._session is None:
            kwargs = {}
            if self._region_name:
                kwargs["region_name"] = self._region_name
            self._session = boto3.Session(**kwargs)
        return self._session

    def s3_client(self):
        """S3 client for the current session and config."""
        return self.session.client("s3", config=self._config)

    def send_to_s3_bucket(
        self,
        bucket: str,
        key: str,
        body: str | Path | bytes | BinaryIO,
        content_type: str | None = None,
    ) -> str:
        """
        Upload data to an S3 bucket.

        Args:
            bucket: S3 bucket name.
            key: S3 object key (path within the bucket).
            body: Source of data: local file path (str or Path), raw bytes, or file-like object.
            content_type: Optional Content-Type for the object (e.g. "text/csv", "application/json").

        Returns:
            S3 URI of the uploaded object (s3://bucket/key).

        Raises:
            FileNotFoundError: If body is a path and the file does not exist.
        """
        s3 = self.s3_client()
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        if isinstance(body, (str, Path)):
            path = Path(body)
            if not path.is_file():
                raise FileNotFoundError(f"File not found: {path}")
            kwargs = {"ExtraArgs": extra_args} if extra_args else {}
            s3.upload_file(str(path), bucket, key, **kwargs)
        elif isinstance(body, bytes):
            s3.put_object(Bucket=bucket, Key=key, Body=body, **extra_args)
        else:
            kwargs = {"ExtraArgs": extra_args} if extra_args else {}
            s3.upload_fileobj(body, bucket, key, **kwargs)

        return f"s3://{bucket}/{key}"
