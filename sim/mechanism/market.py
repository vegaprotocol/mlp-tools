import pandas as pd

from prelude import *
from .risk import *
from .liquidity_provider import *
from .liquidity import *


class Market(Data):
    '''

    '''
    name: str

    # Liquidity mechanic network parameters
    liquidity: Liquidity = default_factory(Liquidity)
    risk_model: RiskModel = default_factory(RiskModel)

    # Market data
    num_ticks: int = 10  #TODO: not have this fixed num_ticks thing
    tick_size: float = 1
    mark_price: float = 0
    traded_volume: float = 0
    open_interest: float = 0

    # Liquidity provider store, lookup by name
    _lps: Dict[str, 'LiquidityProvider'] = default_factory(dict)

    # implementation details
    _n: int = 0  # used to record a record's place in history
    _history: List['Market'] = field(default_factory=list, repr=False)

    def __post_init__(self):
        if not self._history:
            # initialise history when creating a new market
            self._history = [self]

    @property
    def valuation(self):
        '''
        This is the market's "valuation" for stake commitment, min of traded volume over a window and total stake
        '''
        period = self.liquidity.valuation_period
        # factor scales the valuation when the window is short to avoid artificial "growth" at the start of a market
        factor = float(period) / float(self._n + 1 - max(0, self._n - period + 1))
        return max(factor * sum(self._window(period, 'traded_volume')), self.total_stake)

    @property
    def total_stake(self):
        return sum(lp.stake for lp in self.lps)

    @property
    def total_margin(self):
        return sum(lp.margin for lp in self.lps)

    @property
    def total_equity(self):
        return sum(lp.equity for lp in self.lps)

    @property
    def target_stake(self):
        max_oi = max(self._window(
            self.liquidity.stake_target_period, 'open_interest'))
        c2, v = self.liquidity.c2, self.liquidity.v
        rf = self.risk_model.RiskFactorShort()
        return max_oi * c2 * v * rf

    @property
    def annualised_return(self):
        '''
        Calculates the return across all liquidity providers on current total stake if fee rate and volume remained
        constant for a year.
        '''
        return (365 * self.fees_collected) / self.total_stake if self.total_stake > 0 else 0

    @property
    def annualised_return_on_capital(self):
        '''
        Calculates the return across all liquidity providers on current total stake if fee rate and volume remained
        constant for a year.
        '''
    
        cost_base = self.total_stake + self.total_margin
        return (365 * self.fees_collected) / cost_base if cost_base > 0 else 0


    @property
    def fee_rate(self):
        '''
        Fee rate is calculated by sorting all committed liquditiy providers by their fee bid (lowest to highest), then
        working down the list until the total cumulative stake >= the stake target. The fee bid from the last liquidity
        provider needed to take the cumulative stake to the target is the liquidity fee rate for the market.
        '''
        bids = sorted(list(self.lps), key=attr('fee_bid'))
        stake_covered = 0
        for bid in bids:
            stake_covered += bid.stake
            if stake_covered >= self.target_stake:
                return bid.fee_bid
        return bids[-1].fee_bid if len(bids) > 0 else 0

    @property
    def fees_collected(self):
        return self.traded_volume * self.fee_rate

    def _window(self, period, attr=None):
        '''
        Return a list of the value of field over up to period previous records from the history
        '''
        records = self._history[max(0, self._n - period + 1):self._n + 1]
        return [r if attr == None else getattr(r, attr) for r in records]

    @property
    def lps(self):
        return self._lps.values()

    def lp(self, name, attr=None, default=None):
        if name in self._lps:
            return self._lps[name] if attr == None else getattr(self._lps[name], attr)
        else:
            return default

    def next(self, traded_volume=None, open_interest=None, liquidity=None, mark_price=None):
        '''
        Move time forward a step. Returns a copy of the market record and adds it to the history.
        '''
        next_m = replace(
            self._history[-1],
            # copy here otherwise all history records share one LP list
            _lps=self._history[-1]._lps.copy(),
            traded_volume=traded_volume or self.traded_volume,
            open_interest=open_interest or self.open_interest,
            liquidity=liquidity or replace(self.liquidity),
            mark_price=mark_price or self.mark_price,
            _n=len(self._history))

        for lp in next_m.lps:
            # oint at correct history entry
            next_m._lps[lp.name] = replace(lp, market=next_m)
            if lp.name in self._lps: next_m._lps[lp.name].entry_valuation = self._lps[lp.name].entry_valuation

        self._history.append(next_m)
        return next_m

    def to_csv(self,
               market_fields=[
                   '_n',
                   'mark_price',
                   'traded_volume',
                   'valuation',
                   'target_stake',
                   'total_stake',
                   'total_margin',
                   'fee_rate',
                   'fees_collected',
                   'annualised_return',
                   'annualised_return_on_capital',
                   'total_equity'],

               lp_fields=[
                   'stake',
                   'equity',
                   'equity_share',
                   'fee_revenue',
                   'annualised_return',
                   'margin',
                   'entry_valuation',
                   'obligation'],
               output=sys.stdout):
        '''
        Dump the market history to CSV. Creates columns for each liquidity provider's data.
        '''
        lps = list(dict.fromkeys(
            [lp.name for m in self._history for lp in m.lps]))  # all LPs in history
        # output CSV header
        output.write(
            ','.join([*market_fields, *[f'{lp}_{f}' for lp in lps for f in lp_fields]])+'\n')
        for m in self._history:
            market_data = [getattr(m, f) for f in market_fields]
            lp_data = [m.lp(name=lp, attr=f)
                       or '' for lp in lps for f in lp_fields]
            output.write(','.join([str(d) for d in [*market_data, *lp_data]])+'\n')

    def to_data_frame(self,
                      market_fields=[
                          '_n',
                          'mark_price',
                          'traded_volume',
                          'open_interest',
                          'valuation',
                          'target_stake',
                          'total_stake',
                          'total_margin',
                          'fee_rate',
                          'fees_collected',
                          'annualised_return',
                          'annualised_return_on_capital'],
                      lp_fields=[
                          'stake',
                          'equity_share',
                          'fee_revenue',
                          'annualised_return',
                          'margin'],
                      output=print):
        '''
        Dump the market history to CSV. Creates columns for each liquidity provider's data.
        '''
        lps = list(dict.fromkeys(
            [lp.name for m in self._history for lp in m.lps]))  # all LPs in history
        df = pd.DataFrame(
            columns=[*market_fields, *[f'{lp}_{f}' for lp in lps for f in lp_fields]])

        i = 0
        for m in self._history:
            market_data = [getattr(m, f) for f in market_fields]
            lp_data = [m.lp(name=lp, attr=f)
                       or '' for lp in lps for f in lp_fields]
            row = [*market_data, *lp_data]
            df.loc[i] = [tryFloat(d) for d in row]
            i = i + 1
        return df

    def __getitem__(self, key):
        return self._history[key]

    def __invert__(self):
        return self._history[-1]


def tryFloat(s):
    try:
        return float(s)
    except:
        return 0
