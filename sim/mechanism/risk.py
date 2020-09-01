import sys; sys.path.append('../')
from prelude import *

import numpy as np
from scipy.stats import norm


class RiskModel(Data):
    '''
    Risk Model
    '''

    mu: float = 0.0
    sigma: float = 2.0
    tau: float = 1.0/60/24/365.25
    lambd: float = 0.001

    def __post_init__(self):
        if (self.tau < 0 or self.sigma <= 0 or self.lambd < 0.0 or self.lambd > 1.0):
            raise ValueError(
                "Time and volatility parameter should be strictly +ve and lambd must be between 0 and 1. ")

    def RiskFactorLong(self):
        sigmaBar = np.sqrt(self.tau) * self.sigma 
        muBar=(self.mu - 0.5*self.sigma*self.sigma) * self.tau
        quantileForLambda = norm.ppf(self.lambd)
        #print("quantileForLambda = " + str(quantileForLambda))
        logNormalEs = -(1/self.lambd)*np.exp(muBar*sigmaBar*sigmaBar*0.5) * norm.cdf(quantileForLambda-sigmaBar)
        #print("logNormalEs = " + str(logNormalEs))
        return logNormalEs + 1.0

    def RiskFactorShort(self):
        sigmaBar = np.sqrt(self.tau) * self.sigma 
        muBar=(self.mu - 0.5*self.sigma*self.sigma) * self.tau
        quantileForOneMinusLambda = norm.ppf(1.0 - self.lambd)
        #print("quantileForOneMinusLambda = " + str(quantileForOneMinusLambda))
        negativeLogNormalEs = (1/self.lambd)*np.exp(muBar*sigmaBar*sigmaBar*0.5) * (1.0 - norm.cdf(quantileForOneMinusLambda-sigmaBar))
        #print("negativeLogNormalEs = " + str(negativeLogNormalEs))
        return negativeLogNormalEs - 1.0

    def ProbOfTrading(self, mid: float, level: float):
        transLevel = (np.log(level/mid) - (self.mu - 0.5*self.sigma*self.sigma)*self.tau) / (self.sigma*np.sqrt(self.tau))
        #print("transLevel = " + str(transLevel))
        if (mid < level):
            return 1.0 - norm.cdf(transLevel)
        else:
            return norm.cdf(transLevel)