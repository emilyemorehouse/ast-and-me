"""      turtle-example-suite:

        tdemo_fractalCurves.py

This program draws two fractal-curve-designs:
(1) A hilbert curve (in a box)
(2) A combination of Koch-curves.

The CurvesTurtle class and the fractal-curve-
methods are taken from the PythonCard example
scripts for turtle-graphics.
"""
from turtle import *
from time import sleep, clock


class CurvesTurtle(Pen):

    def hilbert(self, size, level, parity):
        if level == 0:
            return
        self.left(parity * 90)
        self.hilbert(size, level - 1, -parity)
        self.forward(size)
        self.right(parity * 90)
        self.hilbert(size, level - 1, parity)
        self.forward(size)
        self.hilbert(size, level - 1, parity)
        self.right(parity * 90)
        self.forward(size)
        self.hilbert(size, level - 1, -parity)
        self.left(parity * 90)

    def fractalgon(self, n, rad, lev, dir):
        import math
        edge = 2 * rad * math.sin(math.pi / n)
        self.pu()
        self.fd(rad)
        self.pd()
        self.rt(180 - 90 * (n - 2) / n)
        for i in range(n):
            self.fractal(edge, lev, dir)
            self.rt(360 / n)
        self.lt(180 - 90 * (n - 2) / n)
        self.pu()
        self.bk(rad)
        self.pd()

    def fractal(self, dist, depth, dir):
        if depth < 1:
            self.fd(dist)
            return
        self.fractal(dist / 3, depth - 1, dir)
        self.lt(60 * dir)
        self.fractal(dist / 3, depth - 1, dir)
        self.rt(120 * dir)
        self.fractal(dist / 3, depth - 1, dir)
        self.lt(60 * dir)
        self.fractal(dist / 3, depth - 1, dir)


def main():
    ft = CurvesTurtle()
    ft.reset()
    ft.speed(0)
    ft.ht()
    ft.getscreen().tracer(1, 0)
    ft.pu()
    size = 6
    ft.setpos(-33 * size, -32 * size)
    ft.pd()
    ta = clock()
    ft.fillcolor('red')
    ft.begin_fill()
    ft.fd(size)
    ft.hilbert(size, 6, 1)
    ft.fd(size)
    for i in range(3):
        ft.lt(90)
        ft.fd(size * (64 + i % 2))
    ft.pu()
    for i in range(2):
        ft.fd(size)
        ft.rt(90)
    ft.pd()
    for i in range(4):
        ft.fd(size * (66 + i % 2))
        ft.rt(90)
    ft.end_fill()
    tb = clock()
    res = 'Hilbert: %.2fsec. ' % (tb - ta)
    sleep(3)
    ft.reset()
    ft.speed(0)
    ft.ht()
    ft.getscreen().tracer(1, 0)
    ta = clock()
    ft.color('black', 'blue')
    ft.begin_fill()
    ft.fractalgon(3, 250, 4, 1)
    ft.end_fill()
    ft.begin_fill()
    ft.color('red')
    ft.fractalgon(3, 200, 4, -1)
    ft.end_fill()
    tb = clock()
    res += 'Koch: %.2fsec.' % (tb - ta)
    return res


if __name__ == '__main__':
    msg = main()
    print(msg)
    mainloop()
