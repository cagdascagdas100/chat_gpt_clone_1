# AAYS ChatGPT Runner V4 Result

## Task
TerraYield safe API root-cause recovery and score hold

## Task ID
terrayield-verification-035-api-rootcause-recovery

## Progress
99%

## Action


## Time
05/04/2026 06:15:09

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Timeout Seconds
1200

## Exit Code
0

## Output
``text
[0 s] TASK: TerraYield verification 035 API root-cause recovery
[0 s] MODE: safe concise diagnostics; no compose config dump; no env dump; targeted recovery only
[5 s] API_HEALTH_INITIAL=False
[5 s] --- docker ps api/db concise ---
NAMES                     STATUS                        PORTS
terrayield_land_api       Exited (255) 34 minutes ago   
terrayield_land_postgis   Up 8 hours                    0.0.0.0:55460->5432/tcp, [::]:55460->5432/tcp

[5 s] docker ps api/db concise EXIT=0
NAMES                     STATUS                        PORTS
terrayield_land_api       Exited (255) 34 minutes ago   
terrayield_land_postgis   Up 8 hours                    0.0.0.0:55460->5432/tcp, [::]:55460->5432/tcp

[5 s] --- api logs tail concise ---
Downloading watchfiles-1.1.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (456 kB)
Downloading websockets-16.0-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (184 kB)
Downloading mako-1.3.12-py3-none-any.whl (78 kB)
Downloading packaging-26.2-py3-none-any.whl (100 kB)
Downloading annotated_types-0.7.0-py3-none-any.whl (13 kB)
Downloading markupsafe-3.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (22 kB)
Building wheels for collected packages: terrayield-land-intelligence
  Building editable for terrayield-land-intelligence (pyproject.toml): started
  Building editable for terrayield-land-intelligence (pyproject.toml): finished with status 'done'
  Created wheel for terrayield-land-intelligence: filename=terrayield_land_intelligence-0.1.0-0.editable-py3-none-any.whl size=10071 sha256=e0943f7ec72511714ed83d0c0867b29ffd4e81e5137a87901ea4d6097e646bcc
  Stored in directory: /tmp/pip-ephem-wheel-cache-7rzqnw06/wheels/54/1b/b7/aa63e25c8f14f4f2ae7b04e6097bdecb770e455c5c1ee0a600
Successfully built terrayield-land-intelligence
Installing collected packages: websockets, uvloop, urllib3, typing-extensions, six, pyyaml, python-dotenv, psycopg-binary, packaging, numpy, MarkupSafe, idna, httptools, h11, greenlet, click, charset_normalizer, certifi, annotated-types, annotated-doc, uvicorn, typing-inspection, sqlalchemy, shapely, requests, python-dateutil, pyproj, pyogrio, pydantic-core, psycopg, Mako, httpcore, anyio, watchfiles, starlette, pydantic, pandas, httpx, geoalchemy2, alembic, pydantic-settings, geopandas, fastapi, terrayield-land-intelligence
Successfully installed Mako-1.3.12 MarkupSafe-3.0.3 alembic-1.18.4 annotated-doc-0.0.4 annotated-types-0.7.0 anyio-4.13.0 certifi-2026.4.22 charset_normalizer-3.4.7 click-8.3.3 fastapi-0.136.1 geoalchemy2-0.19.0 geopandas-1.1.3 greenlet-3.5.0 h11-0.16.0 httpcore-1.0.9 httptools-0.7.1 httpx-0.28.1 idna-3.13 numpy-2.4.4 packaging-26.2 pandas-3.0.2 psycopg-3.3.4 psycopg-binary-3.3.4 pydantic-2.13.3 pydantic-core-2.46.3 pydantic-settings-2.14.0 pyogrio-0.12.1 pyproj-3.7.2 python-dateutil-2.9.0.post0 python-dotenv-1.2.2 pyyaml-6.0.3 requests-2.33.1 shapely-2.1.2 six-1.17.0 sqlalchemy-2.0.49 starlette-1.0.0 terrayield-land-intelligence-0.1.0 typing-extensions-4.15.0 typing-inspection-0.4.2 urllib3-2.6.3 uvicorn-0.46.0 uvloop-0.22.1 watchfiles-1.1.1 websockets-16.0
FAILED: Multiple head revisions are present for given argument 'head'; please specify a specific target revision, '<branchname>@head' to narrow to a specific head, or 'heads' for all heads
Obtaining file:///app
  Installing build dependencies: started
  Installing build dependencies: finished with status 'done'
  Checking if build backend supports build_editable: started
  Checking if build backend supports build_editable: finished with status 'done'
  Getting requirements to build editable: started
  Getting requirements to build editable: finished with status 'done'
  Preparing editable metadata (pyproject.toml): started
  Preparing editable metadata (pyproject.toml): finished with status 'done'
Requirement already satisfied: alembic>=1.14.1 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (1.18.4)
Requirement already satisfied: fastapi>=0.116.0 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (0.136.1)
Requirement already satisfied: geoalchemy2>=0.16.0 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (0.19.0)
Requirement already satisfied: geopandas>=1.0.1 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (1.1.3)
Requirement already satisfied: httpx>=0.28.0 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (0.28.1)
Requirement already satisfied: pandas>=2.2.3 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (3.0.2)
Requirement already satisfied: psycopg>=3.2.0 in /usr/local/lib/python3.12/site-packages (from psycopg[binary]>=3.2.0->terrayield-land-intelligence==0.1.0) (3.3.4)
docker : WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the sy
stem package manager, possibly rendering your system unusable. It is recommended to use a virtual environment instead: 
https://pip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppres
s this warning.
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_verification_035_api_rootcause_recovery.ps1:20 
char:36
+ ... api logs tail concise' { docker logs --tail 100 terrayield_land_api }
+                              ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (WARNING: Runnin...s this warning.:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 

[notice] A new release of pip is available: 25.0.1 -> 26.1
[notice] To update, run: pip install --upgrade pip
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
ERROR [alembic.util.messaging] Multiple head revisions are present for given argument 'head'; please specify a specific
 target revision, '<branchname>@head' to narrow to a specific head, or 'heads' for all heads
ERROR [alembic.util.messaging] Multiple head revisions are present for given argument 'head'; please specify a specific
 target revision, '<branchname>@head' to narrow to a specific head, or 'heads' for all heads
Requirement already satisfied: pyproj>=3.7.1 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (3.7.2)
Requirement already satisfied: pyogrio>=0.11.1 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (0.12.1)
Requirement already satisfied: pydantic-settings>=2.8.0 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (2.14.0)
Requirement already satisfied: python-dateutil>=2.9.0 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (2.9.0.post0)
Requirement already satisfied: python-dotenv>=1.0.1 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (1.2.2)
Requirement already satisfied: requests>=2.32.0 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (2.33.1)
Requirement already satisfied: shapely>=2.0.7 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (2.1.2)
Requirement already satisfied: sqlalchemy>=2.0.38 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (2.0.49)
Requirement already satisfied: uvicorn>=0.34.0 in /usr/local/lib/python3.12/site-packages (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0) (0.46.0)
Requirement already satisfied: Mako in /usr/local/lib/python3.12/site-packages (from alembic>=1.14.1->terrayield-land-intelligence==0.1.0) (1.3.12)
Requirement already satisfied: typing-extensions>=4.12 in /usr/local/lib/python3.12/site-packages (from alembic>=1.14.1->terrayield-land-intelligence==0.1.0) (4.15.0)
Requirement already satisfied: starlette>=0.46.0 in /usr/local/lib/python3.12/site-packages (from fastapi>=0.116.0->terrayield-land-intelligence==0.1.0) (1.0.0)
Requirement already satisfied: pydantic>=2.9.0 in /usr/local/lib/python3.12/site-packages (from fastapi>=0.116.0->terrayield-land-intelligence==0.1.0) (2.13.3)
Requirement already satisfied: typing-inspection>=0.4.2 in /usr/local/lib/python3.12/site-packages (from fastapi>=0.116.0->terrayield-land-intelligence==0.1.0) (0.4.2)
Requirement already satisfied: annotated-doc>=0.0.2 in /usr/local/lib/python3.12/site-packages (from fastapi>=0.116.0->terrayield-land-intelligence==0.1.0) (0.0.4)
Requirement already satisfied: packaging in /usr/local/lib/python3.12/site-packages (from geoalchemy2>=0.16.0->terrayield-land-intelligence==0.1.0) (26.2)
Requirement already satisfied: numpy>=1.24 in /usr/local/lib/python3.12/site-packages (from geopandas>=1.0.1->terrayield-land-intelligence==0.1.0) (2.4.4)
Requirement already satisfied: anyio in /usr/local/lib/python3.12/site-packages (from httpx>=0.28.0->terrayield-land-intelligence==0.1.0) (4.13.0)
Requirement already satisfied: certifi in /usr/local/lib/python3.12/site-packages (from httpx>=0.28.0->terrayield-land-intelligence==0.1.0) (2026.4.22)
Requirement already satisfied: httpcore==1.* in /usr/local/lib/python3.12/site-packages (from httpx>=0.28.0->terrayield-land-intelligence==0.1.0) (1.0.9)
Requirement already satisfied: idna in /usr/local/lib/python3.12/site-packages (from httpx>=0.28.0->terrayield-land-intelligence==0.1.0) (3.13)
Requirement already satisfied: h11>=0.16 in /usr/local/lib/python3.12/site-packages (from httpcore==1.*->httpx>=0.28.0->terrayield-land-intelligence==0.1.0) (0.16.0)
Requirement already satisfied: psycopg-binary==3.3.4 in /usr/local/lib/python3.12/site-packages (from psycopg[binary]>=3.2.0->terrayield-land-intelligence==0.1.0) (3.3.4)
Requirement already satisfied: six>=1.5 in /usr/local/lib/python3.12/site-packages (from python-dateutil>=2.9.0->terrayield-land-intelligence==0.1.0) (1.17.0)
Requirement already satisfied: charset_normalizer<4,>=2 in /usr/local/lib/python3.12/site-packages (from requests>=2.32.0->terrayield-land-intelligence==0.1.0) (3.4.7)
Requirement already satisfied: urllib3<3,>=1.26 in /usr/local/lib/python3.12/site-packages (from requests>=2.32.0->terrayield-land-intelligence==0.1.0) (2.6.3)
Requirement already satisfied: greenlet>=1 in /usr/local/lib/python3.12/site-packages (from sqlalchemy>=2.0.38->terrayield-land-intelligence==0.1.0) (3.5.0)
Requirement already satisfied: click>=7.0 in /usr/local/lib/python3.12/site-packages (from uvicorn>=0.34.0->uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0) (8.3.3)
Requirement already satisfied: httptools>=0.6.3 in /usr/local/lib/python3.12/site-packages (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0) (0.7.1)
Requirement already satisfied: pyyaml>=5.1 in /usr/local/lib/python3.12/site-packages (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0) (6.0.3)
WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system pack
age manager, possibly rendering your system unusable. It is recommended to use a virtual environment instead: https://p
ip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppress this wa
rning.
Requirement already satisfied: uvloop>=0.15.1 in /usr/local/lib/python3.12/site-packages (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0) (0.22.1)
Requirement already satisfied: watchfiles>=0.20 in /usr/local/lib/python3.12/site-packages (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0) (1.1.1)
Requirement already satisfied: websockets>=10.4 in /usr/local/lib/python3.12/site-packages (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0) (16.0)
Requirement already satisfied: annotated-types>=0.6.0 in /usr/local/lib/python3.12/site-packages (from pydantic>=2.9.0->fastapi>=0.116.0->terrayield-land-intelligence==0.1.0) (0.7.0)
Requirement already satisfied: pydantic-core==2.46.3 in /usr/local/lib/python3.12/site-packages (from pydantic>=2.9.0->fastapi>=0.116.0->terrayield-land-intelligence==0.1.0) (2.46.3)
Requirement already satisfied: MarkupSafe>=0.9.2 in /usr/local/lib/python3.12/site-packages (from Mako->alembic>=1.14.1->terrayield-land-intelligence==0.1.0) (3.0.3)
Building wheels for collected packages: terrayield-land-intelligence
  Building editable for terrayield-land-intelligence (pyproject.toml): started
  Building editable for terrayield-land-intelligence (pyproject.toml): finished with status 'done'
  Created wheel for terrayield-land-intelligence: filename=terrayield_land_intelligence-0.1.0-0.editable-py3-none-any.whl size=10071 sha256=c41e928d4b8b84bebb6515dff0f4963ad721c24d80f0b4095d1cb8515e5ab0b0
  Stored in directory: /tmp/pip-ephem-wheel-cache-1_gkdgyy/wheels/54/1b/b7/aa63e25c8f14f4f2ae7b04e6097bdecb770e455c5c1ee0a600
Successfully built terrayield-land-intelligence
Installing collected packages: terrayield-land-intelligence
  Attempting uninstall: terrayield-land-intelligence
    Found existing installation: terrayield-land-intelligence 0.1.0
    Uninstalling terrayield-land-intelligence-0.1.0:
      Successfully uninstalled terrayield-land-intelligence-0.1.0
Successfully installed terrayield-land-intelligence-0.1.0
FAILED: Multiple head revisions are present for given argument 'head'; please specify a specific target revision, '<branchname>@head' to narrow to a specific head, or 'heads' for all heads

[notice] A new release of pip is available: 25.0.1 -> 26.1
[notice] To update, run: pip install --upgrade pip
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
ERROR [alembic.util.messaging] Multiple head revisions are present for given argument 'head'; please specify a specific
 target revision, '<branchname>@head' to narrow to a specific head, or 'heads' for all heads
ERROR [alembic.util.messaging] Multiple head revisions are present for given argument 'head'; please specify a specific
 target revision, '<branchname>@head' to narrow to a specific head, or 'heads' for all heads

[5 s] api logs tail concise EXIT=0
Downloading watchfiles-1.1.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (456 kB)
Downloading websockets-16.0-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (184 kB)
Downloading mako-1.3.12-py3-none-any.whl (78 kB)
Downloading packaging-26.2-py3-none-any.whl (100 kB)
Downloading annotated_types-0.7.0-py3-none-any.whl (13 kB)
Downloading markupsafe-3.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (22 kB)
Building wheels for collected packages: terrayield-land-intelligence
  Building editable for terrayield-land-intelligence (pyproject.toml): started
  Building editable for terrayield-land-intelligence (pyproject.toml): finished with status 'done'
  Created wheel for terrayield-land-intelligence: filename=terrayield_land_intelligence-0.1.0-0.editable-py3-none-any.whl size=10071 sha256=e0943f7ec72511714ed83d0c0867b29ffd4e81e5137a87901ea4d6097e646bcc
  Stored in directory: /tmp/pip-ephem-wheel-cache-7rzqnw06/wheels/54/1b/b7/aa63e25c8f14f4f2ae7b04e6097bdecb770e455c5c1ee0a600
Successfully built terrayield-land-intelligence
Installing collected packages: websockets, uvloop, urllib3, typing-extensions, six, pyyaml, python-dotenv, psycopg-binary, packaging, numpy, MarkupSafe, idna, httptools, h11, greenlet, click, charset_normalizer, certifi, annotated-types, annotated-doc, uvicorn, typing-inspection, sqlalchemy, shapely, requests, python-dateutil, pyproj, pyogrio, pydantic-core, psycopg, Mako, httpcore, anyio, watchfiles, starlette, pydantic, pandas, httpx, geoalchemy2, alembic, pydantic-settings, geopandas, fastapi, terrayield-land-intelligence
Successfully installed Mako-1.3.12 MarkupSafe-3.0.3 alembic-1.18.4 annotated-doc-0.0.4 annotated-types-0.7.0 anyio-4.13.0 certifi-2026.4.22 charset_normalizer-3.4.7 click-8.3.3 fastapi-0.136.1 geoalchemy2-0.19.0 geopandas-1.1.3 greenlet-3.5.0 h11-0.16.0 httpcore-1.0.9 httptools-0.7.1 httpx-0.28.1 idna-3.13 numpy-2.4.4 packaging-26.2 pandas-3.0.2 psycopg-3.3.4 psycopg-binary-3.3.4 pydantic-2.13.3 pydantic-core-2.46.3 pydantic-settings-2.14.0 pyogrio-0.12.1 pyproj-3.7.2 python-dateutil-2.9.0.post0 python-dotenv-1.2.2 pyyaml-6.0.3 requests-2.33.1 shapely-2.1.2 six-1.17.0 sqlalchemy-2.0.49 starlette-1.0.0 terrayield-land-intelligence-0.1.0 typing-extensions-4.15.0 typing-inspection-0.4.2 urllib3-2.6.3 uvicorn-0.46.0 uvloop-0.22.1 watchfiles-1.1.1 websockets-16.0
FAILED: Multiple head revisions are present for given argument 'head'; please specify a specific target revision, '<branchname>@head' to narrow to a specific head, or 'heads' for all heads
Obtaining file:///app
  Installing build dependencies: started
  Installing build dependencies: finished with status 'done'
  Checking if build backend supports build_editable: started
  Checking if build backend supports build_editable: finished with status 'done'
  Getting requirements to build editable: started
  Getting requirements to build editable: finished with status 'done'
  Preparing editable metadata (pyproject.toml): started
  Preparing editable metadata (pyproject.toml): finished with status 'done'
Requirement already satisfied: alembic>=1.14.1 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (1.18.4)
Requirement already satisfied: fastapi>=0.116.0 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (0.136.1)
Requirement already satisfied: geoalchemy2>=0.16.0 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (0.19.0)
Requirement already satisfied: geopandas>=1.0.1 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (1.1.3)
Requirement already satisfied: httpx>=0.28.0 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (0.28.1)
Requirement already satisfied: pandas>=2.2.3 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (3.0.2)
Requirement already satisfied: psycopg>=3.2.0 in /usr/local/lib/python3.12/site-packages (from psycopg[binary]>=3.2.0->terrayield-land-intelligence==0.1.0) (3.3.4)
docker : WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the sy
stem package manager, possibly rendering your system unusable. It is recommended to use a virtual environment instead: 
https://pip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppres
s this warning.
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_verification_035_api_rootcause_recovery.ps1:20 
char:36
+ ... api logs tail concise' { docker logs --tail 100 terrayield_land_api }
+                              ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (WARNING: Runnin...s this warning.:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 

[notice] A new release of pip is available: 25.0.1 -> 26.1
[notice] To update, run: pip install --upgrade pip
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
ERROR [alembic.util.messaging] Multiple head revisions are present for given argument 'head'; please specify a specific
 target revision, '<branchname>@head' to narrow to a specific head, or 'heads' for all heads
ERROR [alembic.util.messaging] Multiple head revisions are present for given argument 'head'; please specify a specific
 target revision, '<branchname>@head' to narrow to a specific head, or 'heads' for all heads
Requirement already satisfied: pyproj>=3.7.1 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (3.7.2)
Requirement already satisfied: pyogrio>=0.11.1 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (0.12.1)
Requirement already satisfied: pydantic-settings>=2.8.0 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (2.14.0)
Requirement already satisfied: python-dateutil>=2.9.0 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (2.9.0.post0)
Requirement already satisfied: python-dotenv>=1.0.1 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (1.2.2)
Requirement already satisfied: requests>=2.32.0 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (2.33.1)
Requirement already satisfied: shapely>=2.0.7 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (2.1.2)
Requirement already satisfied: sqlalchemy>=2.0.38 in /usr/local/lib/python3.12/site-packages (from terrayield-land-intelligence==0.1.0) (2.0.49)
Requirement already satisfied: uvicorn>=0.34.0 in /usr/local/lib/python3.12/site-packages (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0) (0.46.0)
Requirement already satisfied: Mako in /usr/local/lib/python3.12/site-packages (from alembic>=1.14.1->terrayield-land-intelligence==0.1.0) (1.3.12)
Requirement already satisfied: typing-extensions>=4.12 in /usr/local/lib/python3.12/site-packages (from alembic>=1.14.1->terrayield-land-intelligence==0.1.0) (4.15.0)
Requirement already satisfied: starlette>=0.46.0 in /usr/local/lib/python3.12/site-packages (from fastapi>=0.116.0->terrayield-land-intelligence==0.1.0) (1.0.0)
Requirement already satisfied: pydantic>=2.9.0 in /usr/local/lib/python3.12/site-packages (from fastapi>=0.116.0->terrayield-land-intelligence==0.1.0) (2.13.3)
Requirement already satisfied: typing-inspection>=0.4.2 in /usr/local/lib/python3.12/site-packages (from fastapi>=0.116.0->terrayield-land-intelligence==0.1.0) (0.4.2)
Requirement already satisfied: annotated-doc>=0.0.2 in /usr/local/lib/python3.12/site-packages (from fastapi>=0.116.0->terrayield-land-intelligence==0.1.0) (0.0.4)
Requirement already satisfied: packaging in /usr/local/lib/python3.12/site-packages (from geoalchemy2>=0.16.0->terrayield-land-intelligence==0.1.0) (26.2)
Requirement already satisfied: numpy>=1.24 in /usr/local/lib/python3.12/site-packages (from geopandas>=1.0.1->terrayield-land-intelligence==0.1.0) (2.4.4)
Requirement already satisfied: anyio in /usr/local/lib/python3.12/site-packages (from httpx>=0.28.0->terrayield-land-intelligence==0.1.0) (4.13.0)
Requirement already satisfied: certifi in /usr/local/lib/python3.12/site-packages (from httpx>=0.28.0->terrayield-land-intelligence==0.1.0) (2026.4.22)
Requirement already satisfied: httpcore==1.* in /usr/local/lib/python3.12/site-packages (from httpx>=0.28.0->terrayield-land-intelligence==0.1.0) (1.0.9)
Requirement already satisfied: idna in /usr/local/lib/python3.12/site-packages (from httpx>=0.28.0->terrayield-land-intelligence==0.1.0) (3.13)
Requirement already satisfied: h11>=0.16 in /usr/local/lib/python3.12/site-packages (from httpcore==1.*->httpx>=0.28.0->terrayield-land-intelligence==0.1.0) (0.16.0)
Requirement already satisfied: psycopg-binary==3.3.4 in /usr/local/lib/python3.12/site-packages (from psycopg[binary]>=3.2.0->terrayield-land-intelligence==0.1.0) (3.3.4)
Requirement already satisfied: six>=1.5 in /usr/local/lib/python3.12/site-packages (from python-dateutil>=2.9.0->terrayield-land-intelligence==0.1.0) (1.17.0)
Requirement already satisfied: charset_normalizer<4,>=2 in /usr/local/lib/python3.12/site-packages (from requests>=2.32.0->terrayield-land-intelligence==0.1.0) (3.4.7)
Requirement already satisfied: urllib3<3,>=1.26 in /usr/local/lib/python3.12/site-packages (from requests>=2.32.0->terrayield-land-intelligence==0.1.0) (2.6.3)
Requirement already satisfied: greenlet>=1 in /usr/local/lib/python3.12/site-packages (from sqlalchemy>=2.0.38->terrayield-land-intelligence==0.1.0) (3.5.0)
Requirement already satisfied: click>=7.0 in /usr/local/lib/python3.12/site-packages (from uvicorn>=0.34.0->uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0) (8.3.3)
Requirement already satisfied: httptools>=0.6.3 in /usr/local/lib/python3.12/site-packages (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0) (0.7.1)
Requirement already satisfied: pyyaml>=5.1 in /usr/local/lib/python3.12/site-packages (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0) (6.0.3)
WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system pack
age manager, possibly rendering your system unusable. It is recommended to use a virtual environment instead: https://p
ip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppress this wa
rning.
Requirement already satisfied: uvloop>=0.15.1 in /usr/local/lib/python3.12/site-packages (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0) (0.22.1)
Requirement already satisfied: watchfiles>=0.20 in /usr/local/lib/python3.12/site-packages (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0) (1.1.1)
Requirement already satisfied: websockets>=10.4 in /usr/local/lib/python3.12/site-packages (from uvicorn[standard]>=0.34.0->terrayield-land-intelligence==0.1.0) (16.0)
Requirement already satisfied: annotated-types>=0.6.0 in /usr/local/lib/python3.12/site-packages (from pydantic>=2.9.0->fastapi>=0.116.0->terrayield-land-intelligence==0.1.0) (0.7.0)
Requirement already satisfied: pydantic-core==2.46.3 in /usr/local/lib/python3.12/site-packages (from pydantic>=2.9.0->fastapi>=0.116.0->terrayield-land-intelligence==0.1.0) (2.46.3)
Requirement already satisfied: MarkupSafe>=0.9.2 in /usr/local/lib/python3.12/site-packages (from Mako->alembic>=1.14.1->terrayield-land-intelligence==0.1.0) (3.0.3)
Building wheels for collected packages: terrayield-land-intelligence
  Building editable for terrayield-land-intelligence (pyproject.toml): started
  Building editable for terrayield-land-intelligence (pyproject.toml): finished with status 'done'
  Created wheel for terrayield-land-intelligence: filename=terrayield_land_intelligence-0.1.0-0.editable-py3-none-any.whl size=10071 sha256=c41e928d4b8b84bebb6515dff0f4963ad721c24d80f0b4095d1cb8515e5ab0b0
  Stored in directory: /tmp/pip-ephem-wheel-cache-1_gkdgyy/wheels/54/1b/b7/aa63e25c8f14f4f2ae7b04e6097bdecb770e455c5c1ee0a600
Successfully built terrayield-land-intelligence
Installing collected packages: terrayield-land-intelligence
  Attempting uninstall: terrayield-land-intelligence
    Found existing installation: terrayield-land-intelligence 0.1.0
    Uninstalling terrayield-land-intelligence-0.1.0:
      Successfully uninstalled terrayield-land-intelligence-0.1.0
Successfully installed terrayield-land-intelligence-0.1.0
FAILED: Multiple head revisions are present for given argument 'head'; please specify a specific target revision, '<branchname>@head' to narrow to a specific head, or 'heads' for all heads

[notice] A new release of pip is available: 25.0.1 -> 26.1
[notice] To update, run: pip install --upgrade pip
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
ERROR [alembic.util.messaging] Multiple head revisions are present for given argument 'head'; please specify a specific
 target revision, '<branchname>@head' to narrow to a specific head, or 'heads' for all heads
ERROR [alembic.util.messaging] Multiple head revisions are present for given argument 'head'; please specify a specific
 target revision, '<branchname>@head' to narrow to a specific head, or 'heads' for all heads

[5 s] --- compile critical files ---

[5 s] compile critical files EXIT=0

[15 s] BACKUP alembic\versions\20260504_022_sale_land_verification_evidence.py
[15 s] DISABLED_SCAFFOLD_MIGRATION=alembic\versions\20260504_022_sale_land_verification_evidence.py.disabled
[19 s] --- start api only no config dump ---
docker :  Container terrayield_land_postgis Running 
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_verification_035_api_rootcause_recovery.ps1:38 
char:46
+ ... fig dump' { docker compose -f docker-compose.yml -f docker-compose.aa ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: ( Container terr...ostgis Running :String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
 Container terrayield_land_api Starting 
 Container terrayield_land_api Started 

[20 s] start api only no config dump EXIT=0
docker :  Container terrayield_land_postgis Running 
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_verification_035_api_rootcause_recovery.ps1:38 
char:46
+ ... fig dump' { docker compose -f docker-compose.yml -f docker-compose.aa ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: ( Container terr...ostgis Running :String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
 Container terrayield_land_api Starting 
 Container terrayield_land_api Started 

[51 s] API_READY attempt=6
[51 s] API_HEALTH_FINAL=True
[51 s] RECOVERY_ACTION=disable_scaffold_migration_then_api_restart
[51 s] EVIDENCE_CHAIN_ACCURACY=77/100
[51 s] GEOMETRY_BOUNDARY_ACCURACY=41/100
[51 s] API_OPERATIONAL_HEALTH=95/100
[51 s] ELAPSED_SECONDS=51
SUMMARY_FILE=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_next_fix\verification_035_api_rootcause_recovery_20260504_061418\summary.md
DETAIL_FILE=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_next_fix\verification_035_api_rootcause_recovery_20260504_061418\detail.txt
API_HEALTH_FINAL=True
RECOVERY_ACTION=disable_scaffold_migration_then_api_restart
EVIDENCE_CHAIN_ACCURACY=77/100
GEOMETRY_BOUNDARY_ACCURACY=41/100
API_OPERATIONAL_HEALTH=95/100
RESULT=api_rootcause_recovery_done
VERIFICATION_035_API_ROOTCAUSE_RECOVERY_DONE

``

## Error
``text

``

