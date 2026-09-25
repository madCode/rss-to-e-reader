from base_classes.sender import Sender
import os
import shutil
from typing import Callable, Optional

"""
FolderSender copies the file into a folder that syncs to your e-reader. No email involved. For example:
- Kobo: the Dropbox or Google Drive folder linked in the Kobo's settings (Kobo imports new files from it).
- KOReader: a folder synced with Syncthing, or served by KOReader's cloud storage/OPDS plugins.
- Calibre: its "Add books from a folder automatically" folder, then let Calibre send to your device.
- Boox, PocketBook, ...: whichever cloud folder the device syncs.
"""
class FolderSender(Sender):
    def __init__(self, folder: str, keep_last: int = -1,
                 error_log_callback: Optional[Callable] = print, info_log_callback: Optional[Callable] = print):
        """
        Parameters
        ----------
        folder: str
            The folder to copy files into. Created if it doesn't exist.
        keep_last: int, optional
            If positive, delete older files with the same extension so only this many remain. Defaults to -1 (keep all).
        """
        super().__init__(error_log_callback, info_log_callback)
        self.folder = folder
        self.keep_last = keep_last

    def _prune(self, extension: str):
        if self.keep_last <= 0:
            return
        files = sorted(
            (os.path.join(self.folder, f) for f in os.listdir(self.folder) if f.endswith(extension)),
            key=os.path.getmtime, reverse=True)
        for old in files[self.keep_last:]:
            os.remove(old)
            self.log_info(f'Removed old file {old}')

    def send(self, filepath: str, subject: str = "", body: str = "") -> bool:
        try:
            os.makedirs(self.folder, exist_ok=True)
            destination = os.path.join(self.folder, os.path.basename(filepath))
            shutil.copy2(filepath, destination)
            self.log_info(f'Copied {filepath} to {destination}')
            self._prune(os.path.splitext(filepath)[1])
            return True
        except Exception as e:
            self.log_error(f'Unable to copy {filepath} to {self.folder}: {e}')
            return False
