# Markets and Liquidity Programme tools

Tools for members of the Vega Markets and Liquidity Programme

This is a collection of Python classes / Python scripts and Jupyter notebooks that can be used to experiment with some aspects of the Vega protocol. Currently, only some aspects of market making and liquidity obligations and incentives are implemented but not much beyond this. In particular, this does not model trading itself (order matching, auctions, liquidity & price protection, positions, etc.). 


## Code license and additional disclaimer

See [LICENSE](LICENSE). Additional disclaimer:

```
THE SOFTWARE IS PROVIDED ON AN "AS IS" BASIS AND IS AN INCOMPLETE AND SIMPLIFIED 
SIMULATION OF SOME (BUT NOT ALL) ASPECTS OF THE VEGA TESTNET. IT MIGHT BEHAVE IN
UNEXPECTED WAYS AND OUTPUTS MAY CHANGE AT ANY TIME. DEVELOPMENT OF THIS TOOL IS
AN ONGOING EFFORT AND THE CODE, DATA, AND OTHER CONTENTS OF THIS REPOSITORY DO
NOT REPRESENT A STATEMENT ABOUT VEGA OR COMMITMENT THAT VEGA WILL BEHAVE IN ANY
SPECIFIC WAY OR BE USEFUL FOR ANY PURPOSE WHATSOEVER. ALL REFERENCES TO INCOME, 
PROFIT AND LOSSES, HISTORICAL AND RANDOMLY GENERATED DATA REFER TO THE 
SIMULATION, AND ARE FOR ILLUSTRATION PURPOSES ONLY.
```

## Requirements 

You will need Python >= 3.7.x and Jupyter notebooks installed. A possible starting point for Jupyer Notebooks is is https://jupyter-notebook-beginner-guide.readthedocs.io/en/latest/. 

You will also need the following packages:

```
pandas
numpy
scipy
matplotlib
ipywidgets
requests
```

These packages may be installed by running `pip3 -r requirments.txt` in the root of the project, or may be installed manually.


## What is what

- `./data/` will be used to cache market data from other sources, which some of the notebooks will download.
- `./sim/mechanism/` contains Python libraries that implement the logic of the mechanism design. You can change these if you would like to experiment with changing the mechanism but it shouldn't be your starting point. Reading these may help you understand how Vega's mechanism works, although the documentation at this point is incomplete.
- `./notebooks/` are the Python notebooks that show some aspects of the design. *These* should be the starting point for your exploration.


## How to use

This tool models how Vega's liquidity rewards adjust depending on the daily traded notional value, market maker commitment stakes and fee bids (placed by the market makers). It also calculates a market's target liquidity which can be compared against the total committed liquidity, to ascertain if/when a market is under/over supplied. Finally, it calculates for each market maker, the margin amounts that are incurred as a result from their order book obligations.

It makes no assumption about the amount of volume that a market maker will trade, nor the corresponding inventory risk.

For a simple example start with [liquidity_reward_distribution.ipynb](./notebooks/liquidity_reward_distribution.ipynb)


### Step 1 - setting up a market

A market is set up using the Market class in market.py. Each market has one risk model and one or more liquidity providers. 

The important parameters of the markets are:

	# v: [network] this parameter is an input to calculation of the target stake of the market and represents the degree of liquidity demand coverage
	
	# k: [network] this sets obligation (siskas), i.e. obligation = k * committed stake

	# stake_target_period: [network] take MAXIMUM open interest over this period when calculating stake target

	# valuation_period: [netowork] take SUM of traded volume over this period when calculating "valuation"


### Step 2 - creating liquidity provision commitments

Market maker commitments are comprised of the following data: (_day of obligation_, _name of market maker_, _stake-amount_, _fee bid_, _sell side orders_, _buy side orders_),

You can set up a sorted list, where each element corresponds to a new commitment on the market. We currently only support each new commitment representing a new market maker.

To set up the _sell side orders_ and _sell side orders_, you can use those supplied in example_data.py (or create your own). These orders are comprised of limit orders and a proportional allocation of the pegged liquidity orders that auto refresh to meet the commitment. The length of the order array represents the numbers of ticks from the mid.


### Step 3 - simulate the outcomes using daily data.

You can use daily market data from historical market data sets or simulate your own "daily market outcomes". The data required is 24hour-notional-volume, open-interest, price. See [liquidity_reward_distribution.ipynb](./notebooks/liquidity_reward_distribution.ipynb) for how to loop through the daily data and calculate daily liquidity characteristics.


### Step 4 - visualising the outcomes

Some plots have been scripted in [notebooks/_utils.py](./notebooks/_utils.py), these are used by a number of the provided notebooks and can be reused by providing your own. 
