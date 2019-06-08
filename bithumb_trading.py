# 이 프로그램은 빗썸 api 를 테스트하는 프로그램이다.

from bithumb import Bithumb
from configparser import ConfigParser, NoSectionError
import time

# Load Config File
config = ConfigParser()
config.read('trading.conf')

bithumbKey = config.get('ArbBot', 'bithumbKey')
bithumbSecret = config.get('ArbBot', 'bithumbSecret')

targetCurrency = 'XRP'
baseCurrency   = 'KRW'

# object created
bithumb = Bithumb(bithumbKey, bithumbSecret)


