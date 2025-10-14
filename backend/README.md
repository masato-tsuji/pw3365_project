

# install module
pip install fastapi uvicorn psutil
sudo apt install iw
sudo apt install jq


# start command (backend/ ディレクトリ内で実行)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000    # srcディレクトリなら


# get command
curl http://localhost:8000/api/network/status | jq



