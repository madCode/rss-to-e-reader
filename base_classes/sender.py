from abc import abstractmethod
from base_classes.module import Module
from typing import Callable, Optional

"""
A Sender does the following:
- takes the path of a file created by a FileCreator
- delivers it to the user's e-reader (by email, by copying it to a synced folder, ...)
"""
class Sender(Module):
    def __init__(self, error_log_callback: Optional[Callable], info_log_callback: Optional[Callable]):
        """
        Parameters
        ----------
        error_log_callback: function that takes in a string and does not return, optional
            Allows user to pass in a callback for error level logs.
        info_log_callback: function that takes in a string and does not return, optional
            Allows user to pass in a callback for info level logs.
        """
        super().__init__(error_log_callback, info_log_callback)

    @abstractmethod
    def send(self, filepath: str, subject: str = "", body: str = "") -> bool:
        """
        Parameters
        ----------
        filepath: str
            Path to the file to deliver, including its extension.
        subject: str, optional
            Subject line, for Senders that use one. Defaults to the file's name.
        body: str, optional
            Message body, for Senders that use one.

        Returns
        -------
        True if the file was delivered, False otherwise. Failures are reported through the error log callback.
        """
        pass
