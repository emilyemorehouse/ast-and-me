class Delegator:

    def __init__(self, delegate=None):
        self.delegate = delegate
        self.__cache = set()

    def __getattr__(self, name):
        attr = getattr(self.delegate, name)
        setattr(self, name, attr)
        self.__cache.add(name)
        return attr

    def resetcache(self):
        """Removes added attributes while leaving original attributes."""
        for key in self.__cache:
            try:
                delattr(self, key)
            except AttributeError:
                pass
        self.__cache.clear()

    def setdelegate(self, delegate):
        """Reset attributes and change delegate."""
        self.resetcache()
        self.delegate = delegate


if __name__ == '__main__':
    from unittest import main
    main('idlelib.idle_test.test_delegator', verbosity=2)
