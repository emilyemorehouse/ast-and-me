"""A module docstring."""
import sys, inspect


def spam(a, b, c, d=3, e=4, f=5, *g, **h):
    eggs(b + d, c + f)


def eggs(x, y):
    """A docstring."""
    global fr, st
    fr = inspect.currentframe()
    st = inspect.stack()
    p = x
    q = y / 0


class StupidGit:
    """A longer,

    indented

    docstring."""

    def abuse(self, a, b, c):
        """Another

	docstring

        containing

	tabs
	
        """
        self.argue(a, b, c)

    def argue(self, a, b, c):
        try:
            spam(a, b, c)
        except:
            self.ex = sys.exc_info()
            self.tr = inspect.trace()

    @property
    def contradiction(self):
        """The automatic gainsaying."""
        pass


class MalodorousPervert(StupidGit):

    def abuse(self, a, b, c):
        pass

    @property
    def contradiction(self):
        pass


Tit = MalodorousPervert


class ParrotDroppings:
    pass


class FesteringGob(MalodorousPervert, ParrotDroppings):

    def abuse(self, a, b, c):
        pass

    @property
    def contradiction(self):
        pass


async def lobbest(grenade):
    pass
