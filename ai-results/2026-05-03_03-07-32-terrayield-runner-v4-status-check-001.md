# AAYS ChatGPT Runner V4 Result

## Task
Runner V4 TerraYield status check

## Task ID
terrayield-runner-v4-status-check-001

## Progress
100%

## Action
status_check

## Time
05/03/2026 03:07:33

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Timeout Seconds
300

## Exit Code
0

## Output
``text
TASK: TerraYield status check
PROGRESS: 100%
NAME                      IMAGE                    COMMAND                  SERVICE   CREATED      STATUS        PORTS
terrayield_land_postgis   postgis/postgis:16-3.4   "docker-entrypoint.sÔÇĞ"   db        2 days ago   Up 37 hours   0.0.0.0:55460->5432/tcp, [::]:55460->5432/tcp
["bash","-lc","cd /app && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8010"]

``

## Error
``text
=@ : The term '=@' is not recognized as the name of a cmdlet, function, script file, or operable program. Check the spe
lling of the name, or if a path was included, verify that the path is correct and try again.
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-tmp\task-terrayield-runner-v4-status-check-001.ps1:1 char:1
+ =@('/health','/openapi.json','/map/listings','/map/sales-layers/verif ...
+ ~~
    + CategoryInfo          : ObjectNotFound: (=@:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

``

