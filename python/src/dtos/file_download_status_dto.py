"""
DTO for file download status.
"""

from typing import Literal

DownloadStatus = Literal["exists", "error", "success", "ignored"]


class FileDownloadStatusDTO:
    """
    Data transfer object for a single file download result.
    """

    def __init__(self, filename: str, status: DownloadStatus) -> None:
        """
        Args:
            filename: Name of the file.
            status: One of "exists", "error", or "success".
        """
        self._filename = filename
        self._status = status

    @property
    def filename(self) -> str:
        """Name of the file."""
        return self._filename

    @filename.setter
    def filename(self, value: str) -> None:
        self._filename = value

    @property
    def status(self) -> DownloadStatus:
        """Download status: exists, error, or success."""
        return self._status

    @status.setter
    def status(self, value: DownloadStatus) -> None:
        self._status = value
