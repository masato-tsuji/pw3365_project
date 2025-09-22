

# install module
pip install fastapi uvicorn psutil
sudo apt install iw


# start command (backend/ ディレクトリ内で実行)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# get command
curl http://localhost:8000/meter/pw3365/test

- main.py側でmeterのprefixをつけている
- pw3365_api.py側でpw3365のprefixをつけている
- 今後pw3365以外も増やしたときにmeterの配下にできる利点がある



# tests
pytest
testsディレクトリの下にtest_***.pyファイルを配置
rootディレクトリでpytestを実行

