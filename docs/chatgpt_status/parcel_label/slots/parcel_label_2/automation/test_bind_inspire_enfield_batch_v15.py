from __future__ import annotations

import importlib.util
import io
import shutil
import tempfile
from pathlib import Path


def load_worker():
    root = Path(tempfile.mkdtemp(prefix="pl2_v15_test_"))
    source_dir = Path(__file__).resolve().parent
    for name in ("bind_inspire_enfield_batch_v15.py", "official_hmlr_transport_v1.py"):
        shutil.copy2(source_dir / name, root / name)
    stub = '''
from pathlib import Path
base = type("Base", (), {})()
base.DOWNLOAD = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
base.REPO = Path(__file__).parent
base.RESULT = base.REPO / "result.json"
base.RECON = base.REPO / "recon.json"
base.WEB = base.REPO / "web.json"
base.TASK_VERSION = "stub"
base.main = lambda: 0
base.discover = lambda page,url: url
def _write(path,payload): path.write_text(__import__("json").dumps(payload))
base.write = _write
_original_write = _write
_PRIMARY_HOST = "use-land-property-data.service.gov.uk"
_MAX_DOWNLOAD_BYTES = 1024 * 1024
_MAX_GML_BYTES = 1024 * 1024
_MAX_ZIP_MEMBERS = 8
_MAX_ZIP_RATIO = 250.0
_DNS_PREFLIGHT = lambda: None
class Pool:
    def __init__(self): self.items=[]
    def cleanup(self):
        import os
        while self.items:
            mapped,fd,path=self.items.pop(); mapped.close(); os.close(fd); path.unlink(missing_ok=True)
_POOL = Pool()
class Streaming:
    @staticmethod
    def stream_response_to_file(response, limit):
        import tempfile
        from pathlib import Path
        handle=tempfile.NamedTemporaryFile(delete=False); data=response.read(limit+1)
        if len(data)>limit:
            handle.close(); Path(handle.name).unlink(missing_ok=True); raise RuntimeError(f"PAYLOAD_SIZE_LIMIT_EXCEEDED:{limit}")
        with handle: handle.write(data)
        return Path(handle.name)
    @staticmethod
    def normalise_download_file(raw_path, *, final_url, media_type, pool, max_gml_bytes, max_zip_members, max_zip_ratio):
        import mmap, os
        data=raw_path.read_bytes()
        if b"<html" in data.lower(): raise RuntimeError("BINARY_ROUTE_RETURNED_HTML")
        if not data.lstrip().startswith(b"<"): raise RuntimeError("UNEXPECTED_HMLR_PAYLOAD")
        fd=os.open(raw_path, os.O_RDONLY); mapped=mmap.mmap(fd,0,access=mmap.ACCESS_READ); pool.items.append((mapped,fd,raw_path)); return mapped, final_url
streaming=Streaming()
def discover(page,url): return url
'''
    (root / "bind_inspire_enfield_batch_v14.py").write_text(stub, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("worker_v15_test", root / "bind_inspire_enfield_batch_v15.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return root, module


class Headers:
    def __init__(self, media_type: str): self.media_type=media_type
    def get_content_type(self): return self.media_type


class Response(io.BytesIO):
    def __init__(self, payload: bytes, final_url: str, media_type: str):
        super().__init__(payload); self._url=final_url; self.headers=Headers(media_type)
    def geturl(self): return self._url
    def __enter__(self): return self
    def __exit__(self,*args): self.close(); return False


class Opener:
    def __init__(self, response_factory): self.response_factory=response_factory
    def open(self, request, timeout): return self.response_factory()


def expect_error(fragment: str, fn):
    try: fn()
    except RuntimeError as exc: assert fragment in str(exc), exc
    else: raise AssertionError(fragment)


def main() -> int:
    root, worker = load_worker(); checks=0
    try:
        assert worker.base.TASK_VERSION == "7.4-trusted-hmlr-redirect-and-origin-pinning-batch"; checks += 1
        assert worker.base.WEB.name == "progress_wave23_exact_result_latest.json"; checks += 1
        worker._OPENER = Opener(lambda: Response(b"<html>index</html>", worker.base.DOWNLOAD, "text/html"))
        payload, final = worker.fetch(worker.base.DOWNLOAD, 10, 1)
        assert payload.startswith(b"<html") and final == worker.base.DOWNLOAD; checks += 1
        gml = b"<gml:FeatureCollection xmlns:gml='http://www.opengis.net/gml/3.2'/>"
        official_final = "https://inspire.landregistry.gov.uk/download/enfield.gml"
        worker._OPENER = Opener(lambda: Response(gml, official_final, "application/gml+xml"))
        mapped, final = worker.fetch("https://use-land-property-data.service.gov.uk/file/enfield.gml", 10, 1)
        assert bytes(mapped[:4]) == b"<gml" and final == official_final; checks += 1
        worker._POOL.cleanup()
        expect_error("UNTRUSTED_HOST", lambda: worker.fetch("https://evil.example/enfield.gml", 10, 1)); checks += 1
        expect_error("PORT_NOT_443", lambda: worker.fetch("https://use-land-property-data.service.gov.uk:444/enfield.gml", 10, 1)); checks += 1
        worker._OPENER = Opener(lambda: Response(gml, "https://evil.example/enfield.gml", "application/gml+xml"))
        expect_error("UNTRUSTED_HOST", lambda: worker.fetch("https://use-land-property-data.service.gov.uk/file/enfield.gml", 10, 1)); checks += 1
        worker._OPENER = Opener(lambda: Response(b"not html", worker.base.DOWNLOAD, "application/octet-stream"))
        expect_error("DOWNLOAD_INDEX_UNEXPECTED_MEDIA_TYPE", lambda: worker.fetch(worker.base.DOWNLOAD, 10, 1)); checks += 1
        worker._MAX_INDEX_BYTES = 8; worker._OPENER = Opener(lambda: Response(b"x"*9, worker.base.DOWNLOAD, "text/html"))
        expect_error("RESPONSE_SIZE_LIMIT_EXCEEDED:8", lambda: worker.fetch(worker.base.DOWNLOAD, 10, 1)); checks += 1
        worker._MAX_DOWNLOAD_BYTES = 8; worker._OPENER = Opener(lambda: Response(b"x"*9, official_final, "application/octet-stream"))
        expect_error("PAYLOAD_SIZE_LIMIT_EXCEEDED:8", lambda: worker.fetch("https://use-land-property-data.service.gov.uk/file/enfield.gml", 10, 1)); checks += 1
        assert worker.main() == 0; checks += 1
    finally:
        try: worker._POOL.cleanup()
        except Exception: pass
        shutil.rmtree(root, ignore_errors=True)
    print(f"PARCEL_LABEL_2_V15_WRAPPER_TESTS={checks}/{checks}")
    print("FINAL_READY=false")
    return 0


if __name__ == "__main__": raise SystemExit(main())
