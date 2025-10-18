import psycopg2
import logging
from src.config.config_loader import load_config
from src.utils.get_mac_id import get_representative_mac

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 接続情報（辻さん指定）
EDGE_DB_CONFIG = {
    'host': '172.21.206.157',
    'port': 5432,
    'dbname': 'bems_test',
    'user': 'postgres',
    'password': 'postgres'
}

MAIN_DB_CONFIG = {
    'host': '161.94.139.28',
    'port': 5432,
    'dbname': 'tecs_data',
    'user': 'postgres',
    'password': 'postgres'
}

tables = 'iot_data.pw3365_current, iot_data.pw3365_demand, ' \
'iot_data.pw3365_energy, iot_data.pw3365_freq, iot_data.pw3365_power, iot_data.pw3365_voltage'

mac = get_representative_mac()
PUBLICATION_NAME = f'pub_{mac}'
SUBSCRIPTION_NAME = f'sub_{mac}'

# autocommit対応の接続関数
def connect_db(config, autocommit=False):
    conn = psycopg2.connect(**config)
    if autocommit:
        conn.autocommit = True
    return conn

def ensure_publication(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_publication WHERE pubname = %s", (PUBLICATION_NAME,))
        if cur.fetchone():
            logging.info("Publication already exists. Skipping creation.")
        else:
            cur.execute(f"CREATE PUBLICATION {PUBLICATION_NAME} FOR TABLE {tables};")
            conn.commit()
            logging.info("Publication created successfully.")

# 
def ensure_subscription(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_subscription WHERE subname = %s", (SUBSCRIPTION_NAME,))
        if cur.fetchone():
            logging.info("Subscription already exists. Skipping creation.")
        else:
            conn_str = f"host={EDGE_DB_CONFIG['host']} port={EDGE_DB_CONFIG['port']} dbname={EDGE_DB_CONFIG['dbname']} user={EDGE_DB_CONFIG['user']} password={EDGE_DB_CONFIG['password']}"
            cur.execute(f"""
                CREATE SUBSCRIPTION {SUBSCRIPTION_NAME}
                CONNECTION '{conn_str}'
                PUBLICATION {PUBLICATION_NAME}
                WITH (create_slot = true, enabled = true);
            """)
            logging.info("Subscription created successfully.")

# 実行
try:
    edge_conn = connect_db(EDGE_DB_CONFIG)
    ensure_publication(edge_conn)
    edge_conn.close()

    main_conn = connect_db(MAIN_DB_CONFIG, autocommit=True)
    ensure_subscription(main_conn)
    main_conn.close()

except Exception as e:
    logging.error(f"Error occurred: {e}")