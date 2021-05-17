import numpy as np
import time
import sched
import tulipy as ti
import argparse
from pyrh import Robinhood
from datetime import datetime


class RHTrader:
    """
    Algorithmic trader using Robinhood API to enter positions based on RSI period and historical prices.
    """
    def __init__(self, username, pwd, rsi=5):
        self.rh = Robinhood()
        self.rh.login(username=username, password=pwd)
        self.rsiPeriod = rsi
        self.enteredPosition = False
        self.s = sched.scheduler(time.time, time.sleep)
        self.data = np.array([])
        self.closePrices = []

    def populate(self):
        historical_quotes = self.rh.get_historical_quotes("F", "5minute", "day")
        index = 0
        support = 0
        resistance = 0
        for key in historical_quotes["results"][0]["historicals"]:
            if index >= len(historical_quotes["results"][0]["historicals"]) - (self.rsiPeriod + 1):
                if (index >= (self.rsiPeriod - 1) and datetime.strptime(key['begins_at'],
                                                                               '%Y-%m-%dT%H:%M:%SZ').minute == 0):
                    support = 0
                    resistance = 0
                    print("Resetting support and resistance")
                if float(key['close_price']) < support or support == 0:
                    support = float(key['close_price'])
                    print("Current Support is : ")
                    print(support)
                if float(key['close_price']) > resistance:
                    resistance = float(key['close_price'])
                    print("Current Resistance is : ")
                    print(resistance)
                self.closePrices.append(float(key['close_price']))
            index += 1
        self.data = np.array(self.closePrices)

    def execute(self, sc):
        if len(self.closePrices) > self.rsiPeriod:
            # Calculate RSI
            rsi = ti.rsi(self.data, period=self.rsiPeriod)
            instrument = self.rh.instruments("F")[0]
            # If rsi is less than or equal to 30 buy
            if rsi[len(rsi) - 1] <= 30 and not self.enteredPosition:
                print("Buying RSI is below 30!")
                self.rh.place_buy_order(instrument, 1)
                self.enteredPosition = True
            # Sell when RSI reaches 70
            if rsi[len(rsi) - 1] >= 70 and self.enteredPosition:
                print("Selling RSI is above 70!")
                self.rh.place_sell_order(instrument, 1)
                self.enteredPosition = False
            print(rsi)
            # call this method again every 5 minutes for new price changes
        self.s.enter(300, 1, self.execute, (sc,))

    def run(self):
        self.s.enter(1, 1, self.execute, (self.s,))
        self.s.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Robinhood Login Information")
    parser.add_argument("-u", "--username", type=str, help="Login username", required=True)
    parser.add_argument('-p', "--password", type=str, help="Login password", required=True)
    login = parser.parse_args()

    trader = RHTrader(login["username"], login["password"])
    trader.populate()
    trader.run()
