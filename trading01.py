#!/usr/bin/env python
# 이 프로그램은 빗썸과 코인원간 거래 데모 프로그램이다.

import logging
import logging.handlers
import time

from bithumb import Bithumb
from coinone import Coinone


from configparser import ConfigParser, NoSectionError


class Coin(object):
    def __init__(self):
        self.trade_max_volume = 0
        self.trade_min_thresh = 0
        self.targetSum        = 0
        self.baseSum          = 0
        self.targetCurrency   = 'BTC'
        self.baseCurrency     = 'KRW'
        self.paymentCurrency  = 'KRW'
        self.profit = 0
        self.hit = 0
        self.temp_interval    =  0
        self.update_delay     = 10  # sec
        self.last_update      = 0
        self.bithumb_enabled  = False
        self.traded           = False
        self.dryrun           = 1
        self.rate             = 1.001
        self.interval         = 5
        self.max              = 0
        self.thresh           = 0
        self.loop_number      = 0
        self.markets  = []
        self.observer = []


    def cal_profit(self, _from, _to):
        #from: ask market, buy  exchanger
        #to  : bid market, sell exchanger

        #determine tradesize
        # self.trade_max_volume = 10
        # TradeSize = min(_from.askqty, _to.bidqty, self.trade_max_volume)
        TradeSize = min(_from.askqty, _to.bidqty, self.trade_max_volume)

        SellBalance = _to.targetBalance
        BuyBalance  = _from.baseBalance

        if (TradeSize > SellBalance):
            TradeSize = SellBalance
        if(TradeSize * _from.askprice > BuyBalance):
            TradeSize = BuyBalance / _from.askprice
        TradeSize = int(TradeSize) #truncate under point
        Profit    = TradeSize *(_to.bidprice - _from.askprice) - TradeSize*2*0.001
        return TradeSize, Profit

    def main(self):

        # Create Logger
        logger = logging.getLogger()
        logger.setLevel(logging.NOTSET)
        # Create console handler and set level to debug
        sh = logging.StreamHandler()
        sh.setLevel(logging.DEBUG)
        # Create file handler and set level to debug
        fh = logging.FileHandler('mylog.txt', mode='a')
        fh.setLevel(logging.INFO)

        # Create formatter
        #formatter = logging.Formatter('%(asctime)s %(filename)s %(message)s')
        formatter = logging.Formatter('%(asctime)s %(message)s')
        # Add formatter to handlers
        sh.setFormatter(formatter)
        fh.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(sh)
        logger.addHandler(fh)

        # Load Config File
        config = ConfigParser()
        config.read('trading.conf')

        bithumbKey = config.get('ArbBot', 'bithumbKey')
        bithumbSecret = config.get('ArbBot', 'bithumbSecret')
        coinoneKey = config.get('ArbBot', 'coinoneKey')
        coinoneSecret = config.get('ArbBot', 'coinoneSecret')
        korbitKey = config.get('ArbBot', 'korbitKey')
        korbitSecret = config.get('ArbBot', 'korbitSecret')

        chat_id = config.get('ChatBot', 'chatId')
        chat_token = config.get('ChatBot', 'chatToken')

        coin_name = config.get('ArbBot', 'Coin')
        imarket    = config.get(coin_name, 'market')
        self.trade_max_volume = (float)(config.get(coin_name, 'TRADE_MAX_VOLUME'))
        self.trade_min_thresh = (float)(config.get(coin_name,'TRADE_MIN_THRESH'))

        self.dryrun = (int)(config.get('ArbBot', 'dryrun'))


        # Load Configuration
        self.targetCurrency  = coin_name
        self.baseCurrency    = 'KRW'
        self.paymentCurrency = 'KRW'

        # Create Exchange API Objects
        bithumbAPI = Bithumb(bithumbKey, bithumbSecret)
        coinoneAPI = Coinone(coinoneKey, coinoneSecret)

        # Main Loop
        self.markets.append(bithumbAPI)
        self.markets.append(coinoneAPI)

        #check balance bithumb and coinone
        print("===check balance")
        response = bithumbAPI.balance(self.targetCurrency)
        status = 'OK' if response['status'] == "0000" else "ERROR"
        print(status)
        bithumbAPI.targetBalance = (float)(response["data"]["available_" + self.targetCurrency.lower()])
        bithumbAPI.baseBalance   = (float)(response["data"]["available_" + self.baseCurrency.lower()])
        logging.info("**{} : (tBal: {:.8f}) | (pBal: {:.4f})**"
              .format("bithumb", bithumbAPI.targetBalance, bithumbAPI.baseBalance))


        #coinone
        response = coinoneAPI.balance()
        status = 'OK' if response['errorCode'] == "0" else "ERROR"
        print(status)
        coinoneAPI.targetBalance = (float)(response[self.targetCurrency.lower()]["avail"])
        coinoneAPI.baseBalance   = (float)(response[self.baseCurrency.lower()]["avail"])
        logging.info("**{} : (tBal: {:.8f}) | (pBal: {:.4f})**"
                     .format("coinone", coinoneAPI.targetBalance, coinoneAPI.baseBalance))

        if(self.dryrun):
            bithumbAPI.targetBalance = 100
            bithumbAPI.baseBalance   = 100000000
            coinoneAPI.targetBalance = 100
            coinoneAPI.baseBalance   = 100000000

        while True:
            #check price the target
            response = bithumbAPI.orderbook(self.targetCurrency)
            bithumbAPI.askprice = float(response["data"]["asks"][0]["price"])
            bithumbAPI.bidprice = float(response["data"]["bids"][0]["price"])
            bithumbAPI.askqty   = float(response["data"]["asks"][0]["quantity"])
            bithumbAPI.bidqty   = float(response["data"]["bids"][0]["quantity"])
            logging.info("**{} : ask {:.0f} bid {:.0f} askqty {:.4f} bidqty {:.4f}"
                         .format("bithumb", bithumbAPI.askprice,bithumbAPI.bidprice, \
                         bithumbAPI.askqty,bithumbAPI.bidqty ))

            response = coinoneAPI.orderbook(self.targetCurrency)
            coinoneAPI.askprice = float(response['ask'][0]['price'])
            coinoneAPI.askqty   = float(response['ask'][0]['qty'])
            coinoneAPI.bidprice = float(response['bid'][0]['price'])
            coinoneAPI.bidqty   = float(response['bid'][0]['qty'])
            logging.info("**{} : ask {:.0f} bid {:.0f} askqty {:.4f} bidqty {:.4f}"
                         .format("coinone", coinoneAPI.askprice,coinoneAPI.bidprice, \
                         coinoneAPI.askqty,coinoneAPI.bidqty ))

            #test s
            # bithumbAPI.askprice = 950
            # coinoneAPI.bidprice = 960
            #test e

            #find the chance
            if(bithumbAPI.askprice < coinoneAPI.bidprice):
                logging.info("do trading bithumb buy coinone sell !!!")
                TradeSize, Profit = self.cal_profit(bithumbAPI, coinoneAPI)
                self.trade_min_thresh = 10
                if(TradeSize > self.trade_min_thresh and Profit > 0):
                    print("start trading1 TS[%d] Profit[%d]" % (TradeSize, Profit))
                    if(dryrun==0):
                        bithumbAPI.buy(self.targetCurrency, TradeSize,bithumbAPI.askprice)
                        coinoneAPI.sell(self.targetCurrency, TradeSize, coinoneAPI.bidprice)
                else:
                    print("skip trading1 TS[%d] Profit[%d]" %(TradeSize, Profit))
            elif(coinoneAPI.askprice < bithumbAPI.bidprice):
                logging.info("do trading coinone buy bithumb sell !!!")
                TradeSize, Profit = self.cal_profit(coinoneAPI, bithumbAPI)
                self.trade_min_thresh = 10
                if (TradeSize > self.trade_min_thresh and Profit > 10):
                    print("start trading2 TS[%d] Profit[%d]" % (TradeSize, Profit))
                    if(dryrun==0):
                        coinoneAPI.buy(self.targetCurrency, TradeSize, coinoneAPI.askprice)
                        bithumbAPI.sell(self.targetCurrency, TradeSize, bithumbAPI.bidprice)
                else:
                    print("skip trading2 TS[%d] Profit[%d]" % (TradeSize, Profit))
            else:
                logging.info("..")

            time.sleep(5)

if __name__ == "__main__":
    print("Arbitrage start")
    coin = Coin()
    coin.main()