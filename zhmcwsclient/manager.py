
import exceptions

class BaseManager(object):

    def list(self):
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

