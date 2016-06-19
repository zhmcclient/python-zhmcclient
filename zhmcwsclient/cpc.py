
import session
from zhmcwsclient.lpar import LparManager

class CpcManager(object):
    def __init__(self, session):
        self.session = session

    def list(self):
        cpcs = self.session.get('/api/cpcs')
        cpc_list = []
        if cpcs:
            cpc_items = cpcs['cpcs']
            for cpc in cpc_items:
                cpc_list.append(Cpc(self, cpc))
        return cpc_list

class Cpc(object):
    def __init__(self, manager, info):
        self.manager = manager
        self._info = info
        self._add_details(info)
        self.lpars = LparManager(self, manager.session)

    def _add_details(self, info):
       for (k, v) in info.items():
           setattr(self, k, v)

    def lpars(self):
        return self.lpars

