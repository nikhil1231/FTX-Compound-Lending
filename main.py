from client import FtxClient
import configparser
import schedule
import os
import datetime as dt
import time
import csv

DATA_PATH = 'data.csv'

config = configparser.ConfigParser()
config.read('config.ini')

client = FtxClient(api_key=config['ftx']['api'], api_secret=config['ftx']['secret'], subaccount_name='Lending')

coins = ['USD', 'USDT']
headers = ['datetime'] + [c + ' APR' for c in coins] + [c + ' APY' for c in coins]

def convert_to_apr(hourly_rate):
  return round(hourly_rate * 24 * 365, 3)

def convert_to_apy(hourly_rate):
  return round((1 + (hourly_rate * 24)) ** 365, 3)

def get_rates():
  rates = client.get_lending_rates()
  rates = [x for x in rates if x['coin'] in coins]

  return {coin['coin']: coin['previous'] for coin in rates}

def init_csv():
  with open(DATA_PATH, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(headers)

def record_rates():
  rates = get_rates()

  d = dt.datetime.now()
  row = [d] + [convert_to_apr(rates[coin]) for coin in coins] + [convert_to_apy(rates[coin]) for coin in coins]

  print(f"Writing at {d}")

  with open(DATA_PATH, 'a', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(row)

def compound_lending():
  lending_info = client.get_lending_info()

  for coin_lending_info in lending_info:
    if coin_lending_info['lendable'] > 0.0:
      client.submit_lending_offer(coin_lending_info['coin'], coin_lending_info['lendable'], coin_lending_info['minRate'])

if __name__ == '__main__':
  if not os.path.exists(DATA_PATH):
    init_csv()

  schedule.every().hour.at(':04').do(record_rates)
  schedule.every().hour.at(':05').do(compound_lending)

  while True:
    schedule.run_pending()
    time.sleep(1)
