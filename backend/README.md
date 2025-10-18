

# install module
pip install fastapi uvicorn psutil
sudo apt install iw
sudo apt install jq


# apiserver start command (backend/ ディレクトリ内で実行 venv環境にて)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000    # srcディレクトリなら


# get command
curl http://localhost:8000/api/network/status | jq


# 作業用メモ
scp tecsmnt@172.21.206.157:~/pw3365_api.py /home/tecsmnt/repositories/pw3365_project/backend/src/api/
scp tecsmnt@172.21.206.157:~/pw3365_service.py /home/tecsmnt/repositories/pw3365_project/backend/src/core/services/
scp tecsmnt@172.21.206.157:~/insert_service.py /home/tecsmnt/repositories/pw3365_project/backend/src/core/services/

# srcの下で実行 devからtaf padのwslへ
scp -P 2222  api/pw3365_api.py tecsmnt@172.21.206.157:/home/tecsmnt/repositories/pw3365_project/backend/src/api/

scp -P 2222  config/settings.yaml tecsmnt@172.21.206.157:/home/tecsmnt/repositories/pw3365_project/backend/src/config/

scp -P 2222 core/services/pw3365_service.py tecsmnt@172.21.206.157:/home/tecsmnt/repositories/pw3365_project/backend/src/core/services/
scp -P 2222 core/services/insert_service.py tecsmnt@172.21.206.157:/home/tecsmnt/repositories/pw3365_project/backend/src/core/services/
scp -P 2222 core/services/network_service.py tecsmnt@172.21.206.157:/home/tecsmnt/repositories/pw3365_project/backend/src/core/services/
scp -P 2222 core/db.py tecsmnt@172.21.206.157:/home/tecsmnt/repositories/pw3365_project/backend/src/core/

scp -P 2222 utils/get_mac_id.py tecsmnt@172.21.206.157:/home/tecsmnt/repositories/pw3365_project/backend/src/utils/
scp -P 2222 utils/pw3365_parser.py tecsmnt@172.21.206.157:/home/tecsmnt/repositories/pw3365_project/backend/src/utils/
scp -P 2222 utils/pg_replication.py tecsmnt@172.21.206.157:/home/tecsmnt/repositories/pw3365_project/backend/src/utils/
scp -P 2222 utils/*.py tecsmnt@172.21.206.157:/home/tecsmnt/repositories/pw3365_project/backend/src/utils/

# wslからpower shellを呼び出してwindows側のIPを取得
export PATH=$PATH:/mnt/c/Windows/System32/WindowsPowerShell/v1.0  # windowsのPATHをwslに渡す
powershell.exe -Command "Get-NetIPAddress -AddressFamily IPv4 | Select-Object InterfaceAlias, IPAddress"

# 固有ID
cat /etc/machine-id

# ------------------------------------------------
# API REQUEST (localhostのproxy除外をしておくこと)

# get request
curl http://localhost:8000/network/status |jq   # ネットワーク確認
curl http://localhost:8000/meter/pw3365/current | jq    # 現在の計測値を取得
curl http://localhost:8000/meter/pw3365/status | jq 

## post request データ収集開始 periodは分単位
curl -X POST "http://localhost:8000/meter/pw3365/start?type=lan" \
     -H "Content-Type: application/json" \
     -d '{"period": 5, "device_name": "保全C大型モニター"}'

curl -X POST http://localhost:8000/meter/pw3365/stop


## api path確認
curl http://localhost:8000/openapi.json | jq '.paths'

# ------------------------------------------------
## postgresql replication
```SQL
-- エッジ側でパブリケーション作成
CREATE PUBLICATION edge_pub FOR ALL TABLES;

-- メインDBにサブスクリプション作成
CREATE SUBSCRIPTION edge_sub
  CONNECTION 'host=db.example.com dbname=maindb user=replicator password=xxx'
  PUBLICATION edge_pub;
```

### 管理用テーブル作成
```SQL
--- エッジ側で計測開始/停止時にDB更新することでそのトリガーでサブを開始
CREATE TABLE admin.subscription_control (
  subscription_id TEXT PRIMARY KEY,
  ip_address TEXT NOT NULL,
  status TEXT CHECK (status IN ('start', 'stop')),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  last_enabled_at TIMESTAMPTZ
);
```

### pg_cronで一定時間パブなければサブを一時停止
```SQL
-- pg_cron拡張なければインストール
sudo apt update
sudo apt install postgresql-16-cron

-- psqlで有効化
tecs_data=# CREATE EXTENSION pg_cron;

-- 10分周期で確認し61分以上パブなければ一時停止するcronを登録
-- 関数を作成
CREATE OR REPLACE FUNCTION admin.disable_stale_subs()
RETURNS void AS $$
DECLARE
  r RECORD;
BEGIN
  FOR r IN
    SELECT subname FROM pg_stat_subscription
    WHERE enabled = true
      AND last_msg_receipt_time IS NOT NULL
      AND last_msg_receipt_time < now() - interval '61 minutes'
  LOOP
    EXECUTE format('ALTER SUBSCRIPTION %I DISABLE;', r.subname);
    UPDATE admin.subscription_control
    SET status = 'stop'
    WHERE device_id = substring(r.subname from 5); -- 'sub_<device_id>'からdevice_idを抽出
  END LOOP;
END;
$$ LANGUAGE plpgsql;

-- pg_cronにjobを登録
SELECT cron.schedule(
  'disable_stale_subs',
  '*/10 * * * *',
  'SELECT admin.disable_stale_subs();'
);

-- jobを確認
SELECT * FROM cron.job;
```

### トリガーでサブを開始/停止
```SQL
-- 関数を作成
CREATE OR REPLACE FUNCTION admin.control_subscription()
RETURNS TRIGGER AS $$
BEGIN

  -- insertやsubのIPが変わった時の処理
  IF TG_OP = 'INSERT' OR NEW.ip_address IS DISTINCT FROM OLD.ip_address THEN
    EXECUTE format(
      'ALTER SUBSCRIPTION %I CONNECTION ''host=%s dbname=tecs_data user=postgres password=postgres'';',
      NEW.subscription_id, NEW.ip_address
    );
  END IF;

  -- statusが変化したときのみ処理
  IF TG_OP = 'UPDATE' AND NEW.status = OLD.status THEN
    RETURN NEW;
  END IF;

  IF NEW.status = 'start' THEN
    EXECUTE format('ALTER SUBSCRIPTION %I ENABLE;', NEW.subscription_id);
    UPDATE admin.subscription_control
    SET last_enabled_at = now()
    WHERE subscription_id = NEW.subscription_id;

  ELSIF NEW.status = 'stop' THEN
    EXECUTE format('ALTER SUBSCRIPTION %I DISABLE;', NEW.subscription_id);
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- トリガーを登録
CREATE TRIGGER trg_control_subscription
AFTER INSERT OR UPDATE ON admin.subscription_control
FOR EACH ROW
EXECUTE FUNCTION admin.control_subscription();

```


# ------------------------------------------------

# pw3365 関係テーブルスキーマ ※timescaledbにするとlogical replicationできない・・・
```SQL

-- スキーマの移動
-- ALTER TABLE public.テーブル名 SET SCHEMA iot_data;

CREATE TABLE iot_data.pw3365_power (
    time TIMESTAMPTZ NOT NULL,
    device_id TEXT NOT NULL,
    device_name TEXT,
    voltage_phase_r DOUBLE PRECISION,
    voltage_phase_s DOUBLE PRECISION,
    voltage_phase_t DOUBLE PRECISION,
    current_phase_r DOUBLE PRECISION,
    current_phase_s DOUBLE PRECISION,
    current_phase_t DOUBLE PRECISION,
    power_active DOUBLE PRECISION,
    power_reactive DOUBLE PRECISION,
    power_apparent DOUBLE PRECISION,
    power_factor DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS iot_data.pw3365_voltage (
    date_time TIMESTAMPTZ NOT NULL,
    device_id TEXT,
    device_name TEXT,
    u1_ins REAL,
    ufnd1_ins REAL,
    udeg1_ins REAL,
    upeak1_ins REAL,
    u1_avg REAL,
    ufnd1_avg REAL,
    udeg1_avg REAL,
    u1_max REAL,
    ufnd1_max REAL,
    udeg1_max REAL,
    upeak1_max REAL,
    u1_min REAL,
    ufnd1_min REAL,
    udeg1_min REAL,
    upeak1_min REAL,
    PRIMARY KEY (date_time, device_id)
);

------------------------------------------------
CREATE TABLE IF NOT EXISTS iot_data.pw3365_current (
    date_time TIMESTAMPTZ NOT NULL,
    device_id TEXT,
    device_name TEXT,
    i1_ins REAL,
    ifnd1_ins REAL,
    ideg1_ins REAL,
    ipeak1_ins REAL,
    i1_avg REAL,
    ifnd1_avg REAL,
    ideg1_avg REAL,
    i1_max REAL,
    ifnd1_max REAL,
    ideg1_max REAL,
    ipeak1_max REAL,
    i1_min REAL,
    ifnd1_min REAL,
    ideg1_min REAL,
    ipeak1_min REAL,
    PRIMARY KEY (date_time, device_id)
);

------------------------------------------------
CREATE TABLE IF NOT EXISTS iot_data.pw3365_freq (
    date_time TIMESTAMPTZ NOT NULL,
    device_id TEXT,
    device_name TEXT,
    freq_ins REAL,
    freq_avg REAL,
    freq_max REAL,
    freq_min REAL,
    PRIMARY KEY (date_time, device_id)
);

------------------------------------------------
CREATE TABLE IF NOT EXISTS iot_data.pw3365_energy (
    date_time TIMESTAMPTZ NOT NULL,
    device_id TEXT,
    device_name TEXT,
    wpplus1 REAL,
    wp_1 REAL,
    wqlag1 REAL,
    wqlead1 REAL,
    wpplusdem1 REAL,
    wp_dem1 REAL,
    wqlagdem1 REAL,
    wqleaddem1 REAL,
    PRIMARY KEY (date_time, device_id)
);

------------------------------------------------
CREATE TABLE IF NOT EXISTS iot_data.pw3365_demand (
    date_time TIMESTAMPTZ NOT NULL,
    device_id TEXT,
    device_name TEXT,
    wpplusdem1 REAL,
    wp_dem1 REAL,
    wqlagdem1 REAL,
    wqleaddem1 REAL,
    pdemplus1 REAL,
    pdem_1 REAL,
    qdemlag1 REAL,
    qdemlead1 REAL,
    PRIMARY KEY (date_time, device_id)
);

```




