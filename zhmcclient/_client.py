#!/usr/bin/env python

from __future__ import absolute_import

from ._session import Session
from ._cpc import CpcManager

__all__ = ['Client']

class Client(object):

    def __init__(self, hmc_ip, userid, password):
        self.hmc_ip = hmc_ip
        self.userid = userid
        self.password = password
        self.session = Session(self.hmc_ip, self.userid, self.password)
        self.cpcs = CpcManager(self.session)

    def cpcs(self):
        return self.cpcs

