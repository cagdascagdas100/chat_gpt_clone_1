# AAYS ChatGPT Runner V4 Result

## Task
Probe TerraYield recovery status after 013

## Task ID
terrayield-recovery-014-status-probe

## Progress
97%

## Action


## Time
05/03/2026 22:18:37

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Timeout Seconds
600

## Exit Code
0

## Output
``text
TASK: Recovery 014 status probe
PROGRESS: 97%
TIME:

3 Mayıs 2026 Pazar 22:18:19
--- script exists ---
SCRIPT_EXISTS C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_recovery_013_docker_daemon.ps1
--- latest recovery reports ---

FullName                                                                                                               
--------                                                                                                               
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_next_fix\recovery_013_docker_daemon_20260503...
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_next_fix\recovery_012_docker_compile_2026050...



--- newest recovery summary preview ---
# TerraYield Recovery 013 Summary

## Result
api_not_ready

## Compile OK
True

## Docker Ready
True

## API Ready
False

## API Ready Seconds
-1

## Endpoint Summary
[894 s] FAIL /health error=Uzak sunucuya bağlanılamıyor
FAIL /health error=Uzak sunucuya bağlanılamıyor
[898 s] FAIL /openapi.json error=Uzak sunucuya bağlanılamıyor
FAIL /openapi.json error=Uzak sunucuya bağlanılamıyor
[902 s] FAIL /map/listings error=Uzak sunucuya bağlanılamıyor
FAIL /map/listings error=Uzak sunucuya bağlanılamıyor
[906 s] FAIL /map/sales-history/status error=Uzak sunucuya bağlanılamıyor
FAIL /map/sales-history/status error=Uzak sunucuya bağlanılamıyor
[910 s] FAIL /map/sales-history/external-evidence error=Uzak sunucuya bağlanılamıyor
FAIL /map/sales-history/external-evidence error=Uzak sunucuya bağlanılamıyor
[914 s] FAIL /map/sales-history/parcels error=Uzak sunucuya bağlanılamıyor
FAIL /map/sales-history/parcels error=Uzak sunucuya bağlanılamıyor
[918 s] FAIL /map/sales-history/combined error=Uzak sunucuya bağlanılamıyor
FAIL /map/sales-history/combined error=Uzak sunucuya bağlanılamıyor
[922 s] FAIL /map/listings error=Uzak sunucuya bağlanılamıyor
FAIL /map/listings error=Uzak sunucuya bağlanılamıyor


## Progress Estimate
- Application stabilization/speed: 
95%
- Cross-computer fast-start/runability: 
90%
- Continue-only automation bridge: 91%
- Overall combined project: 
91-92%

## Files
Detail: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_next_fix\recovery_013_docker_daemon_20260503_215159\detail.txt
Elapsed seconds: 923

--- docker info ---
Client:
 Version:    29.3.1
 Context:    desktop-linux
 Debug Mode: false
 Plugins:
  agent: Docker AI Agent Runner (Docker Inc.)
    Version:  v1.32.4
    Path:     C:\Program Files\Docker\cli-plugins\docker-agent.exe
  ai: Docker AI Agent - Ask Gordon (Docker Inc.)
    Version:  v1.20.1
    Path:     C:\Program Files\Docker\cli-plugins\docker-ai.exe
  buildx: Docker Buildx (Docker Inc.)
    Version:  v0.32.1-desktop.1
    Path:     C:\Program Files\Docker\cli-plugins\docker-buildx.exe
  compose: Docker Compose (Docker Inc.)
    Version:  v5.1.0
    Path:     C:\Program Files\Docker\cli-plugins\docker-compose.exe
  debug: Get a shell into any image or container (Docker Inc.)
    Version:  0.0.47
    Path:     C:\Program Files\Docker\cli-plugins\docker-debug.exe
  desktop: Docker Desktop commands (Docker Inc.)
    Version:  v0.3.0
    Path:     C:\Program Files\Docker\cli-plugins\docker-desktop.exe
  dhi: CLI for managing Docker Hardened Images (Docker Inc.)
    Version:  v0.0.0-alpha
    Path:     C:\Program Files\Docker\cli-plugins\docker-dhi.exe
  extension: Manages Docker extensions (Docker Inc.)
    Version:  v0.2.31
    Path:     C:\Program Files\Docker\cli-plugins\docker-extension.exe
  init: Creates Docker-related starter files for your project (Docker Inc.)
    Version:  v1.4.0
    Path:     C:\Program Files\Docker\cli-plugins\docker-init.exe
  mcp: Docker MCP Plugin (Docker Inc.)
    Version:  v0.40.1
    Path:     C:\Program Files\Docker\cli-plugins\docker-mcp.exe
  model: Docker Model Runner (Docker Inc.)
    Version:  v1.1.5
    Path:     C:\Program Files\Docker\cli-plugins\docker-model.exe
  offload: Docker Offload (Docker Inc.)
    Version:  v0.5.73
    Path:     C:\Program Files\Docker\cli-plugins\docker-offload.exe
  pass: Docker Pass Secrets Manager Plugin (beta) (Docker Inc.)
    Version:  v0.0.24
    Path:     C:\Program Files\Docker\cli-plugins\docker-pass.exe
  sandbox: Docker Sandbox (Docker Inc.)
    Version:  v0.12.0
    Path:     C:\Program Files\Docker\cli-plugins\docker-sandbox.exe
  sbom: View the packaged-based Software Bill Of Materials (SBOM) for an image (Anchore Inc.)
    Version:  0.6.0
    Path:     C:\Program Files\Docker\cli-plugins\docker-sbom.exe
  scout: Docker Scout (Docker Inc.)
    Version:  v1.20.2
    Path:     C:\Program Files\Docker\cli-plugins\docker-scout.exe

Server:
 Containers: 4
  Running: 3
  Paused: 0
  Stopped: 1
 Images: 4
 Server Version: 29.3.1
 Storage Driver: overlayfs
  driver-type: io.containerd.snapshotter.v1
 Logging Driver: json-file
 Cgroup Driver: cgroupfs
 Cgroup Version: 2
 Plugins:
  Volume: local
  Network: bridge host ipvlan macvlan null overlay
  Log: awslogs fluentd gcplogs gelf journald json-file local splunk syslog
 CDI spec directories:
  /etc/cdi
  /var/run/cdi
 Discovered Devices:
  cdi: docker.com/gpu=webgpu
 Swarm: inactive
 Runtimes: io.containerd.runc.v2 nvidia runc
 Default Runtime: runc
 Init Binary: docker-init
 containerd version: dea7da592f5d1d2b7755e3a161be07f43fad8f75
 runc version: v1.3.4-0-gd6d73eb8
 init version: de40ad0
 Security Options:
  seccomp
   Profile: builtin
  cgroupns
 Kernel Version: 6.6.87.2-microsoft-standard-WSL2
 Operating System: Docker Desktop
 OSType: linux
 Architecture: x86_64
 CPUs: 12
 Total Memory: 3.484GiB
 Name: docker-desktop
 ID: 6606eef4-3055-4601-bc7d-73370ebc1eb6
 Docker Root Dir: /var/lib/docker
 Debug Mode: false
 HTTP Proxy: http.docker.internal:3128
 HTTPS Proxy: http.docker.internal:3128
 No Proxy: hubproxy.docker.internal
 Labels:
  com.docker.desktop.address=npipe://\\.\pipe\docker_cli
 Experimental: false
 Insecure Registries:
  hubproxy.docker.internal:5555
  ::1/128
  127.0.0.0/8
 Live Restore Enabled: false
 Firewall Backend: iptables


--- docker compose ps ---
NAME      IMAGE     COMMAND   SERVICE   CREATED   STATUS    PORTS

--- endpoint quick validation ---
FAIL /health error=Uzak sunucuya bağlanılamıyor
FAIL /map/listings error=Uzak sunucuya bağlanılamıyor
FAIL /map/sales-history/status error=Uzak sunucuya bağlanılamıyor
FAIL /map/sales-history/combined error=Uzak sunucuya bağlanılamıyor
RECOVERY_014_STATUS_PROBE_DONE



``

## Error
``text

``

