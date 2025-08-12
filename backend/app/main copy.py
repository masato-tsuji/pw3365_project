




def insert_dict_to_timescaledb(data_dict: dict):
    if not DB_AVAILABLE or not ENABLE_DB:
        print("DB insert skipped.")
        return

    import psycopg2

    # カテゴリごとのキー判定ルール
    category_keys = {
        "pw3365_voltage": ["U1_", "Ufnd", "Udeg"],
        "pw3365_current": ["I1_", "Ifnd", "Ideg", "Ipeak"],
        "pw3365_power": ["P1_", "PF_", "S1_", "Q1_", "DPF"],
        "pw3365_energy": ["WP_Plus", "WP_Minus", "WQLAG", "WQLEAD", "Ecost"],
        "pw3365_demand": ["WP_Plus_dem", "WP_Minus_dem", "Pdem_", "Qdem_", "PF_dem"],
        "pw3365_freq": ["Freq_"]
    }

    # 共通キー（必須）
    common_keys = ["device_id", "timestamp"]

    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            dbname=PG_DBNAME,
            user=PG_USER,
            password=PG_PASSWORD
        )
        cur = conn.cursor()

        # カテゴリごとにデータを分割して挿入
        for table_name, prefixes in category_keys.items():
            sub_dict = {
                k: v
                for k, v in data_dict.items()
                if any(k.startswith(p) for p in prefixes)
            }

            # 共通キーを追加
            for ck in common_keys:
                if ck in data_dict:
                    sub_dict[ck] = data_dict[ck]

            if len(sub_dict) > len(common_keys):  # 実データがある場合のみ
                columns = ', '.join(sub_dict.keys())
                placeholders = ', '.join(['%s'] * len(sub_dict))
                values = list(sub_dict.values())

                query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders});"
                cur.execute(query, values)
                print(f"Inserted into {table_name}.")

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"TimescaleDB Error: {e}")
