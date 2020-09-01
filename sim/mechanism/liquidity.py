from prelude import *


class Liquidity(Data):
	'''
	Liquidity engine
	'''

	# v: [network] this parameter is the multiple of the margin required as coverage to secure the minimum stake obligation
	v: float = 5

	# k: [network] this sets obligation (siskas), i.e. obligation = k * comitted stake
	k: float = 1

	# stake_target_period: [network] take MAXIMUM open interest over this period when calculating stake target
	stake_target_period: int = 7

	# valuation_period: [netowrk] take SUM of traded volume over this period when calculating "valuation"
	valuation_period: int = 1