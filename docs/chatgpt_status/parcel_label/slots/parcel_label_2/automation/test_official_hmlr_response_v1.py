from __future__ import annotations

import io
import tempfile
import unittest
from email.message import Message
from pathlib import Path

import official_hmlr_response_v1 as subject


class Response:
    def __init__(self, body=b"abc", *, status=200, headers=None):
        self._stream = io.BytesIO(body)
        self.status = status
        self.headers = headers if headers is not None else Message()

    def read(self, size=-1):
        return self._stream.read(size)

    def getcode(self):
        return self.status


def headers(**items):
    message = Message()
    for key, value in items.items():
        if isinstance(value, list):
            for item in value:
                message[key.replace("_", "-")] = item
        else:
            message[key.replace("_", "-")] = value
    return message


class ResponseIntegrityTests(unittest.TestCase):
    def test_200_without_length_passes(self):
        meta = subject.validate_response_integrity(Response(), limit=10)
        self.assertEqual(meta.status, 200)
        self.assertIsNone(meta.content_length)

    def test_206_partial_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "STATUS_NOT_200:206"):
            subject.validate_response_integrity(Response(status=206), limit=10)

    def test_204_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "STATUS_NOT_200:204"):
            subject.validate_response_integrity(Response(status=204), limit=10)

    def test_missing_headers_rejected(self):
        response = Response()
        response.headers = None
        with self.assertRaisesRegex(RuntimeError, "HEADERS_MISSING"):
            subject.validate_response_integrity(response, limit=10)

    def test_single_content_length(self):
        meta = subject.validate_response_integrity(
            Response(headers=headers(Content_Length="3")), limit=10
        )
        self.assertEqual(meta.content_length, 3)

    def test_duplicate_equal_content_length_allowed(self):
        meta = subject.validate_response_integrity(
            Response(headers=headers(Content_Length=["3", "3"])), limit=10
        )
        self.assertEqual(meta.content_length, 3)

    def test_comma_equal_content_length_allowed(self):
        meta = subject.validate_response_integrity(
            Response(headers=headers(Content_Length="3, 3")), limit=10
        )
        self.assertEqual(meta.content_length, 3)

    def test_conflicting_content_length_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "CONTENT_LENGTH_CONFLICT"):
            subject.validate_response_integrity(
                Response(headers=headers(Content_Length="3, 4")), limit=10
            )

    def test_invalid_content_length_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "CONTENT_LENGTH_INVALID"):
            subject.validate_response_integrity(
                Response(headers=headers(Content_Length="+3")), limit=10
            )

    def test_content_length_above_limit_rejected_before_read(self):
        with self.assertRaisesRegex(RuntimeError, "CONTENT_LENGTH_LIMIT_EXCEEDED:2"):
            subject.validate_response_integrity(
                Response(headers=headers(Content_Length="3")), limit=2
            )

    def test_content_range_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "CONTENT_RANGE_FORBIDDEN"):
            subject.validate_response_integrity(
                Response(headers=headers(Content_Range="bytes 0-2/10")), limit=10
            )

    def test_chunked_allowed_without_content_length(self):
        meta = subject.validate_response_integrity(
            Response(headers=headers(Transfer_Encoding="chunked")), limit=10
        )
        self.assertEqual(meta.transfer_encoding, "chunked")

    def test_non_chunked_transfer_encoding_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "TRANSFER_ENCODING_UNSUPPORTED"):
            subject.validate_response_integrity(
                Response(headers=headers(Transfer_Encoding="gzip")), limit=10
            )

    def test_conflicting_transfer_encodings_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "TRANSFER_ENCODING_CONFLICT"):
            subject.validate_response_integrity(
                Response(headers=headers(Transfer_Encoding=["chunked", "gzip"])), limit=10
            )

    def test_content_length_and_transfer_encoding_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "LENGTH_AND_TRANSFER_ENCODING_CONFLICT"):
            subject.validate_response_integrity(
                Response(headers=headers(Content_Length="3", Transfer_Encoding="chunked")),
                limit=10,
            )

    def test_identity_content_encoding_allowed(self):
        meta = subject.validate_response_integrity(
            Response(headers=headers(Content_Encoding="identity")), limit=10
        )
        self.assertEqual(meta.content_encoding, "identity")

    def test_compressed_content_encoding_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "CONTENT_ENCODING_UNSUPPORTED:gzip"):
            subject.validate_response_integrity(
                Response(headers=headers(Content_Encoding="gzip")), limit=10
            )

    def test_conflicting_content_encodings_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "CONTENT_ENCODING_CONFLICT"):
            subject.validate_response_integrity(
                Response(headers=headers(Content_Encoding=["identity", "gzip"])), limit=10
            )

    def test_read_bounded_complete_exact_length(self):
        response = Response(b"abc", headers=headers(Content_Length="3"))
        meta = subject.validate_response_integrity(response, limit=10)
        self.assertEqual(
            subject.read_bounded_complete(response, limit=10, metadata=meta), b"abc"
        )

    def test_read_bounded_complete_truncated_rejected(self):
        response = Response(b"abc", headers=headers(Content_Length="4"))
        meta = subject.validate_response_integrity(response, limit=10)
        with self.assertRaisesRegex(RuntimeError, "BODY_LENGTH_MISMATCH:3:4"):
            subject.read_bounded_complete(response, limit=10, metadata=meta)

    def test_read_bounded_complete_over_limit_rejected(self):
        response = Response(b"abcd")
        meta = subject.validate_response_integrity(response, limit=3)
        with self.assertRaisesRegex(RuntimeError, "SIZE_LIMIT_EXCEEDED:3"):
            subject.read_bounded_complete(response, limit=3, metadata=meta)

    def test_empty_body_rejected(self):
        response = Response(b"")
        meta = subject.validate_response_integrity(response, limit=3)
        with self.assertRaisesRegex(RuntimeError, "BODY_EMPTY"):
            subject.read_bounded_complete(response, limit=3, metadata=meta)

    def test_verify_file_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body"
            path.write_bytes(b"abc")
            meta = subject.ResponseIntegrity(200, 3, None, None)
            self.assertEqual(subject.verify_file_complete(path, meta), 3)

    def test_verify_file_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body"
            path.write_bytes(b"abc")
            meta = subject.ResponseIntegrity(200, 4, None, None)
            with self.assertRaisesRegex(RuntimeError, "BODY_LENGTH_MISMATCH:3:4"):
                subject.verify_file_complete(path, meta)


if __name__ == "__main__":
    unittest.main(verbosity=2)
