
import session

class LparManager(object):
    def __init__(self, cpc, session):
        self.session = session
        self.cpc = cpc

    def list(self):
        cpc_object_uri = getattr(self.cpc, "object-uri")
        lpars = self.session.get(cpc_object_uri + '/logical-partitions')
        lpar_list = []
        if lpars:
            lpar_items = lpars['logical-partitions']
            for lpar in lpar_items:
                lpar_list.append(Lpar(self, lpar))
        return lpar_list

    def find(self, name):
        pass

class Lpar(object):
    def __init__(self, manager, info):
       self.manager = manager
       self._info = info
       self._add_details(info)

    def _add_details(self, info):
       for (k, v) in info.items():
           setattr(self, k, v)

    def activate(self):
        pass

    def deactivate(self):
        pass

    def load(self, oad_address):
        pass

