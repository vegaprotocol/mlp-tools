import numpy as np
from scipy.stats import norm

from prelude import *
from .risk import *
import mechanism.market

# This cell implements the equity-like rewards and fee bidding mechanism
#
# Features so far:
#   - iterate through a market creating history as volume, open insterest, fees, and LP commitments change
#   - commit liquidity with stake and fee bid for an arbitrary number of LPs
#   - calculate equity and reward share for each LP
#   - calculate fees from fee bids and open interest
#   - set calculation window for demand proxy (stake target) and valuation (volume)
#
# Still to do:
#   - reduce size of existing commitment
#   - increase size of commitment


# To avoid division by zero errors
PROB_TO_L = 1e-10


class LiquidityProvider(Data):
    '''
    A liquidity provider's commitment and fee bid. Also calculates returns from liquidity rewards.
    '''

    market: 'Market'
    name: str
    stake: float
    fee_bid: float = 0.0
    sell_side_shape: Optional['OrderSetForSide'] = None
    buy_side_shape: Optional['OrderSetForSide'] = None
    entry_valuation: float = field(default=0, init=False)

    def __post_init__(self):
        self.entry_valuation = self.market.valuation  # TODO: update valuation
        self.market._lps[self.name] = self
        if self.sell_side_shape != None and self.sell_side_shape.is_sell_side == False:
            raise ValueError("Sell side should have 'is_sell_side'=True")
        if self.sell_side_shape != None and self.buy_side_shape.is_sell_side == True:
            raise ValueError("Buy side should have 'is_sell_side'=False")

    @property
    def margin(self):
        if self.sell_side_shape != None:
            sellShapeWithCurrentMarket = replace(
                self.sell_side_shape, market=self.market)
            sellVolArray = self.get_volume_meeting_obligation_from_shape(
                sellShapeWithCurrentMarket)
        if self.buy_side_shape != None:
            buyShapeWithCurrentMarket = replace(
                self.buy_side_shape, market=self.market)
            buyVolArray = self.get_volume_meeting_obligation_from_shape(
                buyShapeWithCurrentMarket)
        return (sellShapeWithCurrentMarket.CalculateMargin(sellVolArray) if self.sell_side_shape != None else 0) + \
               (buyShapeWithCurrentMarket.CalculateMargin(
                   buyVolArray) if self.buy_side_shape != None else 0)

    @property
    def obligation(self):
        return self.stake * self.market.liquidity.k

    @property
    def equity(self):
        # if self.entry_valuation > 0 else 0
        return (self.market.valuation / self.entry_valuation) * self.stake

    @property
    def equity_share(self):
        return self.equity / self.market.total_equity if self.market.total_equity > 0 else 0

    @property
    def stake_share(self):
        return self.stake / self.market.total_stake if self.market.total_stake > 0 else 0

    @property
    def fee_revenue(self):
        return self.market.fees_collected * self.equity_share

    @property
    def annualised_return(self):
        '''
        Calculates the return for this liquidity provider on current total stake if fee rate and volume remained
        constant for a year.
        '''
        return (365 * self.fee_revenue) / self.stake

    def get_volume_meeting_obligation_from_shape(self, orderSet: 'OrderSetForSide'):
        limitOrderLiquidity = orderSet.CalculateLimitOrderLiquidity()
        remainingObligation = max(
            self.obligation - limitOrderLiquidity, 0.0)
        vol_shape = self._normalise_fractions(orderSet.liquidity_fractions)

        impliedVolume = np.empty_like(vol_shape)
        for bookIdx in range(0, self.market.num_ticks):
            priceLevel = orderSet.priceList[bookIdx]
            probTrading = self.market.risk_model.ProbOfTrading(
                orderSet.mid, priceLevel)
            if probTrading > PROB_TO_L:
                impliedVolume[bookIdx] = remainingObligation * \
                    vol_shape[bookIdx] / probTrading / priceLevel

        return np.ceil(impliedVolume)

    def _normalise_fractions(self, liquidity_fractions):
        normFactor = np.sum(liquidity_fractions)
        if (normFactor <= 0.0):
            raise ValueError(
                "liquidity_fractions must have non-negative entries with at least one strictly positive")
        vol_shape = (1.0 / normFactor) * liquidity_fractions
        return vol_shape

    def check_if_volume_meets_obligation(self, orderVolArray: np.array, orderSet: 'OrderSetForSide'):
        if np.shape(orderVolArray) != (self.market.num_ticks, ):
            raise ValueError(
                "limitOrders array must have length equal to number of ticks on the book side.")

        limitOrderLiquidity = orderSet.CalculateLimitOrderLiquidity()
        additionalLiquidity = orderSet.CalculateLiquidity(
            orderVolArray)
        if (limitOrderLiquidity + additionalLiquidity > self.obligation):
            return True
        else:
            return False

    def __repr__(self):
        return f'{self.name}(stake={self.stake}, equity={self.equity_share:.1%}, fee_bid={self.fee_bid})'


class OrderSetForSide(Data):
    market: 'Market'
    is_sell_side: bool
    limit_orders: np.array
    liquidity_fractions: np.array

    @property
    def mid(self):
        return self.market.mark_price

    @property
    def tick(self):
        return self.market.tick_size

    @property
    def num_ticks(self):
        return self.market.num_ticks

    def __post_init__(self):
        if (self.tick <= 0 or self.num_ticks <= 0):
            raise ValueError("Invalid book params.")

        if (self.mid - self.tick * self.num_ticks <= 0):
            raise ValueError(
                "Cannot handle negative prices, choose higher mid or smaller tick or fewer ticks.")

        if type(self.limit_orders) != np.ndarray:
            self.limit_orders = np.array(self.limit_orders)

        if type(self.liquidity_fractions) != np.ndarray:
            self.liquidity_fractions = np.array(self.liquidity_fractions)

        if np.shape(self.limit_orders) != (self.num_ticks, ):
            raise ValueError(
                "limit_orders array must have length equal to number of ticks on the book side.")

        if np.shape(self.liquidity_fractions) != (self.num_ticks, ):
            raise ValueError(
                "liquidity_fractions array must have length equal to number of ticks on the book side.")

        self.priceList = np.linspace(
            self.mid + self.tick, self.mid + self.tick * self.num_ticks, self.num_ticks)

    def CalculateLiquidity(self, volArray: np.array):
        if np.shape(volArray) != (self.num_ticks, ):
            raise ValueError(
                "Volume array must have length equal to number of ticks on the book side.")
        liquidity = 0.0
        for orderIdx in range(0, self.num_ticks):
            priceLevel = self.priceList[orderIdx]
            probOfTrading = self.market.risk_model.ProbOfTrading(
                self.mid, priceLevel)
            volumeAtLevel = volArray[orderIdx]
            liquidity = liquidity + volumeAtLevel * priceLevel * probOfTrading
        return liquidity

    def CalculateLimitOrderLiquidity(self):
        return self.CalculateLiquidity(self.limit_orders)

    def CalculateMargin(self, orderVolArray: np.array):
        if np.shape(orderVolArray) != (self.num_ticks, ):
            raise ValueError(
                "Volume array must have length equal to number of ticks on the book side.")
        margin = 0.0

        riskFactor = 0.0
        if self.is_sell_side:
            riskFactor = self.market.risk_model.RiskFactorShort()
        else:
            riskFactor = self.market.risk_model.RiskFactorLong()

        margin = riskFactor * self.mid * orderVolArray
        return np.sum(margin)
