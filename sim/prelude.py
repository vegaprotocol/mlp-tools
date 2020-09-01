import os
from typing import List, Optional, Union, Dict
from functools import reduce, namedtuple
from dataclasses import dataclass, field, replace
from copy import deepcopy

ROOT = (os.path.dirname(__file__) + '/../{}').format

class Data: 
	def __init_subclass__(cls, **kwargs): return dataclass(cls)

def default_factory(x, init=True, repr=True):
	return field(default_factory=x, init=init, repr=repr)

def attr(name):
	return lambda o: getattr(o, name)