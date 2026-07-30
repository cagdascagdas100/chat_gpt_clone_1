from __future__ import annotations
import hashlib, importlib.util, io, json, shutil, tempfile, zipfile
from pathlib import Path

def blob(data):return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()
def expect(fragment,fn):
    try:fn()
    except RuntimeError as exc:assert fragment in str(exc),exc
    else:raise AssertionError(fragment)
class Headers:
    def __init__(self,value):self.value=value
    def get_content_type(self):return self.value
class Response(io.BytesIO):
    def __init__(self,data,url,media):super().__init__(data);self.url=url;self.headers=Headers(media)
    def geturl(self):return self.url
    def __enter__(self):return self
    def __exit__(self,*args):self.close();return False
class Opener:
    def __init__(self,factory):self.factory=factory
    def open(self,request,timeout):return self.factory()
def load_worker():
    root=Path(tempfile.mkdtemp(prefix="pl2_v14_"));src=Path(__file__).resolve().parent
    shutil.copy2(src/"bind_inspire_enfield_batch_v14.py",root/"bind_inspire_enfield_batch_v14.py");shutil.copy2(src/"stream_inspire_payload_v1.py",root/"stream_inspire_payload_v1.py")
    features=[{"type":"Feature","properties":{"parcel_id":f"parcel_{i}","row_no":i,"hmlr_inspire_id":str(46000000+i),"hmlr_lon":0,"hmlr_lat":0,"hmlr_area_m2":1,"london_authority":"Enfield"}} for i in range(1,13)]
    raw=json.dumps({"features":features},separators=(",", ":")).encode();(root/"security.geojson").write_bytes(raw)
    (root/"bind_inspire_enfield_batch_v13.py").write_text(f'''from pathlib import Path
base=type("Base",(),{{}})();base.DOWNLOAD="https://use-land-property-data.service.gov.uk/datasets/inspire/download";base.SOURCE=Path(__file__).with_name("security.geojson");base.BLOB="{blob(raw)}";base.COUNT=12;base.TARGET_IDS=[f"parcel_{{i}}" for i in range(1,13)];base.REPO=Path(__file__).parent;base.RESULT=base.REPO/"r.json";base.RECON=base.REPO/"c.json";base.WEB=base.REPO/"w.json";base.main=lambda:0;base.sha256=lambda p:__import__("hashlib").sha256(p).hexdigest();base.write=lambda p,v:None;base.discover=lambda p,u:u
_original_write=lambda p,v:None
index_calls=[]
def fetch(url,timeout,attempts=2):index_calls.append(url);return b"<html>index</html>",url
def discover(page,url):return url
def _bounded_dns_preflight():return None
previous=None
''')
    spec=importlib.util.spec_from_file_location("v14_test",root/"bind_inspire_enfield_batch_v14.py");module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return root,module

def main():
    root,w=load_worker();checks=0
    try:
        rows,summary=w.canonical();assert len(rows)==12 and summary["canonical_streaming_mmap"];checks+=1
        assert w.base.TASK_VERSION=="7.3-streaming-canonical-and-download-batch";checks+=1
        assert w.base.WEB.name=="progress_wave22_exact_result_latest.json";checks+=1
        index,url=w.fetch(w.base.DOWNLOAD,10,1);assert index.startswith(b"<html") and url==w.base.DOWNLOAD;checks+=1
        gml=b"<gml:FeatureCollection xmlns:gml='http://www.opengis.net/gml/3.2'><gml:featureMember/></gml:FeatureCollection>"
        w._OPENER=Opener(lambda:Response(gml,"https://use-land-property-data.service.gov.uk/f/enfield.gml","application/gml+xml"));mapped,final=w.fetch("https://use-land-property-data.service.gov.uk/f/enfield.gml",10,1);assert bytes(mapped[:4])==b"<gml" and final.endswith("enfield.gml");checks+=1
        assert w.base.sha256(mapped)==hashlib.sha256(gml).hexdigest();checks+=1;w._POOL.cleanup()
        buffer=io.BytesIO();
        with zipfile.ZipFile(buffer,"w",zipfile.ZIP_DEFLATED) as z:z.writestr("data/enfield.gml",gml)
        w._OPENER=Opener(lambda:Response(buffer.getvalue(),"https://use-land-property-data.service.gov.uk/f/enfield.zip","application/zip"));mapped,final=w.fetch("https://use-land-property-data.service.gov.uk/f/enfield.zip",10,1);assert final.endswith("#data/enfield.gml") and w.base.sha256(mapped)==hashlib.sha256(gml).hexdigest();checks+=1;w._POOL.cleanup()
        w._OPENER=Opener(lambda:Response(b"<html>bad</html>","https://use-land-property-data.service.gov.uk/f/x.gml","text/html"));expect("BINARY_ROUTE_RETURNED_HTML",lambda:w.fetch("https://use-land-property-data.service.gov.uk/f/x.gml",10,1));checks+=1
        expect("OFFICIAL_DOWNLOAD_URL_CROSS_ORIGIN",lambda:w.fetch("https://evil.example/x.gml",10,1));checks+=1
        w._MAX_DOWNLOAD_BYTES=8;w._OPENER=Opener(lambda:Response(b"x"*9,"https://use-land-property-data.service.gov.uk/f/x.gml","application/octet-stream"));expect("PAYLOAD_SIZE_LIMIT_EXCEEDED:8",lambda:w.fetch("https://use-land-property-data.service.gov.uk/f/x.gml",10,1));checks+=1
        w._POOL.cleanup();assert not w._POOL._items;checks+=1
        assert w.main()==0;checks+=1
    finally:
        try:w._POOL.cleanup()
        except Exception:pass
        shutil.rmtree(root,ignore_errors=True)
    print(f"PARCEL_LABEL_2_V14_WRAPPER_TESTS={checks}/{checks}");print("FINAL_READY=false");return 0
if __name__=="__main__":raise SystemExit(main())
