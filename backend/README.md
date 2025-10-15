

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

scp -P 2222 core/services/pw3365_service.py tecsmnt@172.21.206.157:/home/tecsmnt/repositories/pw3365_project/backend/src/core/services/
scp -P 2222 core/services/insert_service.py tecsmnt@172.21.206.157:/home/tecsmnt/repositories/pw3365_project/backend/src/core/services/

scp -P 2222 utils/get_mac_id.py tecsmnt@172.21.206.157:/home/tecsmnt/repositories/pw3365_project/backend/src/utils/
scp -P 2222 utils/pw3365_parser.py tecsmnt@172.21.206.157:/home/tecsmnt/repositories/pw3365_project/backend/src/utils/
scp -P 2222 utils/pg_replication.py tecsmnt@172.21.206.157:/home/tecsmnt/repositories/pw3365_project/backend/src/utils/



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

-- エッジ側でパブリケーション作成
CREATE PUBLICATION edge_pub FOR ALL TABLES;

-- メインDBに接続してサブスクリプション作成
CREATE SUBSCRIPTION edge_sub
  CONNECTION 'host=db.example.com dbname=maindb user=replicator password=xxx'
  PUBLICATION edge_pub;

# ------------------------------------------------

# pw3365 関係テーブルスキーマ & timescaledbのhypertable作成
CREATE TABLE IF NOT EXISTS pw3365_voltage (
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
SELECT create_hypertable('pw3365_voltage', 'date_time', if_not_exists => TRUE);
------------------------------------------------
CREATE TABLE IF NOT EXISTS pw3365_current (
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
SELECT create_hypertable('pw3365_current', 'date_time', if_not_exists => TRUE);
------------------------------------------------
CREATE TABLE IF NOT EXISTS pw3365_freq (
    date_time TIMESTAMPTZ NOT NULL,
    device_id TEXT,
    device_name TEXT,
    freq_ins REAL,
    freq_avg REAL,
    freq_max REAL,
    freq_min REAL,
    PRIMARY KEY (date_time, device_id)
);
SELECT create_hypertable('pw3365_freq', 'date_time', if_not_exists => TRUE);
------------------------------------------------
CREATE TABLE IF NOT EXISTS pw3365_energy (
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
SELECT create_hypertable('pw3365_energy', 'date_time', if_not_exists => TRUE);
------------------------------------------------
CREATE TABLE IF NOT EXISTS pw3365_demand (
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
SELECT create_hypertable('pw3365_demand', 'date_time', if_not_exists => TRUE);

