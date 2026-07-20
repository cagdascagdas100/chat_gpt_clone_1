# AAYS Portable Any-PC Bootstrap Test

## Result

- Status: `PASS`
- Workstream: `AAYS_21_SLOT_SAFE_PARALLEL_V1`
- Portable root on this PC: `F:\TerraYield_AAYS_Portable`
- Drive letter is runtime-only: `true`
- Primary user launcher: `00_BASKA_BILGISAYARDA_ONCE_BUNA_CIFT_TIKLA.cmd`
- Shortcut installer: `01_BU_BILGISAYARA_MASAUSTU_KISAYOLLARINI_KUR.cmd`
- Source implementation commits: `c4d97a69f48cd161b21e09410fd8b7fe6230b5ea`, `b00a0dbb4833190dbdb95080026cca02054ad5fe`
- GitHub remote readback: `PASS`
- Coordinator remote sync: `PASS`
- `final_ready=false`

## Verified Behavior

- Normal `F:\TerraYield_AAYS_Portable` startup: `PASS`.
- Alternate drive simulation through `R:\TerraYield_AAYS_Portable`: `PASS`.
- Temporary `R:` mapping removed after the test: `PASS`.
- Portable preflight: `PASS`.
- Application health on fixed port 8012: `PASS`.
- Single coordinator: one live process; duplicate runner was not created.
- Logical slot count: 21.
- Control panel: one live process; duplicate panel was not created.
- Current-PC desktop shortcuts: 3 created and targets verified.
- Publisher Git connectivity check: `PASS`.
- GitHub branch HEAD readback: `b00a0dbb4833190dbdb95080026cca02054ad5fe`.

## New-PC Use

1. Connect the portable disk.
2. Open its `TerraYield_AAYS_Portable` folder.
3. Double-click `00_BASKA_BILGISAYARDA_ONCE_BUNA_CIFT_TIKLA.cmd`.
4. To install shortcuts for that PC, run `01_BU_BILGISAYARA_MASAUSTU_KISAYOLLARINI_KUR.cmd` once.

The shortcut installer must be run separately on each PC because Windows `.lnk` files store the drive path used on the PC where they were created. The portable `.cmd` launcher itself does not store a fixed drive letter.

## Fixed URLs

- Application: `http://127.0.0.1:8012/england_map_web/index.html`
- Health: `http://127.0.0.1:8012/health`
- OpenAPI: `http://127.0.0.1:8012/openapi.json`

## Recovery Note

During implementation, the live coordinator and manual publisher edit overlapped and the shallow boundary file was zero-filled. The coordinator was stopped, the corrupt file was backed up to the portable recovery directory, the shallow boundary was rebuilt from verified Git history, and `git fsck --connectivity-only` passed. The final edits were committed before the coordinator was restarted.

## Safety

- New runner architecture: `false`
- Parallel duplicate coordinator: `false`
- Automatic Windows startup installation: `false`
- Fake data: `false`
- DB write: `false`
- Migration: `false`
- Production deploy: `false`
- Product final ready: `false`
- Final ready: `false`
