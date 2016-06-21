
import session
from zhmcwsclient.manager import BaseManager

class LparManager(BaseManager):
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


class Lpar(object):
    def __init__(self, manager, info):
       self.manager = manager
       self._info = info
       self._add_details(info)

    def _add_details(self, info):
       for (k, v) in info.items():
            setattr(self, k, v)

    def activate(self):
        if getattr(self, "status") == "not-activated":
            lpar_object_uri = getattr(self, "object-uri")
            body = {}
            status, meta = self.manager.session.post(lpar_object_uri + '/operations/activate', body)
            self._update_status()
            return status
        else:
            return False

    def deactivate(self):
        if getattr(self, "status") in ["operating", "not-operating", "exceptions"]:
            lpar_object_uri = getattr(self, "object-uri")
            body = { 'force' : True }
            status, meta = self.manager.session.post(lpar_object_uri + '/operations/deactivate', body)
            self._update_status()
            return status
        else:
            return False

    def load(self, load_address):
        if getattr(self, "status") in ["not-operating"]:
            lpar_object_uri = getattr(self, "object-uri")
            body = { 'load-address' : load_address }
            status, meta = self.manager.session.post(lpar_object_uri + '/operations/load', body)
            self._update_status()
            return status
        else:
            return False

    def _update_status(self):
        lpar_object_uri = getattr(self, "object-uri")
        lpar = self.manager.session.get(lpar_object_uri)
        setattr(self, 'status', lpar.get("status"))
        return

