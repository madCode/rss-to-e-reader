from abc import ABC
from typing import Callable, Optional


class Module(ABC):
    def __init__(self, error_log_callback: Optional[Callable], info_log_callback: Optional[Callable]):
        """
        Parameters
        ----------
        error_log_callback: function that takes in a string and does not return, optional
            Allows user to pass in a callback for error level logs.
            Why? By making this required, it requires implementors of Module to consider
                surfacing these arguments to users in their initializers.
        info_logs: function that takes in a string and does not return, optional
            Allows user to pass in a callback for info level logs.
            Why? By making this required, it requires implementors of Module to consider
                surfacing these arguments to users in their initializers.
        """
        self._info_log_callback = info_log_callback
        self._error_log_callback = error_log_callback

    def log_error(self, log: str):
        self._error_log_callback and self._error_log_callback(log)
    
    def log_info(self, log: str):
        self._info_log_callback and self._info_log_callback(log)