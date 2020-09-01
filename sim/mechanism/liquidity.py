from prelude import *


class Liquidity(Data):
	'''
	Liquidity engine
	'''

	# c2: [network] this is the  multiple of open interest that we target for coverage by liquidity providers
	c2: float = 1

	# v: [network] this parameter is the multiple of the target coverage required as stake to secure the obligation
	v: float = 5

	# k: [network] this sets obligation (siskas), i.e. obligation = k * comitted stake
	k: float = 1

	# stake_target_period: [network] take MAXIMUM open interest over this period when calculating stake target
	stake_target_period: int = 7

	# valuation_period: [netowrk] take SUM of traded volume over this period when calculating "valuation"
	valuation_period: int = 1