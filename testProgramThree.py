import os
import os.path
import sys
import requests
import json
from selenium import webdriver
from shutil import which
import urllib.parse as up
import pandas as pd
import requests
from pandas.io.json import json_normalize
from datetime import datetime
import time
from urllib.parse import unquote
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib import style
import pandas_datareader.data as web


class Td:

    def __init__(self, client_id):
        self.client_id = client_id
        self.main()


    def main(self):
        myFile = Path('RefreshToken.txt')
        if myFile.is_file():
            self
        else:
            self.auth_code()
            

    def auth_code(self):

        print('Auth Code Working.............')
        print('-------')

        client_id = self.client_id
        url = 'https://auth.tdameritrade.com/auth?response_type=code&redirect_uri=' + up.quote('http://localhost:8080') + '&client_id=' + up.quote(client_id)

        options = webdriver.ChromeOptions()

        if sys.platform == 'darwin':
        # MacOS
            if os.path.exists("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
                options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            elif os.path.exists("/Applications/Chrome.app/Contents/MacOS/Google Chrome"):
                options.binary_location = "/Applications/Chrome.app/Contents/MacOS/Google Chrome"
            
        
        PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
        
        chrome_driver_binary = os.path.join(PROJECT_ROOT, "chromedriver")
        driver = webdriver.Chrome(chrome_driver_binary, options=options)

        driver.get(url)

        input('after giving access, hit enter to continue')

        code = up.unquote(driver.current_url.split('code=')[1])

        driver.close()

        authreply = requests.post('https://api.tdameritrade.com/v1/oauth2/token',
                             headers={'Content-Type': 'application/x-www-form-urlencoded'},
                             data={'grant_type': 'authorization_code',
                                   'refresh_token': '',
                                   'access_type': 'offline',
                                   'code': code,
                                   'client_id': client_id,
                                   'redirect_uri': 'http://localhost:8080'})

        if authreply.status_code != 200:
            raise Exception('Could not authenticate!')
        else:
            data = authreply.json()
            refresh_token = data['refresh_token']
            f = open('authtoken.txt', 'w+')
            f.write(refresh_token)
            f.close()
            return refresh_token


    def getTokenFromFile(self):
        myFile = Path('authtoken.txt')
        if myFile.is_file():
            f = open('authtoken.txt', 'r')
            print('Accessed File')
            print('-----------------')
            if f.mode == 'r':
                token = f.read()
                print('Refresh Token on File: ' + token)
                print('--------------')
                f.close()
                return token



    def getNewRefreshToken(self):
        
        token = self.getTokenFromFile()
    
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': token,
            'access_type': 'offline',
            'client_id': self.client_id,
            'redirect_uri': 'http://localhost:8080'
        }
        authReply = requests.post(
            'https://api.tdameritrade.com/v1/oauth2/token',
            headers=headers,
            data=data)
        if authReply.status_code == 200:
            authReplyData = authReply.json()
            newRefreshTokenOnFile = authReplyData['access_token']
            print('New Refresh Token on File: ' + newRefreshTokenOnFile)
            print('__________________________')
            f = open('RefreshToken.txt', 'w+')
            f.write(newRefreshTokenOnFile)
            f.close()
            return newRefreshTokenOnFile
        else:
            self.auth_code()
            self.getNewRefreshToken()


            

    def get_price_history(self, symbol, startDate=None, endDate=None):

        access_token = self.getNewRefreshToken()
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Bearer {}'.format(access_token)
        }
        data = {
            'periodType': 'year',
            'frequencyType': 'daily',
            'startDate': startDate,
            'endDate': endDate
        }
        authReply = requests.get(
            'https://api.tdameritrade.com/v1/marketdata/' + symbol +
            '/pricehistory',
            headers=headers,
            params=data)
        candles = authReply.json()
        df = json_normalize(authReply.json())
        
        df = pd.DataFrame(candles.get('candles'))
        df['100ma'] = df['close'].rolling(window=100, min_periods=0).mean()
        ax1 = plt.subplot2grid((6,1), (0,0), rowspan = 5, colspan = 1)
        ax2 = plt.subplot2grid((6,1), (5,0), rowspan = 1, colspan = 1, sharex = ax1)
        ax1.plot(df.index, df.get('close'))
        ax1.plot(df.index, df.get('100ma'))
        ax2.bar(df.index, df.get('volume'))
        plt.show()
        

        return df

    def unix_time_millis(self, dt):
        epoch = datetime.utcfromtimestamp(0)
        return int((dt - epoch).total_seconds() * 1000.0)

    def get_quotes(self, symbol):
        access_token = self.getNewRefreshToken()
       
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Bearer {}'.format(access_token)
        }
        data = {'symbol': symbol, 'apikey': self.client_id}
        authReply = requests.get(
            'https://api.tdameritrade.com/v1/marketdata/quotes',
            headers=headers,
            params=data)
        data = authReply.json()
        symbol = data.get('symbol')
        return data

    def get_option_chain(self, symbol, contractType, strikeCount, interval, strike,   startDate=None, endDate=None):
        access_token = self.getNewRefreshToken()
        headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': 'Bearer {}'.format(access_token)
            }
        data = {
                'symbol': symbol,
                'contractType': contractType,
                'strikeCount' : strikeCount,
                'includeQuotes' : 'FALSE',
                'strategy' : 'SINGLE',
                'interval' : interval,
                'strike' : strike,
                'range' : 'ALL',
                'fromDate' : startDate,
                'toDate' : endDate,
                'volatility' : '',
                'underlyingPrice' : '',
                'interestRate' : '',
                'daysToExpiration' : '',
                'expMonth' : 'ALL',
                'optionType' : 'ALL'
            }
        authReply = requests.get(
                'https://api.tdameritrade.com/v1/marketdata/chains',
                headers=headers,
                params=data)
        candles = authReply.json()
        df = json_normalize(authReply.json())
        df = pd.DataFrame(candles)
        return candles





start_date = datetime.strptime('01 01 2018  9:00AM', '%m %d %Y %I:%M%p')
end_date = datetime.strptime('01 11 2019  4:00PM', '%m %d %Y %I:%M%p')
##end_date = datetime.now()
p = Td('IPHONETWO@AMER.OAUTHAP')
##print(p.unix_time_millis(start_date))
##print(p.unix_time_millis(end_date))   
print(p.get_price_history('SPY', p.unix_time_millis(start_date),p.unix_time_millis(end_date)))
print(p.get_quotes('SPY'))
print(p.get_option_chain('SPY', 'CALL', '1', '1', '250',   '2019-01-08', '2019-01-09'))

        
