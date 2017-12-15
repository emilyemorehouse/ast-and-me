class TwoNames:
    """f() and g() are two names for the same method"""

    def f(self):
        """
        >>> print(TwoNames().f())
        f
        """
        return 'f'
    g = f
