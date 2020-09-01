import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import ticker as mtick, pyplot as plt


def plots(m,
          mark_price=False,
          market_size=False,
          stake_vs_target=False,
          fee_rate=False,
          fees_collected=False,
          equity_share=False,
          stake_share=False,
          annualised_return=False,
          traded_volume=False,
          open_interest=False,
          margin=False):

    show_all = not (
        mark_price or
        market_size or
        stake_vs_target or
        fee_rate or
        fees_collected or
        equity_share or
        stake_share or
        annualised_return or
        traded_volume or
        open_interest or
        margin)

    df = m.to_data_frame(
        lp_fields=['stake', 'equity_share', 'stake_share', 'fee_revenue', 'annualised_return', 'margin'])

    if show_all or mark_price:
        ax = df[['mark_price']].plot(title="Mark price")
        ax.get_yaxis().set_major_formatter(
            mtick.FuncFormatter(lambda x, p: format(int(x), ',')))
        ax.set(xlabel="day")

    if show_all or market_size:
        ax = df[['traded_volume', 'open_interest']].plot(
            subplots=True, title="Volume & open interest")
        ax[0].get_yaxis().set_major_formatter(
            mtick.FuncFormatter(lambda x, p: f'%1.0fM' % (x * 1e-6)))
        ax[1].get_yaxis().set_major_formatter(
            mtick.FuncFormatter(lambda x, p: f'%1.0fk' % (x * 1e-3)))
        ax[1].set(xlabel="day")

    if traded_volume:  # already covered in market_size so not including in show_all
        ax = df[['traded_volume']].plot(title="Volume")
        ax.get_yaxis().set_major_formatter(
            mtick.FuncFormatter(lambda x, p: f'%1.0fM' % (x * 1e-6)))
        ax.set(xlabel="day")

    if open_interest:  # already covered in market_size so not including in show_all
        ax = df[['open_interest']].plot(title="Open interest")
        ax.get_yaxis().set_major_formatter(
            mtick.FuncFormatter(lambda x, p: f'%1.0fk' % (x * 1e-3)))
        ax.set(xlabel="day")

    if show_all or stake_vs_target:
        ax = df[['target_stake', 'total_stake']].plot(title="Stake")
        ax.get_yaxis().set_major_formatter(
            mtick.FuncFormatter(lambda x, p: f'%1.0fk' % (x * 1e-3)))
        ax.set(xlabel="day")

    if show_all or fee_rate:
        ax = df[['fee_rate']].plot(title="Fee rate")
        ax.get_yaxis().set_major_formatter(
            mtick.FuncFormatter(lambda x, p: '{:.3%}'.format(x)))
        ax.set(xlabel="day")

    if show_all or fees_collected:
        fees = df[['fees_collected']]
        ax = fees.plot(title="Fees collected / day")
        ax.get_yaxis().set_major_formatter(
            mtick.FuncFormatter(lambda x, p: format(int(x), ',')))
        ax.set(xlabel="day")

    if show_all or equity_share:
        df[[col for col in df.columns if 'equity_share' in col]].plot()

    if show_all or stake_share:
        df[[col for col in df.columns if 'stake_share' in col]].plot()

    if show_all or annualised_return:
        df[[col for col in df.columns if 'annualised_return' in col]].plot(
            title="Annualised Rate of Return")

    if show_all or margin:
        df[[col for col in df.columns if 'margin' in col]].plot()


def visualise_orders(lp: 'LiquidityProvider', plot_pegged_orders=False, plot_liquidity_fractions=False, plot_prob_of_trading=False, title='', print_liquidity=False, print_margins=False):
    mid = lp.market.mark_price
    tick_size = lp.market.tick_size
    bid_levels = []
    offer_levels = []
    for i in range(1, lp.market.num_ticks+1):
        bid_levels = np.append(bid_levels, mid-i*tick_size)
        offer_levels = np.append(offer_levels, mid+i*tick_size)

    bid_indices = [i for i in range(lp.market.num_ticks)]
    offer_indices = [i for i in range(
        lp.market.num_ticks+1, 2*lp.market.num_ticks+1)]

    # bids
    plt.bar(bid_indices, np.flip(
        lp.buy_side_shape.limit_orders), color='green')

    # offers
    plt.bar(offer_indices, lp.sell_side_shape.limit_orders, color='red')

    plt.xticks([i for i in range(2*lp.market.num_ticks+1)],
               np.concatenate((np.flip(bid_levels), "mid", offer_levels), axis=None))
    plt.xticks(rotation=90)

    plt.xlabel("Price")
    plt.ylabel("Volume")
    legend = ['Bids', 'Offers']

    if plot_pegged_orders:
        shape_implied_bids = lp.get_volume_meeting_obligation_from_shape(
            lp.buy_side_shape)
        shape_implied_offers = lp.get_volume_meeting_obligation_from_shape(
            lp.sell_side_shape)

        # bids
        plt.bar(bid_indices, np.flip(shape_implied_bids), bottom=np.flip(
            lp.buy_side_shape.limit_orders), color='lightgreen')

        # offers
        plt.bar(offer_indices, shape_implied_offers,
                bottom=lp.sell_side_shape.limit_orders, color='coral')

        legend = np.append(legend, ["Pegged bids", "Pegged offers"])

    ax1 = plt.gca()
    if plot_liquidity_fractions or plot_prob_of_trading:

        ax2 = ax1.twinx()
        ax2.set_ylabel('probability')
        legend2 = np.array([])
        if plot_liquidity_fractions:
            bid_fractions = np.flip(lp._normalise_fractions(
                lp.buy_side_shape.liquidity_fractions))
            offer_fractions = lp._normalise_fractions(
                lp.sell_side_shape.liquidity_fractions)

            ax2.scatter(np.concatenate((bid_indices, offer_indices)), np.concatenate(
                (bid_fractions, offer_fractions)), marker='_', color='b')

            legend2 = np.append(legend2, ['liquidity fraction'])

        if plot_prob_of_trading:
            price_levels = np.concatenate(
                (np.flip(bid_levels), mid, offer_levels), axis=None)
            probabilities = [lp.market.risk_model.ProbOfTrading(
                mid, level) for level in price_levels]
            ax2.plot([i for i in range(2*lp.market.num_ticks+1)],
                     probabilities, 'm--')
            legend2 = np.append(['prob. of trading'], legend2)

        ax2.legend(legend2, loc="upper right")
        ax2.set_ylim((0, 1.1))
        ax2.tick_params(axis='y', colors='blue')

    ax1.legend(legend, loc="upper left")
    plt.title(title)
    plt.show()

    if print_liquidity:
        bid = lp.buy_side_shape.limit_orders
        offer = lp.sell_side_shape.limit_orders
        if plot_pegged_orders:
            bid = bid + lp.get_volume_meeting_obligation_from_shape(
                lp.buy_side_shape)
            offer = offer + lp.get_volume_meeting_obligation_from_shape(
                lp.sell_side_shape)
        bid_liquidity = lp.buy_side_shape.CalculateLiquidity(bid)
        offer_liquidity = lp.sell_side_shape.CalculateLiquidity(offer)
        print(
            'Liquidity:\n\tobligaton:  {0:,.0f}\n\tbid:        {1:,.0f}\n\toffer:      {2:,.0f}\n\tsupplied:   {3:,.0f} = min(liquidity_bid,liquidity_offer)\n'.
            format(lp.obligation, bid_liquidity, offer_liquidity, min(bid_liquidity, offer_liquidity)))

    if print_margins:
        bid = lp.buy_side_shape.limit_orders
        offer = lp.sell_side_shape.limit_orders
        if plot_pegged_orders:
            bid = bid + lp.get_volume_meeting_obligation_from_shape(
                lp.buy_side_shape)
            offer = offer + lp.get_volume_meeting_obligation_from_shape(
                lp.sell_side_shape)
        bid_margin = lp.buy_side_shape.CalculateMargin(bid)
        offer_margin = lp.sell_side_shape.CalculateMargin(offer)
        print(
            'Margin:\n\tbid:         {0:,.0f}\n\toffer:       {1:,.0f}\n\tcharged:     {2:,.0f} = max(margin_bid,margin_offer)'.format(
                bid_margin, offer_margin, max(bid_margin, offer_margin)))
