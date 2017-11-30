# ssdb-open-falcon

SSDB Monitor Script for Open Falcon

### Step 1: Edit conf

Rename `ssdb-open-falcon.yml.default` to `ssdb-open-falcon.yml`, then edit the file, and add your ssdb servers.

```yml
falcon:
    push_url: http://127.0.0.1:6071/v1/push
    step: 60

# SSDB clusters
ssdb-clusters:
    - {endpoint: "localhost", host: "127.0.0.1", port: 12700, password: "", tags: ""}

```

### Step 2: Add the monitor script to crontab

```
$ crontab -l
*/1 * * * * cd /path/to/ssdb-open-falcon && python -u ./bin/ssdb-falcon.py >> ssdb-open-falcon.log 2>&1
```

# ssdb-open-falcon

用于 Open Falcon 的 SSDB 监控采集脚本

### 第一步：编辑配置文件

将 `ssdb-open-falcon.yml.default` 重命名为 `ssdb-open-falcon.yml`，然后编辑这个文件，添加你要监控的 SSDB 服务器信息。

```yml
falcon:
    push_url: http://127.0.0.1:6071/v1/push
    step: 60

# SSDB clusters
ssdb-clusters:
    - {endpoint: "localhost", host: "127.0.0.1", port: 12700, password: "", tags: ""}

```

### 第二步：将监控脚本添加到 crontab 中定时执行

```
$ crontab -l
*/1 * * * * cd /path/to/ssdb-open-falcon && python -u ./bin/ssdb-falcon.py >> ssdb-open-falcon.log 2>&1
```

## 好用就给个 Star 呗！