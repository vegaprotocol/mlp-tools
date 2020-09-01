import json
import matplotlib.pyplot as plt

from .liquidity_provider import *


def get_order_profiles(mkt):

    # Set up some market maker profiles

    # Empty
    lo_empty=[0,0,0,0,0,0,0,0,0,0]

    # Smoothed
    lo_smoothed=[1,1,1,1,1,1,1,1,1,1]
    lf_smoothed=[1,1,1,1,1,1,1,1,1,1]

    # Highly active
    lo_active=[1,0,0,0,0,0,0,0,0,0]
    lf_active=[1,0,0,0,0,0,0,0,0,0]

    # Highly passive
    lo_passive=[0,0,0,0,0,0,0,0,0,1]
    lf_passive=[0,0,0,0,0,0,0,0,0,1]


    sellSideA = OrderSetForSide(
        market=mkt, 
        is_sell_side=True, 
        limit_orders=lo_empty,
        liquidity_fractions=lf_active) 
    buySideA = OrderSetForSide(
        market=mkt, 
        is_sell_side=False, 
        limit_orders=lo_empty,
        liquidity_fractions=lf_active) 

    sellSideB = OrderSetForSide(
        market=mkt, 
        is_sell_side=True, 
        limit_orders=lo_empty,
        liquidity_fractions=lf_smoothed) 
    buySideB = OrderSetForSide(
        market=mkt, 
        is_sell_side=False, 
        limit_orders=lo_empty,
        liquidity_fractions=lf_smoothed) 

    sellSideC = OrderSetForSide(
        market=mkt, 
        is_sell_side=True, 
        limit_orders=lo_empty,
        liquidity_fractions=lf_active)
    buySideC = OrderSetForSide(
        market=mkt, 
        is_sell_side=False, 
        limit_orders=lo_empty,
        liquidity_fractions=lf_active)  

    sellSideD = OrderSetForSide(
        market=mkt, 
        is_sell_side=True, 
        limit_orders=lo_empty,
        liquidity_fractions=lf_active) 
    buySideD = OrderSetForSide(
        market=mkt, 
        is_sell_side=False, 
        limit_orders=lo_empty,
        liquidity_fractions=lf_active) 

    return (
        lo_empty, lo_smoothed, lf_smoothed, lo_active, lf_active, lo_passive, lf_passive,
        buySideA, sellSideA, buySideB, sellSideB, buySideC, sellSideC, buySideD, sellSideD
    )