
import session
import exceptions
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

	pass

    def find(self, **kwargs):
        matches = self.findall(**kwargs)
        num_matches = len(matches)
        if num_matches == 0:
            raise exceptions.NotFound
        elif num_matches > 1:
            raise exceptions.NoUniqueMatch
        else:
            return matches[0]

    def findall(self, **kwargs):
        searches = kwargs.items()
        print searches
	found = list()
        listing = self.list()
        for obj in listing:
            try:
                if all(getattr(obj, attr) == value
                       for (attr, value) in searches):
                    found.append(obj)
            except AttributeError:
                continue

        return found

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

