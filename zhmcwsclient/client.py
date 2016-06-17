#!/usr/bin/python

from zhmcwsclient.session import Session
from zhmcwsclient.cpc import CpcManager

class Client(object):
    def __init__(self, hmc_ip, userid, password):
        self.hmc_ip = hmc_ip
        self.userid = userid
        self.password = password

        self.session = Session(self.hmc_ip, self.userid, self.password)
	self.cpcs = CpcManager(self.session)

    def cpcs(self):
        return self.cpcs

