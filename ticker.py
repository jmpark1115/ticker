"""
빗썸과 코인원의 시세를 조회한다
"""
import requests
import json

print("빗썸과 코인원의 시세를 조회합니다")

url = "https://api.bithumb.com/public/ticker/ALL"
res = requests.get(url)
ticker = json.loads(res.content)
bBTC = int(ticker['data']['BTC']['closing_price'])
print("Bithumb BTC(%.2f)" % bBTC )

#coinone
url = 'https://api.coinone.co.kr/ticker'
data = {'currency' : 'all'}
res = requests.get(url, params=data)
ticker = json.loads(res.content)
temp = ticker['btc']['last']
cBTC = int(float(ticker['btc']['last'])) # 소숫점이 있어 float 으로 변환 후 int 함.
print("Coinone BTC(%.2f)" % cBTC)

