from test.support import TestFailed
PI = 3.141592653589793
TWOPI = 6.283185307179586
PI_str = '3.14159265358979324'
TWOPI_str = '6.28318530717958648'


def check_ok(x, x_str):
    assert x > 0.0
    x2 = eval(x_str)
    assert x2 > 0.0
    diff = abs(x - x2)
    if x2 + diff / 8.0 != x2:
        raise TestFailed('Manifest const %s lost too much precision ' % x_str)


check_ok(PI, PI_str)
check_ok(TWOPI, TWOPI_str)
