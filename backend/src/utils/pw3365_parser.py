# src/utils/pw3365_parser.py
from datetime import datetime, timezone
import re

def convert_e_notation(value: str) -> float | str:
    """E表記を浮動小数点に変換。変換できなければ文字列のまま返す"""
    try:
        if re.match(r'^-?\d+(\.\d+)?[eE][-+]?\d+$', value):
            return float(value)
        return value
    except ValueError:
        return value

def parse_raw_data(raw_data: str) -> dict:
    """PW3365の生データ文字列を辞書に変換"""
    parts = raw_data.strip().split(';')
    result = {}

    # タイムスタンプ作成(計器の時計はずれている可能性があるので現在時刻を使用)
    # UTCに対応を検討（timescaledbのタイムゾーンに合わせるため）
    timestamp = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    result['date_time'] = timestamp

    for part in parts:
        if not part:
            continue
        try:
            key, value = part.split(maxsplit=1) if ' ' in part else part.split('=', 1)
        except ValueError:
            continue
        # カラム名変換: - -> _, + -> Plus など
        key = key.replace('-', '_').replace('+', 'Plus').replace('/', '_')
        result[key] = convert_e_notation(value)
    return result
