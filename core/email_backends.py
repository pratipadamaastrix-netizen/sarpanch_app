"""
Development email backends.

Django's django.core.mail.backends.filebased.EmailBackend keeps one filename
per backend instance and appends every message to that file, which makes
password-reset links hard to find. This subclass resets the file after each
close() so each send creates a new file.

Raw MIME uses quoted-printable and wraps long URLs across lines. We append
the reset URL taken from the plain-text body (before MIME wrapping) so you
can copy one line.
"""

import datetime
import os
import re
import uuid

from django.core.mail.backends.filebased import EmailBackend as DjangoFileEmailBackend


class OneEmailPerFileBackend(DjangoFileEmailBackend):
    """
    One email message → one new file under EMAIL_FILE_PATH (e.g. email_outbox/).

    Filenames look like: email_20250324-143015_a1b2c3d4e5.txt
    """

    def _get_filename(self):
        if self._fname is None:
            ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            short_id = uuid.uuid4().hex[:10]
            fname = f"email_{ts}_{short_id}.txt"
            self._fname = os.path.join(self.file_path, fname)
        return self._fname

    def write_message(self, message):
        self.stream.write(message.message().as_bytes() + b"\n")
        self.stream.write(b"-" * 79)
        self.stream.write(b"\n")
        url = self._extract_http_reset_url(message)
        if url:
            self.stream.write(
                b"\n"
                b"================================================================\n"
                b"  COPY THIS ENTIRE LINE (password reset link - one line only)\n"
                b"================================================================\n"
            )
            self.stream.write(url.encode("utf-8") + b"\n")

    @staticmethod
    def _extract_http_reset_url(message):
        """Use plain-text body before MIME; fallback to HTML href."""
        body = getattr(message, "body", None) or ""
        if isinstance(body, str):
            m = re.search(r"https?://[^\s\r\n<>\"']+", body)
            if m:
                return m.group(0).rstrip(".,);")
        for content, mimetype in getattr(message, "alternatives", None) or []:
            if mimetype == "text/html" and content:
                m = re.search(r'href=["\']([^"\']+)["\']', content)
                if m and "/reset/" in m.group(1):
                    return m.group(1).replace("&amp;", "&")
        return None

    def close(self):
        try:
            super().close()
        finally:
            # Allow the next send to pick a new file (Django's default keeps _fname forever).
            self._fname = None
