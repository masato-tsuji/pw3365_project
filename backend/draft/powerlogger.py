import socket
import time
from datetime import datetime, timedelta
import os
import re
import sys

# 通信設定
HOST = '192.168.0.31'  # PW3365のIPアドレス
PORT = 3365            # 通信ポート
HEADER_ON = ':HEADER ON\r\n'  # ヘッダーON
HEADER_OFF = ':HEADER OFF\r\n'  # ヘッダーOFF
HEADER_COMMAND = HEADER_ON
SET_COMMAND = ':MEASure:ITEM:POWer 15,207,247,31,15,15\r\n'  # 出力項目設定コマンド
DEFAULT_READ_COMMAND = ':MEASure:POWer?\r\n'  # データ取得コマンド
INTERVAL_MINUTES = 5  # 通常モードの取得間隔（分）

# 保存先のCSVファイル設定
HOME_DIR = os.path.expanduser('~')
start_time_str = datetime.now().strftime('%Y%m%d_%H%M')
CSV_FILENAME = f'pw3365_pow_data_{start_time_str}.csv'
CSV_PATH = os.path.join(HOME_DIR, CSV_FILENAME)

# E表記（指数表記）のみを実数に変換する関数
def convert_e_notation(value):
    try:
        # E表記かどうかを判定して変換
        if re.match(r'^-?\d+(\.\d+)?[eE][-+]?\d+$', value):
            return str(float(value))
        else:
            return value  # 通常の数値はそのまま
    except ValueError:
        return value  # 数値でない場合もそのまま

# データ整形：セミコロン区切り→カンマ区切り、E表記→実数変換
def process_data(raw_data):
    # タイムスタンプ作成（計器の時計ではなく処理した時間にする）
    now = datetime.now()
    new_dt = now.replace(second=0, microsecond=0)
    timestamp = new_dt.strftime("%Y-%m-%d %H:%M:%S")

    # CSVに成形
    parts = raw_data.split(';')
    converted = [convert_e_notation(part.strip()) for part in parts]
    csv_datas = converted[6:]
    csv_datas.insert(0, timestamp)
    csv_datas = ','.join(converted)
    return csv_datas

# PW3365にコマンドを送信し、応答を取得する関数
def send_command(command, debug=False, oneshot=False):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))

            # ヘッダー出力
            if debug or oneshot:
                s.sendall(HEADER_COMMAND.encode())
                header_recv = s.recv(4096).decode().strip()

            # 出力項目の設定（毎回送信）
            s.sendall(SET_COMMAND.encode())
            set_recv = s.recv(4096).decode().strip()
            if debug:
                print(f"[DEBUG] Sending: {SET_COMMAND.strip()}")
                print(f"[DEBUG] Receive: {set_recv}")
            time.sleep(0.5)  # 設定反映のため少し待機

            # 実行コマンド送信
            if debug:
                print(f"[DEBUG] Sending: {command.strip()}")
            s.sendall(command.encode())
            # バッファの終わりを検知するためALL RIGHTの文字を返すクエリも送信
            s.sendall(SET_COMMAND.encode())

            # 応答受信（ALL RIGHTが含まれるまでループ
            raw_data = "" 
            while "ALL RIGHT" not in raw_data:
                raw_data += s.recv(4096).decode().strip()
            raw_data = raw_data.replace("ALL RIGHT", "")
            
            # 残りのバッファの読み出し（HEADRのON/OFFによって回数違う）
            #if command == DEFAULT_READ_COMMAND:
            #    for i in range(1 if HEADER_COMMAND==HEADER_OFF else 3):
            #        raw_data += s.recv(4096).decode().strip()

            if debug:
                print("-"*30 + " raw_data " + "-"*30)
                print(f"[DEBUG] Received raw: {raw_data}")
                print("-"*50)
            return raw_data

    except Exception as e:
        print(f"Error: {e}")
        return None

# 通常モード：データ取得してCSVに保存
def get_pow_data():
    raw_data = send_command(DEFAULT_READ_COMMAND)
    if raw_data:
        processed_data = process_data(raw_data)
        with open(CSV_PATH, 'a') as f:
            f.write(processed_data + '\n')
        print(f"[{datetime.now()}] Data saved.")

# 次の取得タイミングまで待機する関数
def wait_until_next_cycle():
    now = datetime.now()
    minute = (now.minute // INTERVAL_MINUTES) * INTERVAL_MINUTES
    next_time = now.replace(minute=minute, second=0, microsecond=0)
    if now >= next_time:
        next_time += timedelta(minutes=INTERVAL_MINUTES)
    wait_seconds = (next_time - now).total_seconds()
    print(f"Waiting {wait_seconds:.1f} seconds until next cycle at {next_time}")
    time.sleep(wait_seconds)

# メイン処理：引数によってモードを切り替える
def main():
    args = sys.argv[1:]

    # ワンショットモード（引数に 'oneshot' がある場合）
    if args and args[0] == 'oneshot':
        custom_command = args[1] if len(args) > 1 and not args[1].lower() == 'debug' else DEFAULT_READ_COMMAND
        debug = 'debug' in [arg.lower() for arg in args]

        raw_data = send_command(custom_command, debug=debug, oneshot=True)
        if raw_data:
            processed_data = process_data(raw_data)
            print("Processed Data:", processed_data)
            with open(CSV_PATH, 'a') as f:
                f.write(processed_data + '\n')
                

    # 通常モード（10分間隔で取得・保存）
    else:
        while True:
            wait_until_next_cycle()
            get_pow_data()

if __name__ == '__main__':
    main()
