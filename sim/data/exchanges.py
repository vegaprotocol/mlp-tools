import requests
import json
import os

from prelude import *


class DataSource(Data):
	cache_dir: Optional[str] = None

	def get_cached_json(self, url, cache_file=None, force=False):
		cache_path = self.cache_dir and cache_file and os.path.join(self.cache_dir, cache_file)
		
		# Load from cache file
		if cache_path != None and (not force) and os.path.isfile(cache_path):
			try:
				with open(cache_path, 'r') as f: 
					return json.load(f)
			except:
				pass  # this except clause is in case the file doesn't contain valid JSON

		# Download afresh
		data = requests.get(url).json()
		if cache_path != None: 
			with open(cache_path, 'w') as f: 
				json.dump(data, f)
		return data


class FTX(DataSource):
	API = 'https://ftx.com/api/{}'.format
	API_HISTORY = 'markets/{market}/candles?resolution={resolution}'.format

	def get_markets(self, force=False):
		cache_file = f'FTX_{market_id}_markets.json'
		url = FTX.API('markets')
		return self.get_cached_json(url=url, cache_file=cache_file, force=force)['result']

	def get_history(self, market_id, resolution=86400, force=False):
		cache_file = f'FTX_{market_id}_history_{resolution}.json'
		url = FTX.API(FTX.API_HISTORY(market=market_id, resolution=resolution))
		return self.get_cached_json(url=url, cache_file=cache_file, force=force)['result']
