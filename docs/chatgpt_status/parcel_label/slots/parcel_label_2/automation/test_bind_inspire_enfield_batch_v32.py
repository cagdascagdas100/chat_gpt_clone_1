from __future__ import annotations

import hashlib
import importlib.util
import tempfile
from pathlib import Path

SOURCE_ROOT = Path(__file__).parent


def expect(fragment: str, fn) -> None:
    try:
        fn()
    except Exception as exc:
        assert fragment in str(exc), exc
    else:
        raise AssertionError(f"expected {fragment}")


def main() -> int:
    checks = 0
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "bind_inspire_enfield_batch_v32.py").write_text(
            (SOURCE_ROOT / "bind_inspire_enfield_batch_v32.py").read_text(encoding="utf-8"), encoding="utf-8"
        )
        (root / "bind_inspire_enfield_batch_v31.py").write_text('''from pathlib import Path\nclass Base:\n    REPO=Path("/tmp/repo")\n    RESULT=Path("/tmp/repo/result.json")\n    RECON=Path("/tmp/repo/recon.json")\n    WEB=Path("/tmp/repo/old.json")\n    TASK_VERSION="old"\n    def __init__(self): self.sha256=lambda payload: hashlib.sha256(bytes(payload)).hexdigest(); self.main=lambda:0\nimport hashlib\nbase=Base()\nclass Pool:\n    def __init__(self): self.cleaned=False\n    def cleanup(self): self.cleaned=True\n_POOL=Pool()\ndef _original_write(path,payload): return (path,payload)\n''', encoding='utf-8')
        (root / "validate_inspire_cadastral_parcel_v19.py").write_text('''from pathlib import Path\ndef geometry(x): return {"geometry":True}\nLAST=None\ndef parse(path,target_ids,*,expected_sha256):\n    global LAST\n    LAST=(Path(path),set(target_ids),expected_sha256)\n    return {x:[] for x in target_ids},{"expected":expected_sha256}\n''', encoding='utf-8')
        spec = importlib.util.spec_from_file_location("worker_v32_test", root / "bind_inspire_enfield_batch_v32.py")
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)

        assert module.base.TASK_VERSION == "9.1-download-sha256-to-parser-source-stability-batch"; checks += 1
        assert str(module.EXACT_WEB).endswith("progress_wave40_exact_result_latest.json"); checks += 1
        assert module.base.geometry(None)["geometry"] is True; checks += 1
        expect("XML_EXPECTED_SHA256_NOT_CAPTURED", lambda: module.parse(Path("x"), {"1"})); checks += 1
        payload = b"abc"
        digest = module.sha256(payload)
        assert digest == hashlib.sha256(payload).hexdigest(); checks += 1
        expect("XML_EXPECTED_SHA256_ALREADY_CAPTURED", lambda: module.sha256(payload)); checks += 1
        found, summary = module.parse(Path("x.gml"), {"1", "2"})
        assert set(found) == {"1", "2"}; checks += 1
        assert summary["expected"] == digest; checks += 1
        assert module.validator.LAST[2] == digest; checks += 1
        expect("XML_EXPECTED_SHA256_NOT_CAPTURED", lambda: module.parse(Path("x"), {"1"})); checks += 1
        expect("PARCEL_LABEL_2_WRITE_PATH_NOT_ALLOWED", lambda: module.write(Path("/tmp/repo/no.json"), {})); checks += 1
        module._expected_gml_sha256 = None
        module._original_sha256 = lambda payload: "bad"
        expect("XML_DOWNLOAD_SHA256_INVALID", lambda: module.sha256(b"x")); checks += 1
    assert checks == 12, checks
    print("PARCEL_LABEL_2_STABLE_WORKER_TESTS=12/12")
    print("FINAL_READY=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
