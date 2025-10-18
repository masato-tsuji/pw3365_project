# backend/src/utils/notify_pub.py
# メインDBに対して購読開始の通知を行うユーティリティモジュール
# subscription_id と接続元IPアドレスを登録する
# admin.subscription_control テーブルに対してUPSERTを実行
# テーブルにインサート又はstatusを更新したらDB側のトリガで購読を制御
# subscription_id は代表MACアドレスを元に生成
# 接続元IPアドレスはメインDBに接続可能なローカルIPを使用
# 通知はメインDBに疎通できる場合のみ実行
# メインDBに疎通できない場合は通知をスキップ
# 単独実行例:
#   python src/utils/notify_pub.py
# これを単体でcron等から定期実行
#

import psycopg2
from datetime import datetime, timezone
from src.config.config_loader import load_config
from src.utils.get_mac_id import get_representative_mac
from src.utils.netcheck import is_reachable_main_db

# subscription_id を生成する関数
def get_subscription_id():
    mac = get_representative_mac()
    return f"sub_{mac}"

# main DBに接続できるIPアドレスを取得する関数
def get_local_ip():
    return is_reachable_main_db()['src']

def notify_main_db(subscription_id, ip_address):
    try:
        db_conf = load_config()["db"]["main"]
        print(db_conf)
        conn = psycopg2.connect(
            host=db_conf['host'],      # ← メインDBのホスト名またはIP
            dbname=db_conf['dbname'],         # ← メインDB名
            user=db_conf['user'],         # ← メインDBの通知用ユーザー
            password=db_conf['password']
        )
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO admin.subscription_control (subscription_id, ip_address, status, updated_at)
            VALUES (%s, %s, 'start', %s)
            ON CONFLICT (subscription_id) DO UPDATE
            SET ip_address = EXCLUDED.ip_address,
                status = EXCLUDED.status,
                updated_at = EXCLUDED.updated_at;
        """, (subscription_id, ip_address, datetime.now(timezone.utc)))
        conn.commit()
        cur.close()
        conn.close()
        print(f"通知成功: {subscription_id} ({ip_address})")
    except Exception as e:
        print(f"通知失敗: {e}")


if __name__ == "__main__":
    # 実行処理
    ip_address = get_local_ip() # メインDBに接続できるIPアドレスを取得

    if ip_address:
        subscription_id = get_subscription_id()
        notify_main_db(subscription_id, ip_address)
    else:
        print(f"{datetime.now()} メインDBに疎通できません。通知は保留されました。")


