"""Test date/time type.

See http://www.zope.org/Members/fdrake/DateTimeWiki/TestCases
"""
from test.support import is_resource_enabled
import itertools
import bisect
import copy
import decimal
import sys
import os
import pickle
import random
import struct
import unittest
from array import array
from operator import lt, le, gt, ge, eq, ne, truediv, floordiv, mod
from test import support
import datetime as datetime_module
from datetime import MINYEAR, MAXYEAR
from datetime import timedelta
from datetime import tzinfo
from datetime import time
from datetime import timezone
from datetime import date, datetime
import time as _time
import _strptime
pickle_choices = [(pickle, pickle, proto) for proto in range(pickle.
    HIGHEST_PROTOCOL + 1)]
assert len(pickle_choices) == pickle.HIGHEST_PROTOCOL + 1
OTHERSTUFF = 10, 34.5, 'abc', {}, [], ()
INF = float('inf')
NAN = float('nan')


class TestModule(unittest.TestCase):

    def test_constants(self):
        datetime = datetime_module
        self.assertEqual(datetime.MINYEAR, 1)
        self.assertEqual(datetime.MAXYEAR, 9999)

    def test_name_cleanup(self):
        if '_Fast' not in str(self):
            return
        datetime = datetime_module
        names = set(name for name in dir(datetime) if not name.startswith(
            '__') and not name.endswith('__'))
        allowed = set(['MAXYEAR', 'MINYEAR', 'date', 'datetime',
            'datetime_CAPI', 'time', 'timedelta', 'timezone', 'tzinfo'])
        self.assertEqual(names - allowed, set([]))

    def test_divide_and_round(self):
        if '_Fast' in str(self):
            return
        dar = datetime_module._divide_and_round
        self.assertEqual(dar(-10, -3), 3)
        self.assertEqual(dar(5, -2), -2)
        self.assertEqual(dar(7, 3), 2)
        self.assertEqual(dar(-7, 3), -2)
        self.assertEqual(dar(7, -3), -2)
        self.assertEqual(dar(-7, -3), 2)
        self.assertEqual(dar(10, 4), 2)
        self.assertEqual(dar(-10, 4), -2)
        self.assertEqual(dar(10, -4), -2)
        self.assertEqual(dar(-10, -4), 2)
        self.assertEqual(dar(6, 4), 2)
        self.assertEqual(dar(-6, 4), -2)
        self.assertEqual(dar(6, -4), -2)
        self.assertEqual(dar(-6, -4), 2)


class FixedOffset(tzinfo):

    def __init__(self, offset, name, dstoffset=42):
        if isinstance(offset, int):
            offset = timedelta(minutes=offset)
        if isinstance(dstoffset, int):
            dstoffset = timedelta(minutes=dstoffset)
        self.__offset = offset
        self.__name = name
        self.__dstoffset = dstoffset

    def __repr__(self):
        return self.__name.lower()

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return self.__dstoffset


class PicklableFixedOffset(FixedOffset):

    def __init__(self, offset=None, name=None, dstoffset=None):
        FixedOffset.__init__(self, offset, name, dstoffset)

    def __getstate__(self):
        return self.__dict__


class _TZInfo(tzinfo):

    def utcoffset(self, datetime_module):
        return random.random()


class TestTZInfo(unittest.TestCase):

    def test_refcnt_crash_bug_22044(self):
        tz1 = _TZInfo()
        dt1 = datetime(2014, 7, 21, 11, 32, 3, 0, tz1)
        with self.assertRaises(TypeError):
            dt1.utcoffset()

    def test_non_abstractness(self):
        useless = tzinfo()
        dt = datetime.max
        self.assertRaises(NotImplementedError, useless.tzname, dt)
        self.assertRaises(NotImplementedError, useless.utcoffset, dt)
        self.assertRaises(NotImplementedError, useless.dst, dt)

    def test_subclass_must_override(self):


        class NotEnough(tzinfo):

            def __init__(self, offset, name):
                self.__offset = offset
                self.__name = name
        self.assertTrue(issubclass(NotEnough, tzinfo))
        ne = NotEnough(3, 'NotByALongShot')
        self.assertIsInstance(ne, tzinfo)
        dt = datetime.now()
        self.assertRaises(NotImplementedError, ne.tzname, dt)
        self.assertRaises(NotImplementedError, ne.utcoffset, dt)
        self.assertRaises(NotImplementedError, ne.dst, dt)

    def test_normal(self):
        fo = FixedOffset(3, 'Three')
        self.assertIsInstance(fo, tzinfo)
        for dt in (datetime.now(), None):
            self.assertEqual(fo.utcoffset(dt), timedelta(minutes=3))
            self.assertEqual(fo.tzname(dt), 'Three')
            self.assertEqual(fo.dst(dt), timedelta(minutes=42))

    def test_pickling_base(self):
        orig = tzinfo.__new__(tzinfo)
        self.assertIs(type(orig), tzinfo)
        for pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertIs(type(derived), tzinfo)

    def test_pickling_subclass(self):
        offset = timedelta(minutes=-300)
        for otype, args in [(PicklableFixedOffset, (offset, 'cookie')), (
            timezone, (offset,)), (timezone, (offset, 'EST'))]:
            orig = otype(*args)
            oname = orig.tzname(None)
            self.assertIsInstance(orig, tzinfo)
            self.assertIs(type(orig), otype)
            self.assertEqual(orig.utcoffset(None), offset)
            self.assertEqual(orig.tzname(None), oname)
            for pickler, unpickler, proto in pickle_choices:
                green = pickler.dumps(orig, proto)
                derived = unpickler.loads(green)
                self.assertIsInstance(derived, tzinfo)
                self.assertIs(type(derived), otype)
                self.assertEqual(derived.utcoffset(None), offset)
                self.assertEqual(derived.tzname(None), oname)

    def test_issue23600(self):
        DSTDIFF = DSTOFFSET = timedelta(hours=1)


        class UKSummerTime(tzinfo):
            """Simple time zone which pretends to always be in summer time, since
                that's what shows the failure.
            """

            def utcoffset(self, dt):
                return DSTOFFSET

            def dst(self, dt):
                return DSTDIFF

            def tzname(self, dt):
                return 'UKSummerTime'
        tz = UKSummerTime()
        u = datetime(2014, 4, 26, 12, 1, tzinfo=tz)
        t = tz.fromutc(u)
        self.assertEqual(t - t.utcoffset(), u)


class TestTimeZone(unittest.TestCase):

    def setUp(self):
        self.ACDT = timezone(timedelta(hours=9.5), 'ACDT')
        self.EST = timezone(-timedelta(hours=5), 'EST')
        self.DT = datetime(2010, 1, 1)

    def test_str(self):
        for tz in [self.ACDT, self.EST, timezone.utc, timezone.min,
            timezone.max]:
            self.assertEqual(str(tz), tz.tzname(None))

    def test_repr(self):
        datetime = datetime_module
        for tz in [self.ACDT, self.EST, timezone.utc, timezone.min,
            timezone.max]:
            tzrep = repr(tz)
            self.assertEqual(tz, eval(tzrep))

    def test_class_members(self):
        limit = timedelta(hours=23, minutes=59)
        self.assertEqual(timezone.utc.utcoffset(None), ZERO)
        self.assertEqual(timezone.min.utcoffset(None), -limit)
        self.assertEqual(timezone.max.utcoffset(None), limit)

    def test_constructor(self):
        self.assertIs(timezone.utc, timezone(timedelta(0)))
        self.assertIsNot(timezone.utc, timezone(timedelta(0), 'UTC'))
        self.assertEqual(timezone.utc, timezone(timedelta(0), 'UTC'))
        for invalid in [timedelta(microseconds=1), timedelta(1, 1),
            timedelta(seconds=1), timedelta(1), -timedelta(1)]:
            self.assertRaises(ValueError, timezone, invalid)
            self.assertRaises(ValueError, timezone, -invalid)
        with self.assertRaises(TypeError):
            timezone(None)
        with self.assertRaises(TypeError):
            timezone(42)
        with self.assertRaises(TypeError):
            timezone(ZERO, None)
        with self.assertRaises(TypeError):
            timezone(ZERO, 42)
        with self.assertRaises(TypeError):
            timezone(ZERO, 'ABC', 'extra')

    def test_inheritance(self):
        self.assertIsInstance(timezone.utc, tzinfo)
        self.assertIsInstance(self.EST, tzinfo)

    def test_utcoffset(self):
        dummy = self.DT
        for h in [0, 1.5, 12]:
            offset = h * HOUR
            self.assertEqual(offset, timezone(offset).utcoffset(dummy))
            self.assertEqual(-offset, timezone(-offset).utcoffset(dummy))
        with self.assertRaises(TypeError):
            self.EST.utcoffset('')
        with self.assertRaises(TypeError):
            self.EST.utcoffset(5)

    def test_dst(self):
        self.assertIsNone(timezone.utc.dst(self.DT))
        with self.assertRaises(TypeError):
            self.EST.dst('')
        with self.assertRaises(TypeError):
            self.EST.dst(5)

    def test_tzname(self):
        self.assertEqual('UTC', timezone.utc.tzname(None))
        self.assertEqual('UTC', timezone(ZERO).tzname(None))
        self.assertEqual('UTC-05:00', timezone(-5 * HOUR).tzname(None))
        self.assertEqual('UTC+09:30', timezone(9.5 * HOUR).tzname(None))
        self.assertEqual('UTC-00:01', timezone(timedelta(minutes=-1)).
            tzname(None))
        self.assertEqual('XYZ', timezone(-5 * HOUR, 'XYZ').tzname(None))
        with self.assertRaises(TypeError):
            self.EST.tzname('')
        with self.assertRaises(TypeError):
            self.EST.tzname(5)

    def test_fromutc(self):
        with self.assertRaises(ValueError):
            timezone.utc.fromutc(self.DT)
        with self.assertRaises(TypeError):
            timezone.utc.fromutc('not datetime')
        for tz in [self.EST, self.ACDT, Eastern]:
            utctime = self.DT.replace(tzinfo=tz)
            local = tz.fromutc(utctime)
            self.assertEqual(local - utctime, tz.utcoffset(local))
            self.assertEqual(local, self.DT.replace(tzinfo=timezone.utc))

    def test_comparison(self):
        self.assertNotEqual(timezone(ZERO), timezone(HOUR))
        self.assertEqual(timezone(HOUR), timezone(HOUR))
        self.assertEqual(timezone(-5 * HOUR), timezone(-5 * HOUR, 'EST'))
        with self.assertRaises(TypeError):
            timezone(ZERO) < timezone(ZERO)
        self.assertIn(timezone(ZERO), {timezone(ZERO)})
        self.assertTrue(timezone(ZERO) != None)
        self.assertFalse(timezone(ZERO) == None)

    def test_aware_datetime(self):
        t = datetime(1, 1, 1)
        for tz in [timezone.min, timezone.max, timezone.utc]:
            self.assertEqual(tz.tzname(t), t.replace(tzinfo=tz).tzname())
            self.assertEqual(tz.utcoffset(t), t.replace(tzinfo=tz).utcoffset())
            self.assertEqual(tz.dst(t), t.replace(tzinfo=tz).dst())

    def test_pickle(self):
        for tz in (self.ACDT, self.EST, timezone.min, timezone.max):
            for pickler, unpickler, proto in pickle_choices:
                tz_copy = unpickler.loads(pickler.dumps(tz, proto))
                self.assertEqual(tz_copy, tz)
        tz = timezone.utc
        for pickler, unpickler, proto in pickle_choices:
            tz_copy = unpickler.loads(pickler.dumps(tz, proto))
            self.assertIs(tz_copy, tz)

    def test_copy(self):
        for tz in (self.ACDT, self.EST, timezone.min, timezone.max):
            tz_copy = copy.copy(tz)
            self.assertEqual(tz_copy, tz)
        tz = timezone.utc
        tz_copy = copy.copy(tz)
        self.assertIs(tz_copy, tz)

    def test_deepcopy(self):
        for tz in (self.ACDT, self.EST, timezone.min, timezone.max):
            tz_copy = copy.deepcopy(tz)
            self.assertEqual(tz_copy, tz)
        tz = timezone.utc
        tz_copy = copy.deepcopy(tz)
        self.assertIs(tz_copy, tz)


class HarmlessMixedComparison:

    def test_harmless_mixed_comparison(self):
        me = self.theclass(1, 1, 1)
        self.assertFalse(me == ())
        self.assertTrue(me != ())
        self.assertFalse(() == me)
        self.assertTrue(() != me)
        self.assertIn(me, [1, 20, [], me])
        self.assertIn([], [me, 1, 20, []])

    def test_harmful_mixed_comparison(self):
        me = self.theclass(1, 1, 1)
        self.assertRaises(TypeError, lambda : me < ())
        self.assertRaises(TypeError, lambda : me <= ())
        self.assertRaises(TypeError, lambda : me > ())
        self.assertRaises(TypeError, lambda : me >= ())
        self.assertRaises(TypeError, lambda : () < me)
        self.assertRaises(TypeError, lambda : () <= me)
        self.assertRaises(TypeError, lambda : () > me)
        self.assertRaises(TypeError, lambda : () >= me)


class TestTimeDelta(HarmlessMixedComparison, unittest.TestCase):
    theclass = timedelta

    def test_constructor(self):
        eq = self.assertEqual
        td = timedelta
        eq(td(), td(weeks=0, days=0, hours=0, minutes=0, seconds=0,
            milliseconds=0, microseconds=0))
        eq(td(1), td(days=1))
        eq(td(0, 1), td(seconds=1))
        eq(td(0, 0, 1), td(microseconds=1))
        eq(td(weeks=1), td(days=7))
        eq(td(days=1), td(hours=24))
        eq(td(hours=1), td(minutes=60))
        eq(td(minutes=1), td(seconds=60))
        eq(td(seconds=1), td(milliseconds=1000))
        eq(td(milliseconds=1), td(microseconds=1000))
        eq(td(weeks=1.0 / 7), td(days=1))
        eq(td(days=1.0 / 24), td(hours=1))
        eq(td(hours=1.0 / 60), td(minutes=1))
        eq(td(minutes=1.0 / 60), td(seconds=1))
        eq(td(seconds=0.001), td(milliseconds=1))
        eq(td(milliseconds=0.001), td(microseconds=1))

    def test_computations(self):
        eq = self.assertEqual
        td = timedelta
        a = td(7)
        b = td(0, 60)
        c = td(0, 0, 1000)
        eq(a + b + c, td(7, 60, 1000))
        eq(a - b, td(6, 24 * 3600 - 60))
        eq(b.__rsub__(a), td(6, 24 * 3600 - 60))
        eq(-a, td(-7))
        eq(+a, td(7))
        eq(-b, td(-1, 24 * 3600 - 60))
        eq(-c, td(-1, 24 * 3600 - 1, 999000))
        eq(abs(a), a)
        eq(abs(-a), a)
        eq(td(6, 24 * 3600), a)
        eq(td(0, 0, 60 * 1000000), b)
        eq(a * 10, td(70))
        eq(a * 10, 10 * a)
        eq(a * 10, 10 * a)
        eq(b * 10, td(0, 600))
        eq(10 * b, td(0, 600))
        eq(b * 10, td(0, 600))
        eq(c * 10, td(0, 0, 10000))
        eq(10 * c, td(0, 0, 10000))
        eq(c * 10, td(0, 0, 10000))
        eq(a * -1, -a)
        eq(b * -2, -b - b)
        eq(c * -2, -c + -c)
        eq(b * (60 * 24), b * 60 * 24)
        eq(b * (60 * 24), 60 * b * 24)
        eq(c * 1000, td(0, 1))
        eq(1000 * c, td(0, 1))
        eq(a // 7, td(1))
        eq(b // 10, td(0, 6))
        eq(c // 1000, td(0, 0, 1))
        eq(a // 10, td(0, 7 * 24 * 360))
        eq(a // 3600000, td(0, 0, 7 * 24 * 1000))
        eq(a / 0.5, td(14))
        eq(b / 0.5, td(0, 120))
        eq(a / 7, td(1))
        eq(b / 10, td(0, 6))
        eq(c / 1000, td(0, 0, 1))
        eq(a / 10, td(0, 7 * 24 * 360))
        eq(a / 3600000, td(0, 0, 7 * 24 * 1000))
        us = td(microseconds=1)
        eq(3 * us * 0.5, 2 * us)
        eq(5 * us * 0.5, 2 * us)
        eq(0.5 * (3 * us), 2 * us)
        eq(0.5 * (5 * us), 2 * us)
        eq(-3 * us * 0.5, -2 * us)
        eq(-5 * us * 0.5, -2 * us)
        eq(td(seconds=1) * 0.123456, td(microseconds=123456))
        eq(td(seconds=1) * 0.6112295, td(microseconds=611229))
        eq(3 * us / 2, 2 * us)
        eq(5 * us / 2, 2 * us)
        eq(-3 * us / 2.0, -2 * us)
        eq(-5 * us / 2.0, -2 * us)
        eq(3 * us / -2, -2 * us)
        eq(5 * us / -2, -2 * us)
        eq(3 * us / -2.0, -2 * us)
        eq(5 * us / -2.0, -2 * us)
        for i in range(-10, 10):
            eq(i * us / 3 // us, round(i / 3))
        for i in range(-10, 10):
            eq(i * us / -3 // us, round(i / -3))
        eq(td(seconds=1) / (1 / 0.6112295), td(microseconds=611229))
        eq(td(999999999, 86399, 999999) - td(999999999, 86399, 999998), td(
            0, 0, 1))
        eq(td(999999999, 1, 1) - td(999999999, 1, 0), td(0, 0, 1))

    def test_disallowed_computations(self):
        a = timedelta(42)
        for i in (1, 1.0):
            self.assertRaises(TypeError, lambda : a + i)
            self.assertRaises(TypeError, lambda : a - i)
            self.assertRaises(TypeError, lambda : i + a)
            self.assertRaises(TypeError, lambda : i - a)
        zero = 0
        self.assertRaises(TypeError, lambda : zero // a)
        self.assertRaises(ZeroDivisionError, lambda : a // zero)
        self.assertRaises(ZeroDivisionError, lambda : a / zero)
        self.assertRaises(ZeroDivisionError, lambda : a / 0.0)
        self.assertRaises(TypeError, lambda : a / '')

    @support.requires_IEEE_754
    def test_disallowed_special(self):
        a = timedelta(42)
        self.assertRaises(ValueError, a.__mul__, NAN)
        self.assertRaises(ValueError, a.__truediv__, NAN)

    def test_basic_attributes(self):
        days, seconds, us = 1, 7, 31
        td = timedelta(days, seconds, us)
        self.assertEqual(td.days, days)
        self.assertEqual(td.seconds, seconds)
        self.assertEqual(td.microseconds, us)

    def test_total_seconds(self):
        td = timedelta(days=365)
        self.assertEqual(td.total_seconds(), 31536000.0)
        for total_seconds in [123456.789012, -123456.789012, 0.123456, 0, 
            1000000.0]:
            td = timedelta(seconds=total_seconds)
            self.assertEqual(td.total_seconds(), total_seconds)
        for ms in [-1, -2, -123]:
            td = timedelta(microseconds=ms)
            self.assertEqual(td.total_seconds(), td / timedelta(seconds=1))

    def test_carries(self):
        t1 = timedelta(days=100, weeks=-7, hours=-24 * (100 - 49), minutes=
            -3, seconds=12, microseconds=(3 * 60 - 12) * 1000000.0 + 1)
        t2 = timedelta(microseconds=1)
        self.assertEqual(t1, t2)

    def test_hash_equality(self):
        t1 = timedelta(days=100, weeks=-7, hours=-24 * (100 - 49), minutes=
            -3, seconds=12, microseconds=(3 * 60 - 12) * 1000000)
        t2 = timedelta()
        self.assertEqual(hash(t1), hash(t2))
        t1 += timedelta(weeks=7)
        t2 += timedelta(days=7 * 7)
        self.assertEqual(t1, t2)
        self.assertEqual(hash(t1), hash(t2))
        d = {t1: 1}
        d[t2] = 2
        self.assertEqual(len(d), 1)
        self.assertEqual(d[t1], 2)

    def test_pickling(self):
        args = 12, 34, 56
        orig = timedelta(*args)
        for pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)

    def test_compare(self):
        t1 = timedelta(2, 3, 4)
        t2 = timedelta(2, 3, 4)
        self.assertEqual(t1, t2)
        self.assertTrue(t1 <= t2)
        self.assertTrue(t1 >= t2)
        self.assertFalse(t1 != t2)
        self.assertFalse(t1 < t2)
        self.assertFalse(t1 > t2)
        for args in ((3, 3, 3), (2, 4, 4), (2, 3, 5)):
            t2 = timedelta(*args)
            self.assertTrue(t1 < t2)
            self.assertTrue(t2 > t1)
            self.assertTrue(t1 <= t2)
            self.assertTrue(t2 >= t1)
            self.assertTrue(t1 != t2)
            self.assertTrue(t2 != t1)
            self.assertFalse(t1 == t2)
            self.assertFalse(t2 == t1)
            self.assertFalse(t1 > t2)
            self.assertFalse(t2 < t1)
            self.assertFalse(t1 >= t2)
            self.assertFalse(t2 <= t1)
        for badarg in OTHERSTUFF:
            self.assertEqual(t1 == badarg, False)
            self.assertEqual(t1 != badarg, True)
            self.assertEqual(badarg == t1, False)
            self.assertEqual(badarg != t1, True)
            self.assertRaises(TypeError, lambda : t1 <= badarg)
            self.assertRaises(TypeError, lambda : t1 < badarg)
            self.assertRaises(TypeError, lambda : t1 > badarg)
            self.assertRaises(TypeError, lambda : t1 >= badarg)
            self.assertRaises(TypeError, lambda : badarg <= t1)
            self.assertRaises(TypeError, lambda : badarg < t1)
            self.assertRaises(TypeError, lambda : badarg > t1)
            self.assertRaises(TypeError, lambda : badarg >= t1)

    def test_str(self):
        td = timedelta
        eq = self.assertEqual
        eq(str(td(1)), '1 day, 0:00:00')
        eq(str(td(-1)), '-1 day, 0:00:00')
        eq(str(td(2)), '2 days, 0:00:00')
        eq(str(td(-2)), '-2 days, 0:00:00')
        eq(str(td(hours=12, minutes=58, seconds=59)), '12:58:59')
        eq(str(td(hours=2, minutes=3, seconds=4)), '2:03:04')
        eq(str(td(weeks=-30, hours=23, minutes=12, seconds=34)),
            '-210 days, 23:12:34')
        eq(str(td(milliseconds=1)), '0:00:00.001000')
        eq(str(td(microseconds=3)), '0:00:00.000003')
        eq(str(td(days=999999999, hours=23, minutes=59, seconds=59,
            microseconds=999999)), '999999999 days, 23:59:59.999999')

    def test_repr(self):
        name = 'datetime.' + self.theclass.__name__
        self.assertEqual(repr(self.theclass(1)), '%s(1)' % name)
        self.assertEqual(repr(self.theclass(10, 2)), '%s(10, 2)' % name)
        self.assertEqual(repr(self.theclass(-10, 2, 400000)), 
            '%s(-10, 2, 400000)' % name)

    def test_roundtrip(self):
        for td in (timedelta(days=999999999, hours=23, minutes=59, seconds=
            59, microseconds=999999), timedelta(days=-999999999), timedelta
            (days=-999999999, seconds=1), timedelta(days=1, seconds=2,
            microseconds=3)):
            s = repr(td)
            self.assertTrue(s.startswith('datetime.'))
            s = s[9:]
            td2 = eval(s)
            self.assertEqual(td, td2)
            td2 = timedelta(td.days, td.seconds, td.microseconds)
            self.assertEqual(td, td2)

    def test_resolution_info(self):
        self.assertIsInstance(timedelta.min, timedelta)
        self.assertIsInstance(timedelta.max, timedelta)
        self.assertIsInstance(timedelta.resolution, timedelta)
        self.assertTrue(timedelta.max > timedelta.min)
        self.assertEqual(timedelta.min, timedelta(-999999999))
        self.assertEqual(timedelta.max, timedelta(999999999, 24 * 3600 - 1,
            1000000.0 - 1))
        self.assertEqual(timedelta.resolution, timedelta(0, 0, 1))

    def test_overflow(self):
        tiny = timedelta.resolution
        td = timedelta.min + tiny
        td -= tiny
        self.assertRaises(OverflowError, td.__sub__, tiny)
        self.assertRaises(OverflowError, td.__add__, -tiny)
        td = timedelta.max - tiny
        td += tiny
        self.assertRaises(OverflowError, td.__add__, tiny)
        self.assertRaises(OverflowError, td.__sub__, -tiny)
        self.assertRaises(OverflowError, lambda : -timedelta.max)
        day = timedelta(1)
        self.assertRaises(OverflowError, day.__mul__, 10 ** 9)
        self.assertRaises(OverflowError, day.__mul__, 1000000000.0)
        self.assertRaises(OverflowError, day.__truediv__, 1e-20)
        self.assertRaises(OverflowError, day.__truediv__, 1e-10)
        self.assertRaises(OverflowError, day.__truediv__, 9e-10)

    @support.requires_IEEE_754
    def _test_overflow_special(self):
        day = timedelta(1)
        self.assertRaises(OverflowError, day.__mul__, INF)
        self.assertRaises(OverflowError, day.__mul__, -INF)

    def test_microsecond_rounding(self):
        td = timedelta
        eq = self.assertEqual
        eq(td(milliseconds=0.4 / 1000), td(0))
        eq(td(milliseconds=-0.4 / 1000), td(0))
        eq(td(milliseconds=0.5 / 1000), td(microseconds=0))
        eq(td(milliseconds=-0.5 / 1000), td(microseconds=-0))
        eq(td(milliseconds=0.6 / 1000), td(microseconds=1))
        eq(td(milliseconds=-0.6 / 1000), td(microseconds=-1))
        eq(td(milliseconds=1.5 / 1000), td(microseconds=2))
        eq(td(milliseconds=-1.5 / 1000), td(microseconds=-2))
        eq(td(seconds=0.5 / 10 ** 6), td(microseconds=0))
        eq(td(seconds=-0.5 / 10 ** 6), td(microseconds=-0))
        eq(td(seconds=1 / 2 ** 7), td(microseconds=7812))
        eq(td(seconds=-1 / 2 ** 7), td(microseconds=-7812))
        us_per_hour = 3600000000.0
        us_per_day = us_per_hour * 24
        eq(td(days=0.4 / us_per_day), td(0))
        eq(td(hours=0.2 / us_per_hour), td(0))
        eq(td(days=0.4 / us_per_day, hours=0.2 / us_per_hour), td(
            microseconds=1))
        eq(td(days=-0.4 / us_per_day), td(0))
        eq(td(hours=-0.2 / us_per_hour), td(0))
        eq(td(days=-0.4 / us_per_day, hours=-0.2 / us_per_hour), td(
            microseconds=-1))
        eq(td(microseconds=0.5), 0.5 * td(microseconds=1.0))
        eq(td(microseconds=0.5) // td.resolution, 0.5 * td.resolution // td
            .resolution)

    def test_massive_normalization(self):
        td = timedelta(microseconds=-1)
        self.assertEqual((td.days, td.seconds, td.microseconds), (-1, 24 * 
            3600 - 1, 999999))

    def test_bool(self):
        self.assertTrue(timedelta(1))
        self.assertTrue(timedelta(0, 1))
        self.assertTrue(timedelta(0, 0, 1))
        self.assertTrue(timedelta(microseconds=1))
        self.assertFalse(timedelta(0))

    def test_subclass_timedelta(self):


        class T(timedelta):

            @staticmethod
            def from_td(td):
                return T(td.days, td.seconds, td.microseconds)

            def as_hours(self):
                sum = (self.days * 24 + self.seconds / 3600.0 + self.
                    microseconds / 3600000000.0)
                return round(sum)
        t1 = T(days=1)
        self.assertIs(type(t1), T)
        self.assertEqual(t1.as_hours(), 24)
        t2 = T(days=-1, seconds=-3600)
        self.assertIs(type(t2), T)
        self.assertEqual(t2.as_hours(), -25)
        t3 = t1 + t2
        self.assertIs(type(t3), timedelta)
        t4 = T.from_td(t3)
        self.assertIs(type(t4), T)
        self.assertEqual(t3.days, t4.days)
        self.assertEqual(t3.seconds, t4.seconds)
        self.assertEqual(t3.microseconds, t4.microseconds)
        self.assertEqual(str(t3), str(t4))
        self.assertEqual(t4.as_hours(), -1)

    def test_division(self):
        t = timedelta(hours=1, minutes=24, seconds=19)
        second = timedelta(seconds=1)
        self.assertEqual(t / second, 5059.0)
        self.assertEqual(t // second, 5059)
        t = timedelta(minutes=2, seconds=30)
        minute = timedelta(minutes=1)
        self.assertEqual(t / minute, 2.5)
        self.assertEqual(t // minute, 2)
        zerotd = timedelta(0)
        self.assertRaises(ZeroDivisionError, truediv, t, zerotd)
        self.assertRaises(ZeroDivisionError, floordiv, t, zerotd)

    def test_remainder(self):
        t = timedelta(minutes=2, seconds=30)
        minute = timedelta(minutes=1)
        r = t % minute
        self.assertEqual(r, timedelta(seconds=30))
        t = timedelta(minutes=-2, seconds=30)
        r = t % minute
        self.assertEqual(r, timedelta(seconds=30))
        zerotd = timedelta(0)
        self.assertRaises(ZeroDivisionError, mod, t, zerotd)
        self.assertRaises(TypeError, mod, t, 10)

    def test_divmod(self):
        t = timedelta(minutes=2, seconds=30)
        minute = timedelta(minutes=1)
        q, r = divmod(t, minute)
        self.assertEqual(q, 2)
        self.assertEqual(r, timedelta(seconds=30))
        t = timedelta(minutes=-2, seconds=30)
        q, r = divmod(t, minute)
        self.assertEqual(q, -2)
        self.assertEqual(r, timedelta(seconds=30))
        zerotd = timedelta(0)
        self.assertRaises(ZeroDivisionError, divmod, t, zerotd)
        self.assertRaises(TypeError, divmod, t, 10)


class TestDateOnly(unittest.TestCase):

    def test_delta_non_days_ignored(self):
        dt = date(2000, 1, 2)
        delta = timedelta(days=1, hours=2, minutes=3, seconds=4, microseconds=5
            )
        days = timedelta(delta.days)
        self.assertEqual(days, timedelta(1))
        dt2 = dt + delta
        self.assertEqual(dt2, dt + days)
        dt2 = delta + dt
        self.assertEqual(dt2, dt + days)
        dt2 = dt - delta
        self.assertEqual(dt2, dt - days)
        delta = -delta
        days = timedelta(delta.days)
        self.assertEqual(days, timedelta(-2))
        dt2 = dt + delta
        self.assertEqual(dt2, dt + days)
        dt2 = delta + dt
        self.assertEqual(dt2, dt + days)
        dt2 = dt - delta
        self.assertEqual(dt2, dt - days)


class SubclassDate(date):
    sub_var = 1


class TestDate(HarmlessMixedComparison, unittest.TestCase):
    theclass = date

    def test_basic_attributes(self):
        dt = self.theclass(2002, 3, 1)
        self.assertEqual(dt.year, 2002)
        self.assertEqual(dt.month, 3)
        self.assertEqual(dt.day, 1)

    def test_roundtrip(self):
        for dt in (self.theclass(1, 2, 3), self.theclass.today()):
            s = repr(dt)
            self.assertTrue(s.startswith('datetime.'))
            s = s[9:]
            dt2 = eval(s)
            self.assertEqual(dt, dt2)
            dt2 = self.theclass(dt.year, dt.month, dt.day)
            self.assertEqual(dt, dt2)

    def test_ordinal_conversions(self):
        for y, m, d, n in [(1, 1, 1, 1), (1, 12, 31, 365), (2, 1, 1, 366),
            (1945, 11, 12, 710347)]:
            d = self.theclass(y, m, d)
            self.assertEqual(n, d.toordinal())
            fromord = self.theclass.fromordinal(n)
            self.assertEqual(d, fromord)
            if hasattr(fromord, 'hour'):
                self.assertEqual(fromord.hour, 0)
                self.assertEqual(fromord.minute, 0)
                self.assertEqual(fromord.second, 0)
                self.assertEqual(fromord.microsecond, 0)
        for year in range(MINYEAR, MAXYEAR + 1, 7):
            d = self.theclass(year, 1, 1)
            n = d.toordinal()
            d2 = self.theclass.fromordinal(n)
            self.assertEqual(d, d2)
            if year > 1:
                d = self.theclass.fromordinal(n - 1)
                d2 = self.theclass(year - 1, 12, 31)
                self.assertEqual(d, d2)
                self.assertEqual(d2.toordinal(), n - 1)
        dim = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        for year, isleap in ((2000, True), (2002, False)):
            n = self.theclass(year, 1, 1).toordinal()
            for month, maxday in zip(range(1, 13), dim):
                if month == 2 and isleap:
                    maxday += 1
                for day in range(1, maxday + 1):
                    d = self.theclass(year, month, day)
                    self.assertEqual(d.toordinal(), n)
                    self.assertEqual(d, self.theclass.fromordinal(n))
                    n += 1

    def test_extreme_ordinals(self):
        a = self.theclass.min
        a = self.theclass(a.year, a.month, a.day)
        aord = a.toordinal()
        b = a.fromordinal(aord)
        self.assertEqual(a, b)
        self.assertRaises(ValueError, lambda : a.fromordinal(aord - 1))
        b = a + timedelta(days=1)
        self.assertEqual(b.toordinal(), aord + 1)
        self.assertEqual(b, self.theclass.fromordinal(aord + 1))
        a = self.theclass.max
        a = self.theclass(a.year, a.month, a.day)
        aord = a.toordinal()
        b = a.fromordinal(aord)
        self.assertEqual(a, b)
        self.assertRaises(ValueError, lambda : a.fromordinal(aord + 1))
        b = a - timedelta(days=1)
        self.assertEqual(b.toordinal(), aord - 1)
        self.assertEqual(b, self.theclass.fromordinal(aord - 1))

    def test_bad_constructor_arguments(self):
        self.theclass(MINYEAR, 1, 1)
        self.theclass(MAXYEAR, 1, 1)
        self.assertRaises(ValueError, self.theclass, MINYEAR - 1, 1, 1)
        self.assertRaises(ValueError, self.theclass, MAXYEAR + 1, 1, 1)
        self.theclass(2000, 1, 1)
        self.theclass(2000, 12, 1)
        self.assertRaises(ValueError, self.theclass, 2000, 0, 1)
        self.assertRaises(ValueError, self.theclass, 2000, 13, 1)
        self.theclass(2000, 2, 29)
        self.theclass(2004, 2, 29)
        self.theclass(2400, 2, 29)
        self.assertRaises(ValueError, self.theclass, 2000, 2, 30)
        self.assertRaises(ValueError, self.theclass, 2001, 2, 29)
        self.assertRaises(ValueError, self.theclass, 2100, 2, 29)
        self.assertRaises(ValueError, self.theclass, 1900, 2, 29)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 0)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 32)

    def test_hash_equality(self):
        d = self.theclass(2000, 12, 31)
        e = self.theclass(2000, 12, 31)
        self.assertEqual(d, e)
        self.assertEqual(hash(d), hash(e))
        dic = {d: 1}
        dic[e] = 2
        self.assertEqual(len(dic), 1)
        self.assertEqual(dic[d], 2)
        self.assertEqual(dic[e], 2)
        d = self.theclass(2001, 1, 1)
        e = self.theclass(2001, 1, 1)
        self.assertEqual(d, e)
        self.assertEqual(hash(d), hash(e))
        dic = {d: 1}
        dic[e] = 2
        self.assertEqual(len(dic), 1)
        self.assertEqual(dic[d], 2)
        self.assertEqual(dic[e], 2)

    def test_computations(self):
        a = self.theclass(2002, 1, 31)
        b = self.theclass(1956, 1, 31)
        c = self.theclass(2001, 2, 1)
        diff = a - b
        self.assertEqual(diff.days, 46 * 365 + len(range(1956, 2002, 4)))
        self.assertEqual(diff.seconds, 0)
        self.assertEqual(diff.microseconds, 0)
        day = timedelta(1)
        week = timedelta(7)
        a = self.theclass(2002, 3, 2)
        self.assertEqual(a + day, self.theclass(2002, 3, 3))
        self.assertEqual(day + a, self.theclass(2002, 3, 3))
        self.assertEqual(a - day, self.theclass(2002, 3, 1))
        self.assertEqual(-day + a, self.theclass(2002, 3, 1))
        self.assertEqual(a + week, self.theclass(2002, 3, 9))
        self.assertEqual(a - week, self.theclass(2002, 2, 23))
        self.assertEqual(a + 52 * week, self.theclass(2003, 3, 1))
        self.assertEqual(a - 52 * week, self.theclass(2001, 3, 3))
        self.assertEqual(a + week - a, week)
        self.assertEqual(a + day - a, day)
        self.assertEqual(a - week - a, -week)
        self.assertEqual(a - day - a, -day)
        self.assertEqual(a - (a + week), -week)
        self.assertEqual(a - (a + day), -day)
        self.assertEqual(a - (a - week), week)
        self.assertEqual(a - (a - day), day)
        self.assertEqual(c - (c - day), day)
        for i in (1, 1.0):
            self.assertRaises(TypeError, lambda : a + i)
            self.assertRaises(TypeError, lambda : a - i)
            self.assertRaises(TypeError, lambda : i + a)
            self.assertRaises(TypeError, lambda : i - a)
        self.assertRaises(TypeError, lambda : day - a)
        self.assertRaises(TypeError, lambda : day * a)
        self.assertRaises(TypeError, lambda : a * day)
        self.assertRaises(TypeError, lambda : day // a)
        self.assertRaises(TypeError, lambda : a // day)
        self.assertRaises(TypeError, lambda : a * a)
        self.assertRaises(TypeError, lambda : a // a)
        self.assertRaises(TypeError, lambda : a + a)

    def test_overflow(self):
        tiny = self.theclass.resolution
        for delta in [tiny, timedelta(1), timedelta(2)]:
            dt = self.theclass.min + delta
            dt -= delta
            self.assertRaises(OverflowError, dt.__sub__, delta)
            self.assertRaises(OverflowError, dt.__add__, -delta)
            dt = self.theclass.max - delta
            dt += delta
            self.assertRaises(OverflowError, dt.__add__, delta)
            self.assertRaises(OverflowError, dt.__sub__, -delta)

    def test_fromtimestamp(self):
        import time
        year, month, day = 1999, 9, 19
        ts = time.mktime((year, month, day, 0, 0, 0, 0, 0, -1))
        d = self.theclass.fromtimestamp(ts)
        self.assertEqual(d.year, year)
        self.assertEqual(d.month, month)
        self.assertEqual(d.day, day)

    def test_insane_fromtimestamp(self):
        for insane in (-1e+200, 1e+200):
            self.assertRaises(OverflowError, self.theclass.fromtimestamp,
                insane)

    def test_today(self):
        import time
        for dummy in range(3):
            today = self.theclass.today()
            ts = time.time()
            todayagain = self.theclass.fromtimestamp(ts)
            if today == todayagain:
                break
            time.sleep(0.1)
        if today != todayagain:
            self.assertAlmostEqual(todayagain, today, delta=timedelta(
                seconds=0.5))

    def test_weekday(self):
        for i in range(7):
            self.assertEqual(self.theclass(2002, 3, 4 + i).weekday(), i)
            self.assertEqual(self.theclass(2002, 3, 4 + i).isoweekday(), i + 1)
            self.assertEqual(self.theclass(1956, 1, 2 + i).weekday(), i)
            self.assertEqual(self.theclass(1956, 1, 2 + i).isoweekday(), i + 1)

    def test_isocalendar(self):
        for i in range(7):
            d = self.theclass(2003, 12, 22 + i)
            self.assertEqual(d.isocalendar(), (2003, 52, i + 1))
            d = self.theclass(2003, 12, 29) + timedelta(i)
            self.assertEqual(d.isocalendar(), (2004, 1, i + 1))
            d = self.theclass(2004, 1, 5 + i)
            self.assertEqual(d.isocalendar(), (2004, 2, i + 1))
            d = self.theclass(2009, 12, 21 + i)
            self.assertEqual(d.isocalendar(), (2009, 52, i + 1))
            d = self.theclass(2009, 12, 28) + timedelta(i)
            self.assertEqual(d.isocalendar(), (2009, 53, i + 1))
            d = self.theclass(2010, 1, 4 + i)
            self.assertEqual(d.isocalendar(), (2010, 1, i + 1))

    def test_iso_long_years(self):
        ISO_LONG_YEARS_TABLE = """
              4   32   60   88
              9   37   65   93
             15   43   71   99
             20   48   76
             26   54   82

            105  133  161  189
            111  139  167  195
            116  144  172
            122  150  178
            128  156  184

            201  229  257  285
            207  235  263  291
            212  240  268  296
            218  246  274
            224  252  280

            303  331  359  387
            308  336  364  392
            314  342  370  398
            320  348  376
            325  353  381
        """
        iso_long_years = sorted(map(int, ISO_LONG_YEARS_TABLE.split()))
        L = []
        for i in range(400):
            d = self.theclass(2000 + i, 12, 31)
            d1 = self.theclass(1600 + i, 12, 31)
            self.assertEqual(d.isocalendar()[1:], d1.isocalendar()[1:])
            if d.isocalendar()[1] == 53:
                L.append(i)
        self.assertEqual(L, iso_long_years)

    def test_isoformat(self):
        t = self.theclass(2, 3, 2)
        self.assertEqual(t.isoformat(), '0002-03-02')

    def test_ctime(self):
        t = self.theclass(2002, 3, 2)
        self.assertEqual(t.ctime(), 'Sat Mar  2 00:00:00 2002')

    def test_strftime(self):
        t = self.theclass(2005, 3, 2)
        self.assertEqual(t.strftime('m:%m d:%d y:%y'), 'm:03 d:02 y:05')
        self.assertEqual(t.strftime(''), '')
        self.assertEqual(t.strftime('x' * 1000), 'x' * 1000)
        self.assertRaises(TypeError, t.strftime)
        self.assertRaises(TypeError, t.strftime, 'one', 'two')
        self.assertRaises(TypeError, t.strftime, 42)
        self.assertEqual(t.strftime('%m'), '03')
        self.assertEqual(t.strftime("'%z' '%Z'"), "'' ''")
        for f in ['%e', '%', '%#']:
            try:
                t.strftime(f)
            except ValueError:
                pass
        t.strftime('%f')

    def test_format(self):
        dt = self.theclass(2007, 9, 10)
        self.assertEqual(dt.__format__(''), str(dt))
        with self.assertRaisesRegex(TypeError, 'must be str, not int'):
            dt.__format__(123)


        class A(self.theclass):

            def __str__(self):
                return 'A'
        a = A(2007, 9, 10)
        self.assertEqual(a.__format__(''), 'A')


        class B(self.theclass):

            def strftime(self, format_spec):
                return 'B'
        b = B(2007, 9, 10)
        self.assertEqual(b.__format__(''), str(dt))
        for fmt in ['m:%m d:%d y:%y', 'm:%m d:%d y:%y H:%H M:%M S:%S', '%z %Z'
            ]:
            self.assertEqual(dt.__format__(fmt), dt.strftime(fmt))
            self.assertEqual(a.__format__(fmt), dt.strftime(fmt))
            self.assertEqual(b.__format__(fmt), 'B')

    def test_resolution_info(self):
        if issubclass(self.theclass, datetime):
            expected_class = datetime
        else:
            expected_class = date
        self.assertIsInstance(self.theclass.min, expected_class)
        self.assertIsInstance(self.theclass.max, expected_class)
        self.assertIsInstance(self.theclass.resolution, timedelta)
        self.assertTrue(self.theclass.max > self.theclass.min)

    def test_extreme_timedelta(self):
        big = self.theclass.max - self.theclass.min
        n = (big.days * 24 * 3600 + big.seconds) * 1000000 + big.microseconds
        justasbig = timedelta(0, 0, n)
        self.assertEqual(big, justasbig)
        self.assertEqual(self.theclass.min + big, self.theclass.max)
        self.assertEqual(self.theclass.max - big, self.theclass.min)

    def test_timetuple(self):
        for i in range(7):
            d = self.theclass(1956, 1, 2 + i)
            t = d.timetuple()
            self.assertEqual(t, (1956, 1, 2 + i, 0, 0, 0, i, 2 + i, -1))
            d = self.theclass(1956, 2, 1 + i)
            t = d.timetuple()
            self.assertEqual(t, (1956, 2, 1 + i, 0, 0, 0, (2 + i) % 7, 32 +
                i, -1))
            d = self.theclass(1956, 3, 1 + i)
            t = d.timetuple()
            self.assertEqual(t, (1956, 3, 1 + i, 0, 0, 0, (3 + i) % 7, 61 +
                i, -1))
            self.assertEqual(t.tm_year, 1956)
            self.assertEqual(t.tm_mon, 3)
            self.assertEqual(t.tm_mday, 1 + i)
            self.assertEqual(t.tm_hour, 0)
            self.assertEqual(t.tm_min, 0)
            self.assertEqual(t.tm_sec, 0)
            self.assertEqual(t.tm_wday, (3 + i) % 7)
            self.assertEqual(t.tm_yday, 61 + i)
            self.assertEqual(t.tm_isdst, -1)

    def test_pickling(self):
        args = 6, 7, 23
        orig = self.theclass(*args)
        for pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)
        self.assertEqual(orig.__reduce__(), orig.__reduce_ex__(2))

    def test_compare(self):
        t1 = self.theclass(2, 3, 4)
        t2 = self.theclass(2, 3, 4)
        self.assertEqual(t1, t2)
        self.assertTrue(t1 <= t2)
        self.assertTrue(t1 >= t2)
        self.assertFalse(t1 != t2)
        self.assertFalse(t1 < t2)
        self.assertFalse(t1 > t2)
        for args in ((3, 3, 3), (2, 4, 4), (2, 3, 5)):
            t2 = self.theclass(*args)
            self.assertTrue(t1 < t2)
            self.assertTrue(t2 > t1)
            self.assertTrue(t1 <= t2)
            self.assertTrue(t2 >= t1)
            self.assertTrue(t1 != t2)
            self.assertTrue(t2 != t1)
            self.assertFalse(t1 == t2)
            self.assertFalse(t2 == t1)
            self.assertFalse(t1 > t2)
            self.assertFalse(t2 < t1)
            self.assertFalse(t1 >= t2)
            self.assertFalse(t2 <= t1)
        for badarg in OTHERSTUFF:
            self.assertEqual(t1 == badarg, False)
            self.assertEqual(t1 != badarg, True)
            self.assertEqual(badarg == t1, False)
            self.assertEqual(badarg != t1, True)
            self.assertRaises(TypeError, lambda : t1 < badarg)
            self.assertRaises(TypeError, lambda : t1 > badarg)
            self.assertRaises(TypeError, lambda : t1 >= badarg)
            self.assertRaises(TypeError, lambda : badarg <= t1)
            self.assertRaises(TypeError, lambda : badarg < t1)
            self.assertRaises(TypeError, lambda : badarg > t1)
            self.assertRaises(TypeError, lambda : badarg >= t1)

    def test_mixed_compare(self):
        our = self.theclass(2000, 4, 5)
        self.assertEqual(our == 1, False)
        self.assertEqual(1 == our, False)
        self.assertEqual(our != 1, True)
        self.assertEqual(1 != our, True)
        self.assertRaises(TypeError, lambda : our < 1)
        self.assertRaises(TypeError, lambda : 1 < our)


        class SomeClass:
            pass
        their = SomeClass()
        self.assertEqual(our == their, False)
        self.assertEqual(their == our, False)
        self.assertEqual(our != their, True)
        self.assertEqual(their != our, True)
        self.assertRaises(TypeError, lambda : our < their)
        self.assertRaises(TypeError, lambda : their < our)


        class LargerThanAnything:

            def __lt__(self, other):
                return False

            def __le__(self, other):
                return isinstance(other, LargerThanAnything)

            def __eq__(self, other):
                return isinstance(other, LargerThanAnything)

            def __gt__(self, other):
                return not isinstance(other, LargerThanAnything)

            def __ge__(self, other):
                return True
        their = LargerThanAnything()
        self.assertEqual(our == their, False)
        self.assertEqual(their == our, False)
        self.assertEqual(our != their, True)
        self.assertEqual(their != our, True)
        self.assertEqual(our < their, True)
        self.assertEqual(their < our, False)

    def test_bool(self):
        self.assertTrue(self.theclass.min)
        self.assertTrue(self.theclass.max)

    def test_strftime_y2k(self):
        for y in (1, 49, 70, 99, 100, 999, 1000, 1970):
            d = self.theclass(y, 1, 1)
            if d.strftime('%Y') != '%04d' % y:
                self.assertEqual(d.strftime('%Y'), '%d' % y)
                self.assertEqual(d.strftime('%4Y'), '%04d' % y)

    def test_replace(self):
        cls = self.theclass
        args = [1, 2, 3]
        base = cls(*args)
        self.assertEqual(base, base.replace())
        i = 0
        for name, newval in (('year', 2), ('month', 3), ('day', 4)):
            newargs = args[:]
            newargs[i] = newval
            expected = cls(*newargs)
            got = base.replace(**{name: newval})
            self.assertEqual(expected, got)
            i += 1
        base = cls(2000, 2, 29)
        self.assertRaises(ValueError, base.replace, year=2001)

    def test_subclass_date(self):


        class C(self.theclass):
            theAnswer = 42

            def __new__(cls, *args, **kws):
                temp = kws.copy()
                extra = temp.pop('extra')
                result = self.theclass.__new__(cls, *args, **temp)
                result.extra = extra
                return result

            def newmeth(self, start):
                return start + self.year + self.month
        args = 2003, 4, 14
        dt1 = self.theclass(*args)
        dt2 = C(*args, **{'extra': 7})
        self.assertEqual(dt2.__class__, C)
        self.assertEqual(dt2.theAnswer, 42)
        self.assertEqual(dt2.extra, 7)
        self.assertEqual(dt1.toordinal(), dt2.toordinal())
        self.assertEqual(dt2.newmeth(-7), dt1.year + dt1.month - 7)

    def test_pickling_subclass_date(self):
        args = 6, 7, 23
        orig = SubclassDate(*args)
        for pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)

    def test_backdoor_resistance(self):
        base = b'1995-03-25'
        if not issubclass(self.theclass, datetime):
            base = base[:4]
        for month_byte in (b'9', b'\x00', b'\r', b'\xff'):
            self.assertRaises(TypeError, self.theclass, base[:2] +
                month_byte + base[3:])
        if issubclass(self.theclass, datetime):
            with self.assertRaisesRegex(TypeError, '^bad tzinfo state arg$'):
                self.theclass(bytes([1] * len(base)), 'EST')
        for ord_byte in range(1, 13):
            self.theclass(base[:2] + bytes([ord_byte]) + base[3:])


class SubclassDatetime(datetime):
    sub_var = 1


class TestDateTime(TestDate):
    theclass = datetime

    def test_basic_attributes(self):
        dt = self.theclass(2002, 3, 1, 12, 0)
        self.assertEqual(dt.year, 2002)
        self.assertEqual(dt.month, 3)
        self.assertEqual(dt.day, 1)
        self.assertEqual(dt.hour, 12)
        self.assertEqual(dt.minute, 0)
        self.assertEqual(dt.second, 0)
        self.assertEqual(dt.microsecond, 0)

    def test_basic_attributes_nonzero(self):
        dt = self.theclass(2002, 3, 1, 12, 59, 59, 8000)
        self.assertEqual(dt.year, 2002)
        self.assertEqual(dt.month, 3)
        self.assertEqual(dt.day, 1)
        self.assertEqual(dt.hour, 12)
        self.assertEqual(dt.minute, 59)
        self.assertEqual(dt.second, 59)
        self.assertEqual(dt.microsecond, 8000)

    def test_roundtrip(self):
        for dt in (self.theclass(1, 2, 3, 4, 5, 6, 7), self.theclass.now()):
            s = repr(dt)
            self.assertTrue(s.startswith('datetime.'))
            s = s[9:]
            dt2 = eval(s)
            self.assertEqual(dt, dt2)
            dt2 = self.theclass(dt.year, dt.month, dt.day, dt.hour, dt.
                minute, dt.second, dt.microsecond)
            self.assertEqual(dt, dt2)

    def test_isoformat(self):
        t = self.theclass(1, 2, 3, 4, 5, 1, 123)
        self.assertEqual(t.isoformat(), '0001-02-03T04:05:01.000123')
        self.assertEqual(t.isoformat('T'), '0001-02-03T04:05:01.000123')
        self.assertEqual(t.isoformat(' '), '0001-02-03 04:05:01.000123')
        self.assertEqual(t.isoformat('\x00'), '0001-02-03\x0004:05:01.000123')
        self.assertEqual(t.isoformat(timespec='hours'), '0001-02-03T04')
        self.assertEqual(t.isoformat(timespec='minutes'), '0001-02-03T04:05')
        self.assertEqual(t.isoformat(timespec='seconds'), '0001-02-03T04:05:01'
            )
        self.assertEqual(t.isoformat(timespec='milliseconds'),
            '0001-02-03T04:05:01.000')
        self.assertEqual(t.isoformat(timespec='microseconds'),
            '0001-02-03T04:05:01.000123')
        self.assertEqual(t.isoformat(timespec='auto'),
            '0001-02-03T04:05:01.000123')
        self.assertEqual(t.isoformat(sep=' ', timespec='minutes'),
            '0001-02-03 04:05')
        self.assertRaises(ValueError, t.isoformat, timespec='foo')
        self.assertEqual(str(t), '0001-02-03 04:05:01.000123')
        t = self.theclass(1, 2, 3, 4, 5, 1, 999500, tzinfo=timezone.utc)
        self.assertEqual(t.isoformat(timespec='milliseconds'),
            '0001-02-03T04:05:01.999+00:00')
        t = self.theclass(1, 2, 3, 4, 5, 1, 999500)
        self.assertEqual(t.isoformat(timespec='milliseconds'),
            '0001-02-03T04:05:01.999')
        t = self.theclass(1, 2, 3, 4, 5, 1)
        self.assertEqual(t.isoformat(timespec='auto'), '0001-02-03T04:05:01')
        self.assertEqual(t.isoformat(timespec='milliseconds'),
            '0001-02-03T04:05:01.000')
        self.assertEqual(t.isoformat(timespec='microseconds'),
            '0001-02-03T04:05:01.000000')
        t = self.theclass(2, 3, 2)
        self.assertEqual(t.isoformat(), '0002-03-02T00:00:00')
        self.assertEqual(t.isoformat('T'), '0002-03-02T00:00:00')
        self.assertEqual(t.isoformat(' '), '0002-03-02 00:00:00')
        self.assertEqual(str(t), '0002-03-02 00:00:00')
        tz = FixedOffset(timedelta(seconds=16), 'XXX')
        t = self.theclass(2, 3, 2, tzinfo=tz)
        self.assertEqual(t.isoformat(), '0002-03-02T00:00:00+00:00:16')

    def test_format(self):
        dt = self.theclass(2007, 9, 10, 4, 5, 1, 123)
        self.assertEqual(dt.__format__(''), str(dt))
        with self.assertRaisesRegex(TypeError, 'must be str, not int'):
            dt.__format__(123)


        class A(self.theclass):

            def __str__(self):
                return 'A'
        a = A(2007, 9, 10, 4, 5, 1, 123)
        self.assertEqual(a.__format__(''), 'A')


        class B(self.theclass):

            def strftime(self, format_spec):
                return 'B'
        b = B(2007, 9, 10, 4, 5, 1, 123)
        self.assertEqual(b.__format__(''), str(dt))
        for fmt in ['m:%m d:%d y:%y', 'm:%m d:%d y:%y H:%H M:%M S:%S', '%z %Z'
            ]:
            self.assertEqual(dt.__format__(fmt), dt.strftime(fmt))
            self.assertEqual(a.__format__(fmt), dt.strftime(fmt))
            self.assertEqual(b.__format__(fmt), 'B')

    def test_more_ctime(self):
        import time
        t = self.theclass(2002, 3, 2, 18, 3, 5, 123)
        self.assertEqual(t.ctime(), 'Sat Mar  2 18:03:05 2002')
        t = self.theclass(2002, 3, 22, 18, 3, 5, 123)
        self.assertEqual(t.ctime(), time.ctime(time.mktime(t.timetuple())))

    def test_tz_independent_comparing(self):
        dt1 = self.theclass(2002, 3, 1, 9, 0, 0)
        dt2 = self.theclass(2002, 3, 1, 10, 0, 0)
        dt3 = self.theclass(2002, 3, 1, 9, 0, 0)
        self.assertEqual(dt1, dt3)
        self.assertTrue(dt2 > dt3)
        dt1 = self.theclass(MAXYEAR, 12, 31, 23, 59, 59, 999998)
        us = timedelta(microseconds=1)
        dt2 = dt1 + us
        self.assertEqual(dt2 - dt1, us)
        self.assertTrue(dt1 < dt2)

    def test_strftime_with_bad_tzname_replace(self):


        class MyTzInfo(FixedOffset):

            def tzname(self, dt):


                class MyStr(str):

                    def replace(self, *args):
                        return None
                return MyStr('name')
        t = self.theclass(2005, 3, 2, 0, 0, 0, 0, MyTzInfo(3, 'name'))
        self.assertRaises(TypeError, t.strftime, '%Z')

    def test_bad_constructor_arguments(self):
        self.theclass(MINYEAR, 1, 1)
        self.theclass(MAXYEAR, 1, 1)
        self.assertRaises(ValueError, self.theclass, MINYEAR - 1, 1, 1)
        self.assertRaises(ValueError, self.theclass, MAXYEAR + 1, 1, 1)
        self.theclass(2000, 1, 1)
        self.theclass(2000, 12, 1)
        self.assertRaises(ValueError, self.theclass, 2000, 0, 1)
        self.assertRaises(ValueError, self.theclass, 2000, 13, 1)
        self.theclass(2000, 2, 29)
        self.theclass(2004, 2, 29)
        self.theclass(2400, 2, 29)
        self.assertRaises(ValueError, self.theclass, 2000, 2, 30)
        self.assertRaises(ValueError, self.theclass, 2001, 2, 29)
        self.assertRaises(ValueError, self.theclass, 2100, 2, 29)
        self.assertRaises(ValueError, self.theclass, 1900, 2, 29)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 0)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 32)
        self.theclass(2000, 1, 31, 0)
        self.theclass(2000, 1, 31, 23)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, -1)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, 24)
        self.theclass(2000, 1, 31, 23, 0)
        self.theclass(2000, 1, 31, 23, 59)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, 23, -1)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, 23, 60)
        self.theclass(2000, 1, 31, 23, 59, 0)
        self.theclass(2000, 1, 31, 23, 59, 59)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, 23, 59, -1)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, 23, 59, 60)
        self.theclass(2000, 1, 31, 23, 59, 59, 0)
        self.theclass(2000, 1, 31, 23, 59, 59, 999999)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, 23, 59, 
            59, -1)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, 23, 59, 
            59, 1000000)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, fold=-1)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, fold=2)
        self.assertRaises(TypeError, self.theclass, 2000, 1, 31, 23, 59, 59,
            0, None, 1)

    def test_hash_equality(self):
        d = self.theclass(2000, 12, 31, 23, 30, 17)
        e = self.theclass(2000, 12, 31, 23, 30, 17)
        self.assertEqual(d, e)
        self.assertEqual(hash(d), hash(e))
        dic = {d: 1}
        dic[e] = 2
        self.assertEqual(len(dic), 1)
        self.assertEqual(dic[d], 2)
        self.assertEqual(dic[e], 2)
        d = self.theclass(2001, 1, 1, 0, 5, 17)
        e = self.theclass(2001, 1, 1, 0, 5, 17)
        self.assertEqual(d, e)
        self.assertEqual(hash(d), hash(e))
        dic = {d: 1}
        dic[e] = 2
        self.assertEqual(len(dic), 1)
        self.assertEqual(dic[d], 2)
        self.assertEqual(dic[e], 2)

    def test_computations(self):
        a = self.theclass(2002, 1, 31)
        b = self.theclass(1956, 1, 31)
        diff = a - b
        self.assertEqual(diff.days, 46 * 365 + len(range(1956, 2002, 4)))
        self.assertEqual(diff.seconds, 0)
        self.assertEqual(diff.microseconds, 0)
        a = self.theclass(2002, 3, 2, 17, 6)
        millisec = timedelta(0, 0, 1000)
        hour = timedelta(0, 3600)
        day = timedelta(1)
        week = timedelta(7)
        self.assertEqual(a + hour, self.theclass(2002, 3, 2, 18, 6))
        self.assertEqual(hour + a, self.theclass(2002, 3, 2, 18, 6))
        self.assertEqual(a + 10 * hour, self.theclass(2002, 3, 3, 3, 6))
        self.assertEqual(a - hour, self.theclass(2002, 3, 2, 16, 6))
        self.assertEqual(-hour + a, self.theclass(2002, 3, 2, 16, 6))
        self.assertEqual(a - hour, a + -hour)
        self.assertEqual(a - 20 * hour, self.theclass(2002, 3, 1, 21, 6))
        self.assertEqual(a + day, self.theclass(2002, 3, 3, 17, 6))
        self.assertEqual(a - day, self.theclass(2002, 3, 1, 17, 6))
        self.assertEqual(a + week, self.theclass(2002, 3, 9, 17, 6))
        self.assertEqual(a - week, self.theclass(2002, 2, 23, 17, 6))
        self.assertEqual(a + 52 * week, self.theclass(2003, 3, 1, 17, 6))
        self.assertEqual(a - 52 * week, self.theclass(2001, 3, 3, 17, 6))
        self.assertEqual(a + week - a, week)
        self.assertEqual(a + day - a, day)
        self.assertEqual(a + hour - a, hour)
        self.assertEqual(a + millisec - a, millisec)
        self.assertEqual(a - week - a, -week)
        self.assertEqual(a - day - a, -day)
        self.assertEqual(a - hour - a, -hour)
        self.assertEqual(a - millisec - a, -millisec)
        self.assertEqual(a - (a + week), -week)
        self.assertEqual(a - (a + day), -day)
        self.assertEqual(a - (a + hour), -hour)
        self.assertEqual(a - (a + millisec), -millisec)
        self.assertEqual(a - (a - week), week)
        self.assertEqual(a - (a - day), day)
        self.assertEqual(a - (a - hour), hour)
        self.assertEqual(a - (a - millisec), millisec)
        self.assertEqual(a + (week + day + hour + millisec), self.theclass(
            2002, 3, 10, 18, 6, 0, 1000))
        self.assertEqual(a + (week + day + hour + millisec), a + week + day +
            hour + millisec)
        self.assertEqual(a - (week + day + hour + millisec), self.theclass(
            2002, 2, 22, 16, 5, 59, 999000))
        self.assertEqual(a - (week + day + hour + millisec), a - week - day -
            hour - millisec)
        for i in (1, 1.0):
            self.assertRaises(TypeError, lambda : a + i)
            self.assertRaises(TypeError, lambda : a - i)
            self.assertRaises(TypeError, lambda : i + a)
            self.assertRaises(TypeError, lambda : i - a)
        self.assertRaises(TypeError, lambda : day - a)
        self.assertRaises(TypeError, lambda : day * a)
        self.assertRaises(TypeError, lambda : a * day)
        self.assertRaises(TypeError, lambda : day // a)
        self.assertRaises(TypeError, lambda : a // day)
        self.assertRaises(TypeError, lambda : a * a)
        self.assertRaises(TypeError, lambda : a // a)
        self.assertRaises(TypeError, lambda : a + a)

    def test_pickling(self):
        args = 6, 7, 23, 20, 59, 1, 64 ** 2
        orig = self.theclass(*args)
        for pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)
        self.assertEqual(orig.__reduce__(), orig.__reduce_ex__(2))

    def test_more_pickling(self):
        a = self.theclass(2003, 2, 7, 16, 48, 37, 444116)
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            s = pickle.dumps(a, proto)
            b = pickle.loads(s)
            self.assertEqual(b.year, 2003)
            self.assertEqual(b.month, 2)
            self.assertEqual(b.day, 7)

    def test_pickling_subclass_datetime(self):
        args = 6, 7, 23, 20, 59, 1, 64 ** 2
        orig = SubclassDatetime(*args)
        for pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)

    def test_more_compare(self):
        args = [2000, 11, 29, 20, 58, 16, 999998]
        t1 = self.theclass(*args)
        t2 = self.theclass(*args)
        self.assertEqual(t1, t2)
        self.assertTrue(t1 <= t2)
        self.assertTrue(t1 >= t2)
        self.assertFalse(t1 != t2)
        self.assertFalse(t1 < t2)
        self.assertFalse(t1 > t2)
        for i in range(len(args)):
            newargs = args[:]
            newargs[i] = args[i] + 1
            t2 = self.theclass(*newargs)
            self.assertTrue(t1 < t2)
            self.assertTrue(t2 > t1)
            self.assertTrue(t1 <= t2)
            self.assertTrue(t2 >= t1)
            self.assertTrue(t1 != t2)
            self.assertTrue(t2 != t1)
            self.assertFalse(t1 == t2)
            self.assertFalse(t2 == t1)
            self.assertFalse(t1 > t2)
            self.assertFalse(t2 < t1)
            self.assertFalse(t1 >= t2)
            self.assertFalse(t2 <= t1)

    def verify_field_equality(self, expected, got):
        self.assertEqual(expected.tm_year, got.year)
        self.assertEqual(expected.tm_mon, got.month)
        self.assertEqual(expected.tm_mday, got.day)
        self.assertEqual(expected.tm_hour, got.hour)
        self.assertEqual(expected.tm_min, got.minute)
        self.assertEqual(expected.tm_sec, got.second)

    def test_fromtimestamp(self):
        import time
        ts = time.time()
        expected = time.localtime(ts)
        got = self.theclass.fromtimestamp(ts)
        self.verify_field_equality(expected, got)

    def test_utcfromtimestamp(self):
        import time
        ts = time.time()
        expected = time.gmtime(ts)
        got = self.theclass.utcfromtimestamp(ts)
        self.verify_field_equality(expected, got)

    @support.run_with_tz('EST+05EDT,M3.2.0,M11.1.0')
    def test_timestamp_naive(self):
        t = self.theclass(1970, 1, 1)
        self.assertEqual(t.timestamp(), 18000.0)
        t = self.theclass(1970, 1, 1, 1, 2, 3, 4)
        self.assertEqual(t.timestamp(), 18000.0 + 3600 + 2 * 60 + 3 + 4 * 1e-06
            )
        t0 = self.theclass(2012, 3, 11, 2, 30)
        t1 = t0.replace(fold=1)
        self.assertEqual(self.theclass.fromtimestamp(t1.timestamp()), t0 -
            timedelta(hours=1))
        self.assertEqual(self.theclass.fromtimestamp(t0.timestamp()), t1 +
            timedelta(hours=1))
        t = self.theclass(2012, 11, 4, 1, 30)
        self.assertEqual(self.theclass.fromtimestamp(t.timestamp()), t)
        for t in [self.theclass(2, 1, 1), self.theclass(9998, 12, 12)]:
            try:
                s = t.timestamp()
            except OverflowError:
                pass
            else:
                self.assertEqual(self.theclass.fromtimestamp(s), t)

    def test_timestamp_aware(self):
        t = self.theclass(1970, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(t.timestamp(), 0.0)
        t = self.theclass(1970, 1, 1, 1, 2, 3, 4, tzinfo=timezone.utc)
        self.assertEqual(t.timestamp(), 3600 + 2 * 60 + 3 + 4 * 1e-06)
        t = self.theclass(1970, 1, 1, 1, 2, 3, 4, tzinfo=timezone(timedelta
            (hours=-5), 'EST'))
        self.assertEqual(t.timestamp(), 18000 + 3600 + 2 * 60 + 3 + 4 * 1e-06)

    @support.run_with_tz('MSK-03')
    def test_microsecond_rounding(self):
        for fts in [self.theclass.fromtimestamp, self.theclass.utcfromtimestamp
            ]:
            zero = fts(0)
            self.assertEqual(zero.second, 0)
            self.assertEqual(zero.microsecond, 0)
            one = fts(1e-06)
            try:
                minus_one = fts(-1e-06)
            except OSError:
                pass
            else:
                self.assertEqual(minus_one.second, 59)
                self.assertEqual(minus_one.microsecond, 999999)
                t = fts(-1e-08)
                self.assertEqual(t, zero)
                t = fts(-9e-07)
                self.assertEqual(t, minus_one)
                t = fts(-1e-07)
                self.assertEqual(t, zero)
                t = fts(-1 / 2 ** 7)
                self.assertEqual(t.second, 59)
                self.assertEqual(t.microsecond, 992188)
            t = fts(1e-07)
            self.assertEqual(t, zero)
            t = fts(9e-07)
            self.assertEqual(t, one)
            t = fts(0.99999949)
            self.assertEqual(t.second, 0)
            self.assertEqual(t.microsecond, 999999)
            t = fts(0.9999999)
            self.assertEqual(t.second, 1)
            self.assertEqual(t.microsecond, 0)
            t = fts(1 / 2 ** 7)
            self.assertEqual(t.second, 0)
            self.assertEqual(t.microsecond, 7812)

    def test_timestamp_limits(self):
        min_dt = self.theclass.min.replace(tzinfo=timezone.utc)
        min_ts = min_dt.timestamp()
        try:
            self.assertEqual(self.theclass.fromtimestamp(min_ts, tz=
                timezone.utc), min_dt)
        except (OverflowError, OSError) as exc:
            self.skipTest(str(exc))
        max_dt = self.theclass.max.replace(tzinfo=timezone.utc, second=0,
            microsecond=0)
        max_ts = max_dt.timestamp()
        self.assertEqual(self.theclass.fromtimestamp(max_ts, tz=timezone.
            utc), max_dt)
        delta = 3600 * 24 * 400
        ts = min_ts - delta
        with self.assertRaises((ValueError, OverflowError)):
            self.theclass.fromtimestamp(ts)
        with self.assertRaises((ValueError, OverflowError)):
            self.theclass.utcfromtimestamp(ts)
        ts = max_dt.timestamp() + delta
        with self.assertRaises((ValueError, OverflowError)):
            self.theclass.fromtimestamp(ts)
        with self.assertRaises((ValueError, OverflowError)):
            self.theclass.utcfromtimestamp(ts)

    def test_insane_fromtimestamp(self):
        for insane in (-1e+200, 1e+200):
            self.assertRaises(OverflowError, self.theclass.fromtimestamp,
                insane)

    def test_insane_utcfromtimestamp(self):
        for insane in (-1e+200, 1e+200):
            self.assertRaises(OverflowError, self.theclass.utcfromtimestamp,
                insane)

    @unittest.skipIf(sys.platform == 'win32',
        "Windows doesn't accept negative timestamps")
    def test_negative_float_fromtimestamp(self):
        self.theclass.fromtimestamp(-1.05)

    @unittest.skipIf(sys.platform == 'win32',
        "Windows doesn't accept negative timestamps")
    def test_negative_float_utcfromtimestamp(self):
        d = self.theclass.utcfromtimestamp(-1.05)
        self.assertEqual(d, self.theclass(1969, 12, 31, 23, 59, 58, 950000))

    def test_utcnow(self):
        import time
        tolerance = timedelta(seconds=1)
        for dummy in range(3):
            from_now = self.theclass.utcnow()
            from_timestamp = self.theclass.utcfromtimestamp(time.time())
            if abs(from_timestamp - from_now) <= tolerance:
                break
        self.assertLessEqual(abs(from_timestamp - from_now), tolerance)

    def test_strptime(self):
        string = '2004-12-01 13:02:47.197'
        format = '%Y-%m-%d %H:%M:%S.%f'
        expected = _strptime._strptime_datetime(self.theclass, string, format)
        got = self.theclass.strptime(string, format)
        self.assertEqual(expected, got)
        self.assertIs(type(expected), self.theclass)
        self.assertIs(type(got), self.theclass)
        strptime = self.theclass.strptime
        self.assertEqual(strptime('+0002', '%z').utcoffset(), 2 * MINUTE)
        self.assertEqual(strptime('-0002', '%z').utcoffset(), -2 * MINUTE)
        for tzseconds, tzname in ((0, 'UTC'), (0, 'GMT'), (-_time.timezone,
            _time.tzname[0])):
            if tzseconds < 0:
                sign = '-'
                seconds = -tzseconds
            else:
                sign = '+'
                seconds = tzseconds
            hours, minutes = divmod(seconds // 60, 60)
            dtstr = '{}{:02d}{:02d} {}'.format(sign, hours, minutes, tzname)
            dt = strptime(dtstr, '%z %Z')
            self.assertEqual(dt.utcoffset(), timedelta(seconds=tzseconds))
            self.assertEqual(dt.tzname(), tzname)
        dtstr, fmt = '+1234 UTC', '%z %Z'
        dt = strptime(dtstr, fmt)
        self.assertEqual(dt.utcoffset(), 12 * HOUR + 34 * MINUTE)
        self.assertEqual(dt.tzname(), 'UTC')
        self.assertEqual(dt.strftime(fmt), dtstr)
        self.assertEqual(strptime('UTC', '%Z').tzinfo, None)
        with self.assertRaises(ValueError):
            strptime('-2400', '%z')
        with self.assertRaises(ValueError):
            strptime('-000', '%z')

    def test_more_timetuple(self):
        t = self.theclass(2004, 12, 31, 6, 22, 33)
        self.assertEqual(t.timetuple(), (2004, 12, 31, 6, 22, 33, 4, 366, -1))
        self.assertEqual(t.timetuple(), (t.year, t.month, t.day, t.hour, t.
            minute, t.second, t.weekday(), t.toordinal() - date(t.year, 1, 
            1).toordinal() + 1, -1))
        tt = t.timetuple()
        self.assertEqual(tt.tm_year, t.year)
        self.assertEqual(tt.tm_mon, t.month)
        self.assertEqual(tt.tm_mday, t.day)
        self.assertEqual(tt.tm_hour, t.hour)
        self.assertEqual(tt.tm_min, t.minute)
        self.assertEqual(tt.tm_sec, t.second)
        self.assertEqual(tt.tm_wday, t.weekday())
        self.assertEqual(tt.tm_yday, t.toordinal() - date(t.year, 1, 1).
            toordinal() + 1)
        self.assertEqual(tt.tm_isdst, -1)

    def test_more_strftime(self):
        t = self.theclass(2004, 12, 31, 6, 22, 33, 47)
        self.assertEqual(t.strftime('%m %d %y %f %S %M %H %j'),
            '12 31 04 000047 33 22 06 366')

    def test_extract(self):
        dt = self.theclass(2002, 3, 4, 18, 45, 3, 1234)
        self.assertEqual(dt.date(), date(2002, 3, 4))
        self.assertEqual(dt.time(), time(18, 45, 3, 1234))

    def test_combine(self):
        d = date(2002, 3, 4)
        t = time(18, 45, 3, 1234)
        expected = self.theclass(2002, 3, 4, 18, 45, 3, 1234)
        combine = self.theclass.combine
        dt = combine(d, t)
        self.assertEqual(dt, expected)
        dt = combine(time=t, date=d)
        self.assertEqual(dt, expected)
        self.assertEqual(d, dt.date())
        self.assertEqual(t, dt.time())
        self.assertEqual(dt, combine(dt.date(), dt.time()))
        self.assertRaises(TypeError, combine)
        self.assertRaises(TypeError, combine, d)
        self.assertRaises(TypeError, combine, t, d)
        self.assertRaises(TypeError, combine, d, t, 1)
        self.assertRaises(TypeError, combine, d, t, 1, 2)
        self.assertRaises(TypeError, combine, 'date', 'time')
        self.assertRaises(TypeError, combine, d, 'time')
        self.assertRaises(TypeError, combine, 'date', t)
        dt = combine(d, t, timezone.utc)
        self.assertIs(dt.tzinfo, timezone.utc)
        dt = combine(d, t, tzinfo=timezone.utc)
        self.assertIs(dt.tzinfo, timezone.utc)
        t = time()
        dt = combine(dt, t)
        self.assertEqual(dt.date(), d)
        self.assertEqual(dt.time(), t)

    def test_replace(self):
        cls = self.theclass
        args = [1, 2, 3, 4, 5, 6, 7]
        base = cls(*args)
        self.assertEqual(base, base.replace())
        i = 0
        for name, newval in (('year', 2), ('month', 3), ('day', 4), ('hour',
            5), ('minute', 6), ('second', 7), ('microsecond', 8)):
            newargs = args[:]
            newargs[i] = newval
            expected = cls(*newargs)
            got = base.replace(**{name: newval})
            self.assertEqual(expected, got)
            i += 1
        base = cls(2000, 2, 29)
        self.assertRaises(ValueError, base.replace, year=2001)

    def test_astimezone(self):
        return
        dt = self.theclass.now()
        f = FixedOffset(44, '')
        self.assertRaises(ValueError, dt.astimezone)
        self.assertRaises(TypeError, dt.astimezone, f, f)
        self.assertRaises(TypeError, dt.astimezone, dt)
        self.assertRaises(ValueError, dt.astimezone, f)
        self.assertRaises(ValueError, dt.astimezone, tz=f)


        class Bogus(tzinfo):

            def utcoffset(self, dt):
                return None

            def dst(self, dt):
                return timedelta(0)
        bog = Bogus()
        self.assertRaises(ValueError, dt.astimezone, bog)
        self.assertRaises(ValueError, dt.replace(tzinfo=bog).astimezone, f)


        class AlsoBogus(tzinfo):

            def utcoffset(self, dt):
                return timedelta(0)

            def dst(self, dt):
                return None
        alsobog = AlsoBogus()
        self.assertRaises(ValueError, dt.astimezone, alsobog)

    def test_subclass_datetime(self):


        class C(self.theclass):
            theAnswer = 42

            def __new__(cls, *args, **kws):
                temp = kws.copy()
                extra = temp.pop('extra')
                result = self.theclass.__new__(cls, *args, **temp)
                result.extra = extra
                return result

            def newmeth(self, start):
                return start + self.year + self.month + self.second
        args = 2003, 4, 14, 12, 13, 41
        dt1 = self.theclass(*args)
        dt2 = C(*args, **{'extra': 7})
        self.assertEqual(dt2.__class__, C)
        self.assertEqual(dt2.theAnswer, 42)
        self.assertEqual(dt2.extra, 7)
        self.assertEqual(dt1.toordinal(), dt2.toordinal())
        self.assertEqual(dt2.newmeth(-7), dt1.year + dt1.month + dt1.second - 7
            )


class TestSubclassDateTime(TestDateTime):
    theclass = SubclassDatetime

    @unittest.skip('not appropriate for subclasses')
    def test_roundtrip(self):
        pass


class SubclassTime(time):
    sub_var = 1


class TestTime(HarmlessMixedComparison, unittest.TestCase):
    theclass = time

    def test_basic_attributes(self):
        t = self.theclass(12, 0)
        self.assertEqual(t.hour, 12)
        self.assertEqual(t.minute, 0)
        self.assertEqual(t.second, 0)
        self.assertEqual(t.microsecond, 0)

    def test_basic_attributes_nonzero(self):
        t = self.theclass(12, 59, 59, 8000)
        self.assertEqual(t.hour, 12)
        self.assertEqual(t.minute, 59)
        self.assertEqual(t.second, 59)
        self.assertEqual(t.microsecond, 8000)

    def test_roundtrip(self):
        t = self.theclass(1, 2, 3, 4)
        s = repr(t)
        self.assertTrue(s.startswith('datetime.'))
        s = s[9:]
        t2 = eval(s)
        self.assertEqual(t, t2)
        t2 = self.theclass(t.hour, t.minute, t.second, t.microsecond)
        self.assertEqual(t, t2)

    def test_comparing(self):
        args = [1, 2, 3, 4]
        t1 = self.theclass(*args)
        t2 = self.theclass(*args)
        self.assertEqual(t1, t2)
        self.assertTrue(t1 <= t2)
        self.assertTrue(t1 >= t2)
        self.assertFalse(t1 != t2)
        self.assertFalse(t1 < t2)
        self.assertFalse(t1 > t2)
        for i in range(len(args)):
            newargs = args[:]
            newargs[i] = args[i] + 1
            t2 = self.theclass(*newargs)
            self.assertTrue(t1 < t2)
            self.assertTrue(t2 > t1)
            self.assertTrue(t1 <= t2)
            self.assertTrue(t2 >= t1)
            self.assertTrue(t1 != t2)
            self.assertTrue(t2 != t1)
            self.assertFalse(t1 == t2)
            self.assertFalse(t2 == t1)
            self.assertFalse(t1 > t2)
            self.assertFalse(t2 < t1)
            self.assertFalse(t1 >= t2)
            self.assertFalse(t2 <= t1)
        for badarg in OTHERSTUFF:
            self.assertEqual(t1 == badarg, False)
            self.assertEqual(t1 != badarg, True)
            self.assertEqual(badarg == t1, False)
            self.assertEqual(badarg != t1, True)
            self.assertRaises(TypeError, lambda : t1 <= badarg)
            self.assertRaises(TypeError, lambda : t1 < badarg)
            self.assertRaises(TypeError, lambda : t1 > badarg)
            self.assertRaises(TypeError, lambda : t1 >= badarg)
            self.assertRaises(TypeError, lambda : badarg <= t1)
            self.assertRaises(TypeError, lambda : badarg < t1)
            self.assertRaises(TypeError, lambda : badarg > t1)
            self.assertRaises(TypeError, lambda : badarg >= t1)

    def test_bad_constructor_arguments(self):
        self.theclass(0, 0)
        self.theclass(23, 0)
        self.assertRaises(ValueError, self.theclass, -1, 0)
        self.assertRaises(ValueError, self.theclass, 24, 0)
        self.theclass(23, 0)
        self.theclass(23, 59)
        self.assertRaises(ValueError, self.theclass, 23, -1)
        self.assertRaises(ValueError, self.theclass, 23, 60)
        self.theclass(23, 59, 0)
        self.theclass(23, 59, 59)
        self.assertRaises(ValueError, self.theclass, 23, 59, -1)
        self.assertRaises(ValueError, self.theclass, 23, 59, 60)
        self.theclass(23, 59, 59, 0)
        self.theclass(23, 59, 59, 999999)
        self.assertRaises(ValueError, self.theclass, 23, 59, 59, -1)
        self.assertRaises(ValueError, self.theclass, 23, 59, 59, 1000000)

    def test_hash_equality(self):
        d = self.theclass(23, 30, 17)
        e = self.theclass(23, 30, 17)
        self.assertEqual(d, e)
        self.assertEqual(hash(d), hash(e))
        dic = {d: 1}
        dic[e] = 2
        self.assertEqual(len(dic), 1)
        self.assertEqual(dic[d], 2)
        self.assertEqual(dic[e], 2)
        d = self.theclass(0, 5, 17)
        e = self.theclass(0, 5, 17)
        self.assertEqual(d, e)
        self.assertEqual(hash(d), hash(e))
        dic = {d: 1}
        dic[e] = 2
        self.assertEqual(len(dic), 1)
        self.assertEqual(dic[d], 2)
        self.assertEqual(dic[e], 2)

    def test_isoformat(self):
        t = self.theclass(4, 5, 1, 123)
        self.assertEqual(t.isoformat(), '04:05:01.000123')
        self.assertEqual(t.isoformat(), str(t))
        t = self.theclass()
        self.assertEqual(t.isoformat(), '00:00:00')
        self.assertEqual(t.isoformat(), str(t))
        t = self.theclass(microsecond=1)
        self.assertEqual(t.isoformat(), '00:00:00.000001')
        self.assertEqual(t.isoformat(), str(t))
        t = self.theclass(microsecond=10)
        self.assertEqual(t.isoformat(), '00:00:00.000010')
        self.assertEqual(t.isoformat(), str(t))
        t = self.theclass(microsecond=100)
        self.assertEqual(t.isoformat(), '00:00:00.000100')
        self.assertEqual(t.isoformat(), str(t))
        t = self.theclass(microsecond=1000)
        self.assertEqual(t.isoformat(), '00:00:00.001000')
        self.assertEqual(t.isoformat(), str(t))
        t = self.theclass(microsecond=10000)
        self.assertEqual(t.isoformat(), '00:00:00.010000')
        self.assertEqual(t.isoformat(), str(t))
        t = self.theclass(microsecond=100000)
        self.assertEqual(t.isoformat(), '00:00:00.100000')
        self.assertEqual(t.isoformat(), str(t))
        t = self.theclass(hour=12, minute=34, second=56, microsecond=123456)
        self.assertEqual(t.isoformat(timespec='hours'), '12')
        self.assertEqual(t.isoformat(timespec='minutes'), '12:34')
        self.assertEqual(t.isoformat(timespec='seconds'), '12:34:56')
        self.assertEqual(t.isoformat(timespec='milliseconds'), '12:34:56.123')
        self.assertEqual(t.isoformat(timespec='microseconds'),
            '12:34:56.123456')
        self.assertEqual(t.isoformat(timespec='auto'), '12:34:56.123456')
        self.assertRaises(ValueError, t.isoformat, timespec='monkey')
        t = self.theclass(hour=12, minute=34, second=56, microsecond=999500)
        self.assertEqual(t.isoformat(timespec='milliseconds'), '12:34:56.999')
        t = self.theclass(hour=12, minute=34, second=56, microsecond=0)
        self.assertEqual(t.isoformat(timespec='milliseconds'), '12:34:56.000')
        self.assertEqual(t.isoformat(timespec='microseconds'),
            '12:34:56.000000')
        self.assertEqual(t.isoformat(timespec='auto'), '12:34:56')

    def test_1653736(self):
        t = self.theclass(second=1)
        self.assertRaises(TypeError, t.isoformat, foo=3)

    def test_strftime(self):
        t = self.theclass(1, 2, 3, 4)
        self.assertEqual(t.strftime('%H %M %S %f'), '01 02 03 000004')
        self.assertEqual(t.strftime("'%z' '%Z'"), "'' ''")

    def test_format(self):
        t = self.theclass(1, 2, 3, 4)
        self.assertEqual(t.__format__(''), str(t))
        with self.assertRaisesRegex(TypeError, 'must be str, not int'):
            t.__format__(123)


        class A(self.theclass):

            def __str__(self):
                return 'A'
        a = A(1, 2, 3, 4)
        self.assertEqual(a.__format__(''), 'A')


        class B(self.theclass):

            def strftime(self, format_spec):
                return 'B'
        b = B(1, 2, 3, 4)
        self.assertEqual(b.__format__(''), str(t))
        for fmt in ['%H %M %S']:
            self.assertEqual(t.__format__(fmt), t.strftime(fmt))
            self.assertEqual(a.__format__(fmt), t.strftime(fmt))
            self.assertEqual(b.__format__(fmt), 'B')

    def test_str(self):
        self.assertEqual(str(self.theclass(1, 2, 3, 4)), '01:02:03.000004')
        self.assertEqual(str(self.theclass(10, 2, 3, 4000)), '10:02:03.004000')
        self.assertEqual(str(self.theclass(0, 2, 3, 400000)), '00:02:03.400000'
            )
        self.assertEqual(str(self.theclass(12, 2, 3, 0)), '12:02:03')
        self.assertEqual(str(self.theclass(23, 15, 0, 0)), '23:15:00')

    def test_repr(self):
        name = 'datetime.' + self.theclass.__name__
        self.assertEqual(repr(self.theclass(1, 2, 3, 4)), '%s(1, 2, 3, 4)' %
            name)
        self.assertEqual(repr(self.theclass(10, 2, 3, 4000)), 
            '%s(10, 2, 3, 4000)' % name)
        self.assertEqual(repr(self.theclass(0, 2, 3, 400000)), 
            '%s(0, 2, 3, 400000)' % name)
        self.assertEqual(repr(self.theclass(12, 2, 3, 0)), '%s(12, 2, 3)' %
            name)
        self.assertEqual(repr(self.theclass(23, 15, 0, 0)), '%s(23, 15)' % name
            )

    def test_resolution_info(self):
        self.assertIsInstance(self.theclass.min, self.theclass)
        self.assertIsInstance(self.theclass.max, self.theclass)
        self.assertIsInstance(self.theclass.resolution, timedelta)
        self.assertTrue(self.theclass.max > self.theclass.min)

    def test_pickling(self):
        args = 20, 59, 16, 64 ** 2
        orig = self.theclass(*args)
        for pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)
        self.assertEqual(orig.__reduce__(), orig.__reduce_ex__(2))

    def test_pickling_subclass_time(self):
        args = 20, 59, 16, 64 ** 2
        orig = SubclassTime(*args)
        for pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)

    def test_bool(self):
        cls = self.theclass
        self.assertTrue(cls(1))
        self.assertTrue(cls(0, 1))
        self.assertTrue(cls(0, 0, 1))
        self.assertTrue(cls(0, 0, 0, 1))
        self.assertTrue(cls(0))
        self.assertTrue(cls())

    def test_replace(self):
        cls = self.theclass
        args = [1, 2, 3, 4]
        base = cls(*args)
        self.assertEqual(base, base.replace())
        i = 0
        for name, newval in (('hour', 5), ('minute', 6), ('second', 7), (
            'microsecond', 8)):
            newargs = args[:]
            newargs[i] = newval
            expected = cls(*newargs)
            got = base.replace(**{name: newval})
            self.assertEqual(expected, got)
            i += 1
        base = cls(1)
        self.assertRaises(ValueError, base.replace, hour=24)
        self.assertRaises(ValueError, base.replace, minute=-1)
        self.assertRaises(ValueError, base.replace, second=100)
        self.assertRaises(ValueError, base.replace, microsecond=1000000)

    def test_subclass_time(self):


        class C(self.theclass):
            theAnswer = 42

            def __new__(cls, *args, **kws):
                temp = kws.copy()
                extra = temp.pop('extra')
                result = self.theclass.__new__(cls, *args, **temp)
                result.extra = extra
                return result

            def newmeth(self, start):
                return start + self.hour + self.second
        args = 4, 5, 6
        dt1 = self.theclass(*args)
        dt2 = C(*args, **{'extra': 7})
        self.assertEqual(dt2.__class__, C)
        self.assertEqual(dt2.theAnswer, 42)
        self.assertEqual(dt2.extra, 7)
        self.assertEqual(dt1.isoformat(), dt2.isoformat())
        self.assertEqual(dt2.newmeth(-7), dt1.hour + dt1.second - 7)

    def test_backdoor_resistance(self):
        base = '2:59.0'
        for hour_byte in (' ', '9', chr(24), 'ÿ'):
            self.assertRaises(TypeError, self.theclass, hour_byte + base[1:])
        with self.assertRaisesRegex(TypeError, '^bad tzinfo state arg$'):
            self.theclass(bytes([1] * len(base)), 'EST')


class TZInfoBase:

    def test_argument_passing(self):
        cls = self.theclass


        class introspective(tzinfo):

            def tzname(self, dt):
                return dt and 'real' or 'none'

            def utcoffset(self, dt):
                return timedelta(minutes=dt and 42 or -42)
            dst = utcoffset
        obj = cls(1, 2, 3, tzinfo=introspective())
        expected = cls is time and 'none' or 'real'
        self.assertEqual(obj.tzname(), expected)
        expected = timedelta(minutes=cls is time and -42 or 42)
        self.assertEqual(obj.utcoffset(), expected)
        self.assertEqual(obj.dst(), expected)

    def test_bad_tzinfo_classes(self):
        cls = self.theclass
        self.assertRaises(TypeError, cls, 1, 1, 1, tzinfo=12)


        class NiceTry(object):

            def __init__(self):
                pass

            def utcoffset(self, dt):
                pass
        self.assertRaises(TypeError, cls, 1, 1, 1, tzinfo=NiceTry)


        class BetterTry(tzinfo):

            def __init__(self):
                pass

            def utcoffset(self, dt):
                pass
        b = BetterTry()
        t = cls(1, 1, 1, tzinfo=b)
        self.assertIs(t.tzinfo, b)

    def test_utc_offset_out_of_bounds(self):


        class Edgy(tzinfo):

            def __init__(self, offset):
                self.offset = timedelta(minutes=offset)

            def utcoffset(self, dt):
                return self.offset
        cls = self.theclass
        for offset, legit in ((-1440, False), (-1439, True), (1439, True),
            (1440, False)):
            if cls is time:
                t = cls(1, 2, 3, tzinfo=Edgy(offset))
            elif cls is datetime:
                t = cls(6, 6, 6, 1, 2, 3, tzinfo=Edgy(offset))
            else:
                assert 0, 'impossible'
            if legit:
                aofs = abs(offset)
                h, m = divmod(aofs, 60)
                tag = '%c%02d:%02d' % (offset < 0 and '-' or '+', h, m)
                if isinstance(t, datetime):
                    t = t.timetz()
                self.assertEqual(str(t), '01:02:03' + tag)
            else:
                self.assertRaises(ValueError, str, t)

    def test_tzinfo_classes(self):
        cls = self.theclass


        class C1(tzinfo):

            def utcoffset(self, dt):
                return None

            def dst(self, dt):
                return None

            def tzname(self, dt):
                return None
        for t in (cls(1, 1, 1), cls(1, 1, 1, tzinfo=None), cls(1, 1, 1,
            tzinfo=C1())):
            self.assertIsNone(t.utcoffset())
            self.assertIsNone(t.dst())
            self.assertIsNone(t.tzname())


        class C3(tzinfo):

            def utcoffset(self, dt):
                return timedelta(minutes=-1439)

            def dst(self, dt):
                return timedelta(minutes=1439)

            def tzname(self, dt):
                return 'aname'
        t = cls(1, 1, 1, tzinfo=C3())
        self.assertEqual(t.utcoffset(), timedelta(minutes=-1439))
        self.assertEqual(t.dst(), timedelta(minutes=1439))
        self.assertEqual(t.tzname(), 'aname')


        class C4(tzinfo):

            def utcoffset(self, dt):
                return 'aname'

            def dst(self, dt):
                return 7

            def tzname(self, dt):
                return 0
        t = cls(1, 1, 1, tzinfo=C4())
        self.assertRaises(TypeError, t.utcoffset)
        self.assertRaises(TypeError, t.dst)
        self.assertRaises(TypeError, t.tzname)


        class C6(tzinfo):

            def utcoffset(self, dt):
                return timedelta(hours=-24)

            def dst(self, dt):
                return timedelta(hours=24)
        t = cls(1, 1, 1, tzinfo=C6())
        self.assertRaises(ValueError, t.utcoffset)
        self.assertRaises(ValueError, t.dst)


        class C7(tzinfo):

            def utcoffset(self, dt):
                return timedelta(microseconds=61)

            def dst(self, dt):
                return timedelta(microseconds=-81)
        t = cls(1, 1, 1, tzinfo=C7())
        self.assertRaises(ValueError, t.utcoffset)
        self.assertRaises(ValueError, t.dst)

    def test_aware_compare(self):
        cls = self.theclass


        class OperandDependentOffset(tzinfo):

            def utcoffset(self, t):
                if t.minute < 10:
                    return timedelta(minutes=t.minute)
                else:
                    return timedelta(minutes=59)
        base = cls(8, 9, 10, tzinfo=OperandDependentOffset())
        d0 = base.replace(minute=3)
        d1 = base.replace(minute=9)
        d2 = base.replace(minute=11)
        for x in (d0, d1, d2):
            for y in (d0, d1, d2):
                for op in (lt, le, gt, ge, eq, ne):
                    got = op(x, y)
                    expected = op(x.minute, y.minute)
                    self.assertEqual(got, expected)
        if cls is not time:
            d0 = base.replace(minute=3, tzinfo=OperandDependentOffset())
            d1 = base.replace(minute=9, tzinfo=OperandDependentOffset())
            d2 = base.replace(minute=11, tzinfo=OperandDependentOffset())
            for x in (d0, d1, d2):
                for y in (d0, d1, d2):
                    got = (x > y) - (x < y)
                    if (x is d0 or x is d1) and (y is d0 or y is d1):
                        expected = 0
                    elif x is y is d2:
                        expected = 0
                    elif x is d2:
                        expected = -1
                    else:
                        assert y is d2
                        expected = 1
                    self.assertEqual(got, expected)


class TestTimeTZ(TestTime, TZInfoBase, unittest.TestCase):
    theclass = time

    def test_empty(self):
        t = self.theclass()
        self.assertEqual(t.hour, 0)
        self.assertEqual(t.minute, 0)
        self.assertEqual(t.second, 0)
        self.assertEqual(t.microsecond, 0)
        self.assertIsNone(t.tzinfo)

    def test_zones(self):
        est = FixedOffset(-300, 'EST', 1)
        utc = FixedOffset(0, 'UTC', -2)
        met = FixedOffset(60, 'MET', 3)
        t1 = time(7, 47, tzinfo=est)
        t2 = time(12, 47, tzinfo=utc)
        t3 = time(13, 47, tzinfo=met)
        t4 = time(microsecond=40)
        t5 = time(microsecond=40, tzinfo=utc)
        self.assertEqual(t1.tzinfo, est)
        self.assertEqual(t2.tzinfo, utc)
        self.assertEqual(t3.tzinfo, met)
        self.assertIsNone(t4.tzinfo)
        self.assertEqual(t5.tzinfo, utc)
        self.assertEqual(t1.utcoffset(), timedelta(minutes=-300))
        self.assertEqual(t2.utcoffset(), timedelta(minutes=0))
        self.assertEqual(t3.utcoffset(), timedelta(minutes=60))
        self.assertIsNone(t4.utcoffset())
        self.assertRaises(TypeError, t1.utcoffset, 'no args')
        self.assertEqual(t1.tzname(), 'EST')
        self.assertEqual(t2.tzname(), 'UTC')
        self.assertEqual(t3.tzname(), 'MET')
        self.assertIsNone(t4.tzname())
        self.assertRaises(TypeError, t1.tzname, 'no args')
        self.assertEqual(t1.dst(), timedelta(minutes=1))
        self.assertEqual(t2.dst(), timedelta(minutes=-2))
        self.assertEqual(t3.dst(), timedelta(minutes=3))
        self.assertIsNone(t4.dst())
        self.assertRaises(TypeError, t1.dst, 'no args')
        self.assertEqual(hash(t1), hash(t2))
        self.assertEqual(hash(t1), hash(t3))
        self.assertEqual(hash(t2), hash(t3))
        self.assertEqual(t1, t2)
        self.assertEqual(t1, t3)
        self.assertEqual(t2, t3)
        self.assertNotEqual(t4, t5)
        self.assertRaises(TypeError, lambda : t4 < t5)
        self.assertRaises(TypeError, lambda : t5 < t4)
        self.assertEqual(str(t1), '07:47:00-05:00')
        self.assertEqual(str(t2), '12:47:00+00:00')
        self.assertEqual(str(t3), '13:47:00+01:00')
        self.assertEqual(str(t4), '00:00:00.000040')
        self.assertEqual(str(t5), '00:00:00.000040+00:00')
        self.assertEqual(t1.isoformat(), '07:47:00-05:00')
        self.assertEqual(t2.isoformat(), '12:47:00+00:00')
        self.assertEqual(t3.isoformat(), '13:47:00+01:00')
        self.assertEqual(t4.isoformat(), '00:00:00.000040')
        self.assertEqual(t5.isoformat(), '00:00:00.000040+00:00')
        d = 'datetime.time'
        self.assertEqual(repr(t1), d + '(7, 47, tzinfo=est)')
        self.assertEqual(repr(t2), d + '(12, 47, tzinfo=utc)')
        self.assertEqual(repr(t3), d + '(13, 47, tzinfo=met)')
        self.assertEqual(repr(t4), d + '(0, 0, 0, 40)')
        self.assertEqual(repr(t5), d + '(0, 0, 0, 40, tzinfo=utc)')
        self.assertEqual(t1.strftime('%H:%M:%S %%Z=%Z %%z=%z'),
            '07:47:00 %Z=EST %z=-0500')
        self.assertEqual(t2.strftime('%H:%M:%S %Z %z'), '12:47:00 UTC +0000')
        self.assertEqual(t3.strftime('%H:%M:%S %Z %z'), '13:47:00 MET +0100')
        yuck = FixedOffset(-1439, '%z %Z %%z%%Z')
        t1 = time(23, 59, tzinfo=yuck)
        self.assertEqual(t1.strftime("%H:%M %%Z='%Z' %%z='%z'"),
            "23:59 %Z='%z %Z %%z%%Z' %z='-2359'")


        class Badtzname(tzinfo):
            tz = 42

            def tzname(self, dt):
                return self.tz
        t = time(2, 3, 4, tzinfo=Badtzname())
        self.assertEqual(t.strftime('%H:%M:%S'), '02:03:04')
        self.assertRaises(TypeError, t.strftime, '%Z')
        if '_Fast' in str(self):
            Badtzname.tz = '\ud800'
            self.assertRaises(ValueError, t.strftime, '%Z')

    def test_hash_edge_cases(self):
        t1 = self.theclass(0, 1, 2, 3, tzinfo=FixedOffset(1439, ''))
        t2 = self.theclass(0, 0, 2, 3, tzinfo=FixedOffset(1438, ''))
        self.assertEqual(hash(t1), hash(t2))
        t1 = self.theclass(23, 58, 6, 100, tzinfo=FixedOffset(-1000, ''))
        t2 = self.theclass(23, 48, 6, 100, tzinfo=FixedOffset(-1010, ''))
        self.assertEqual(hash(t1), hash(t2))

    def test_pickling(self):
        args = 20, 59, 16, 64 ** 2
        orig = self.theclass(*args)
        for pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)
        self.assertEqual(orig.__reduce__(), orig.__reduce_ex__(2))
        tinfo = PicklableFixedOffset(-300, 'cookie')
        orig = self.theclass(5, 6, 7, tzinfo=tinfo)
        for pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)
            self.assertIsInstance(derived.tzinfo, PicklableFixedOffset)
            self.assertEqual(derived.utcoffset(), timedelta(minutes=-300))
            self.assertEqual(derived.tzname(), 'cookie')
        self.assertEqual(orig.__reduce__(), orig.__reduce_ex__(2))

    def test_more_bool(self):
        cls = self.theclass
        t = cls(0, tzinfo=FixedOffset(-300, ''))
        self.assertTrue(t)
        t = cls(5, tzinfo=FixedOffset(-300, ''))
        self.assertTrue(t)
        t = cls(5, tzinfo=FixedOffset(300, ''))
        self.assertTrue(t)
        t = cls(23, 59, tzinfo=FixedOffset(23 * 60 + 59, ''))
        self.assertTrue(t)

    def test_replace(self):
        cls = self.theclass
        z100 = FixedOffset(100, '+100')
        zm200 = FixedOffset(timedelta(minutes=-200), '-200')
        args = [1, 2, 3, 4, z100]
        base = cls(*args)
        self.assertEqual(base, base.replace())
        i = 0
        for name, newval in (('hour', 5), ('minute', 6), ('second', 7), (
            'microsecond', 8), ('tzinfo', zm200)):
            newargs = args[:]
            newargs[i] = newval
            expected = cls(*newargs)
            got = base.replace(**{name: newval})
            self.assertEqual(expected, got)
            i += 1
        self.assertEqual(base.tzname(), '+100')
        base2 = base.replace(tzinfo=None)
        self.assertIsNone(base2.tzinfo)
        self.assertIsNone(base2.tzname())
        base3 = base2.replace(tzinfo=z100)
        self.assertEqual(base, base3)
        self.assertIs(base.tzinfo, base3.tzinfo)
        base = cls(1)
        self.assertRaises(ValueError, base.replace, hour=24)
        self.assertRaises(ValueError, base.replace, minute=-1)
        self.assertRaises(ValueError, base.replace, second=100)
        self.assertRaises(ValueError, base.replace, microsecond=1000000)

    def test_mixed_compare(self):
        t1 = time(1, 2, 3)
        t2 = time(1, 2, 3)
        self.assertEqual(t1, t2)
        t2 = t2.replace(tzinfo=None)
        self.assertEqual(t1, t2)
        t2 = t2.replace(tzinfo=FixedOffset(None, ''))
        self.assertEqual(t1, t2)
        t2 = t2.replace(tzinfo=FixedOffset(0, ''))
        self.assertNotEqual(t1, t2)


        class Varies(tzinfo):

            def __init__(self):
                self.offset = timedelta(minutes=22)

            def utcoffset(self, t):
                self.offset += timedelta(minutes=1)
                return self.offset
        v = Varies()
        t1 = t2.replace(tzinfo=v)
        t2 = t2.replace(tzinfo=v)
        self.assertEqual(t1.utcoffset(), timedelta(minutes=23))
        self.assertEqual(t2.utcoffset(), timedelta(minutes=24))
        self.assertEqual(t1, t2)
        t2 = t2.replace(tzinfo=Varies())
        self.assertTrue(t1 < t2)

    def test_subclass_timetz(self):


        class C(self.theclass):
            theAnswer = 42

            def __new__(cls, *args, **kws):
                temp = kws.copy()
                extra = temp.pop('extra')
                result = self.theclass.__new__(cls, *args, **temp)
                result.extra = extra
                return result

            def newmeth(self, start):
                return start + self.hour + self.second
        args = 4, 5, 6, 500, FixedOffset(-300, 'EST', 1)
        dt1 = self.theclass(*args)
        dt2 = C(*args, **{'extra': 7})
        self.assertEqual(dt2.__class__, C)
        self.assertEqual(dt2.theAnswer, 42)
        self.assertEqual(dt2.extra, 7)
        self.assertEqual(dt1.utcoffset(), dt2.utcoffset())
        self.assertEqual(dt2.newmeth(-7), dt1.hour + dt1.second - 7)


class TestDateTimeTZ(TestDateTime, TZInfoBase, unittest.TestCase):
    theclass = datetime

    def test_trivial(self):
        dt = self.theclass(1, 2, 3, 4, 5, 6, 7)
        self.assertEqual(dt.year, 1)
        self.assertEqual(dt.month, 2)
        self.assertEqual(dt.day, 3)
        self.assertEqual(dt.hour, 4)
        self.assertEqual(dt.minute, 5)
        self.assertEqual(dt.second, 6)
        self.assertEqual(dt.microsecond, 7)
        self.assertEqual(dt.tzinfo, None)

    def test_even_more_compare(self):
        t1 = self.theclass(1, 1, 1, tzinfo=FixedOffset(1439, ''))
        t2 = self.theclass(MAXYEAR, 12, 31, 23, 59, 59, 999999, tzinfo=
            FixedOffset(-1439, ''))
        self.assertTrue(t1 < t2)
        self.assertTrue(t1 != t2)
        self.assertTrue(t2 > t1)
        self.assertEqual(t1, t1)
        self.assertEqual(t2, t2)
        t1 = self.theclass(1, 12, 31, 23, 59, tzinfo=FixedOffset(1, ''))
        t2 = self.theclass(2, 1, 1, 3, 13, tzinfo=FixedOffset(3 * 60 + 13 +
            2, ''))
        self.assertEqual(t1, t2)
        t1 = self.theclass(1, 12, 31, 23, 59, tzinfo=FixedOffset(0, ''))
        self.assertTrue(t1 > t2)
        t1 = self.theclass(1, 12, 31, 23, 59, tzinfo=FixedOffset(2, ''))
        self.assertTrue(t1 < t2)
        t1 = self.theclass(1, 12, 31, 23, 59, tzinfo=FixedOffset(1, ''),
            second=1)
        self.assertTrue(t1 > t2)
        t1 = self.theclass(1, 12, 31, 23, 59, tzinfo=FixedOffset(1, ''),
            microsecond=1)
        self.assertTrue(t1 > t2)
        t2 = self.theclass.min
        self.assertNotEqual(t1, t2)
        self.assertEqual(t2, t2)


        class Naive(tzinfo):

            def utcoffset(self, dt):
                return None
        t2 = self.theclass(5, 6, 7, tzinfo=Naive())
        self.assertNotEqual(t1, t2)
        self.assertEqual(t2, t2)
        t1 = self.theclass(5, 6, 7)
        self.assertEqual(t1, t2)


        class Bogus(tzinfo):

            def utcoffset(self, dt):
                return timedelta(minutes=1440)
        t1 = self.theclass(2, 2, 2, tzinfo=Bogus())
        t2 = self.theclass(2, 2, 2, tzinfo=FixedOffset(0, ''))
        self.assertRaises(ValueError, lambda : t1 == t2)

    def test_pickling(self):
        args = 6, 7, 23, 20, 59, 1, 64 ** 2
        orig = self.theclass(*args)
        for pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)
        self.assertEqual(orig.__reduce__(), orig.__reduce_ex__(2))
        tinfo = PicklableFixedOffset(-300, 'cookie')
        orig = self.theclass(*args, **{'tzinfo': tinfo})
        derived = self.theclass(1, 1, 1, tzinfo=FixedOffset(0, '', 0))
        for pickler, unpickler, proto in pickle_choices:
            green = pickler.dumps(orig, proto)
            derived = unpickler.loads(green)
            self.assertEqual(orig, derived)
            self.assertIsInstance(derived.tzinfo, PicklableFixedOffset)
            self.assertEqual(derived.utcoffset(), timedelta(minutes=-300))
            self.assertEqual(derived.tzname(), 'cookie')
        self.assertEqual(orig.__reduce__(), orig.__reduce_ex__(2))

    def test_extreme_hashes(self):
        t = self.theclass(1, 1, 1, tzinfo=FixedOffset(1439, ''))
        hash(t)
        t = self.theclass(MAXYEAR, 12, 31, 23, 59, 59, 999999, tzinfo=
            FixedOffset(-1439, ''))
        hash(t)
        t = self.theclass(5, 5, 5, tzinfo=FixedOffset(-1440, ''))
        self.assertRaises(ValueError, hash, t)

    def test_zones(self):
        est = FixedOffset(-300, 'EST')
        utc = FixedOffset(0, 'UTC')
        met = FixedOffset(60, 'MET')
        t1 = datetime(2002, 3, 19, 7, 47, tzinfo=est)
        t2 = datetime(2002, 3, 19, 12, 47, tzinfo=utc)
        t3 = datetime(2002, 3, 19, 13, 47, tzinfo=met)
        self.assertEqual(t1.tzinfo, est)
        self.assertEqual(t2.tzinfo, utc)
        self.assertEqual(t3.tzinfo, met)
        self.assertEqual(t1.utcoffset(), timedelta(minutes=-300))
        self.assertEqual(t2.utcoffset(), timedelta(minutes=0))
        self.assertEqual(t3.utcoffset(), timedelta(minutes=60))
        self.assertEqual(t1.tzname(), 'EST')
        self.assertEqual(t2.tzname(), 'UTC')
        self.assertEqual(t3.tzname(), 'MET')
        self.assertEqual(hash(t1), hash(t2))
        self.assertEqual(hash(t1), hash(t3))
        self.assertEqual(hash(t2), hash(t3))
        self.assertEqual(t1, t2)
        self.assertEqual(t1, t3)
        self.assertEqual(t2, t3)
        self.assertEqual(str(t1), '2002-03-19 07:47:00-05:00')
        self.assertEqual(str(t2), '2002-03-19 12:47:00+00:00')
        self.assertEqual(str(t3), '2002-03-19 13:47:00+01:00')
        d = 'datetime.datetime(2002, 3, 19, '
        self.assertEqual(repr(t1), d + '7, 47, tzinfo=est)')
        self.assertEqual(repr(t2), d + '12, 47, tzinfo=utc)')
        self.assertEqual(repr(t3), d + '13, 47, tzinfo=met)')

    def test_combine(self):
        met = FixedOffset(60, 'MET')
        d = date(2002, 3, 4)
        tz = time(18, 45, 3, 1234, tzinfo=met)
        dt = datetime.combine(d, tz)
        self.assertEqual(dt, datetime(2002, 3, 4, 18, 45, 3, 1234, tzinfo=met))

    def test_extract(self):
        met = FixedOffset(60, 'MET')
        dt = self.theclass(2002, 3, 4, 18, 45, 3, 1234, tzinfo=met)
        self.assertEqual(dt.date(), date(2002, 3, 4))
        self.assertEqual(dt.time(), time(18, 45, 3, 1234))
        self.assertEqual(dt.timetz(), time(18, 45, 3, 1234, tzinfo=met))

    def test_tz_aware_arithmetic(self):
        import random
        now = self.theclass.now()
        tz55 = FixedOffset(-330, 'west 5:30')
        timeaware = now.time().replace(tzinfo=tz55)
        nowaware = self.theclass.combine(now.date(), timeaware)
        self.assertIs(nowaware.tzinfo, tz55)
        self.assertEqual(nowaware.timetz(), timeaware)
        self.assertRaises(TypeError, lambda : now - nowaware)
        self.assertRaises(TypeError, lambda : nowaware - now)
        self.assertRaises(TypeError, lambda : now + nowaware)
        self.assertRaises(TypeError, lambda : nowaware + now)
        self.assertRaises(TypeError, lambda : nowaware + nowaware)
        self.assertEqual(now - now, timedelta(0))
        self.assertEqual(nowaware - nowaware, timedelta(0))
        delta = timedelta(weeks=1, minutes=12, microseconds=5678)
        nowawareplus = nowaware + delta
        self.assertIs(nowaware.tzinfo, tz55)
        nowawareplus2 = delta + nowaware
        self.assertIs(nowawareplus2.tzinfo, tz55)
        self.assertEqual(nowawareplus, nowawareplus2)
        diff = nowawareplus - delta
        self.assertIs(diff.tzinfo, tz55)
        self.assertEqual(nowaware, diff)
        self.assertRaises(TypeError, lambda : delta - nowawareplus)
        self.assertEqual(nowawareplus - nowaware, delta)
        tzr = FixedOffset(random.randrange(-1439, 1440), 'randomtimezone')
        nowawareplus = nowawareplus.replace(tzinfo=tzr)
        self.assertIs(nowawareplus.tzinfo, tzr)
        got = nowaware - nowawareplus
        expected = nowawareplus.utcoffset() - nowaware.utcoffset() - delta
        self.assertEqual(got, expected)
        min = self.theclass(1, 1, 1, tzinfo=FixedOffset(1439, 'min'))
        max = self.theclass(MAXYEAR, 12, 31, 23, 59, 59, 999999, tzinfo=
            FixedOffset(-1439, 'max'))
        maxdiff = max - min
        self.assertEqual(maxdiff, self.theclass.max - self.theclass.min +
            timedelta(minutes=2 * 1439))
        tza = timezone(HOUR, 'A')
        tzb = timezone(HOUR, 'B')
        delta = min.replace(tzinfo=tza) - max.replace(tzinfo=tzb)
        self.assertEqual(delta, self.theclass.min - self.theclass.max)

    def test_tzinfo_now(self):
        meth = self.theclass.now
        base = meth()
        off42 = FixedOffset(42, '42')
        another = meth(off42)
        again = meth(tz=off42)
        self.assertIs(another.tzinfo, again.tzinfo)
        self.assertEqual(another.utcoffset(), timedelta(minutes=42))
        self.assertRaises(TypeError, meth, 16)
        self.assertRaises(TypeError, meth, tzinfo=16)
        self.assertRaises(TypeError, meth, tinfo=off42)
        self.assertRaises(TypeError, meth, off42, off42)
        utc = FixedOffset(0, 'utc', 0)
        for weirdtz in [FixedOffset(timedelta(hours=15, minutes=58),
            'weirdtz', 0), timezone(timedelta(hours=15, minutes=58), 'weirdtz')
            ]:
            for dummy in range(3):
                now = datetime.now(weirdtz)
                self.assertIs(now.tzinfo, weirdtz)
                utcnow = datetime.utcnow().replace(tzinfo=utc)
                now2 = utcnow.astimezone(weirdtz)
                if abs(now - now2) < timedelta(seconds=30):
                    break
            else:
                self.fail('utcnow(), now(tz), or astimezone() may be broken')

    def test_tzinfo_fromtimestamp(self):
        import time
        meth = self.theclass.fromtimestamp
        ts = time.time()
        base = meth(ts)
        off42 = FixedOffset(42, '42')
        another = meth(ts, off42)
        again = meth(ts, tz=off42)
        self.assertIs(another.tzinfo, again.tzinfo)
        self.assertEqual(another.utcoffset(), timedelta(minutes=42))
        self.assertRaises(TypeError, meth, ts, 16)
        self.assertRaises(TypeError, meth, ts, tzinfo=16)
        self.assertRaises(TypeError, meth, ts, tinfo=off42)
        self.assertRaises(TypeError, meth, ts, off42, off42)
        self.assertRaises(TypeError, meth)
        timestamp = 1000000000
        utcdatetime = datetime.utcfromtimestamp(timestamp)
        utcoffset = timedelta(hours=-15, minutes=39)
        tz = FixedOffset(utcoffset, 'tz', 0)
        expected = utcdatetime + utcoffset
        got = datetime.fromtimestamp(timestamp, tz)
        self.assertEqual(expected, got.replace(tzinfo=None))

    def test_tzinfo_utcnow(self):
        meth = self.theclass.utcnow
        base = meth()
        off42 = FixedOffset(42, '42')
        self.assertRaises(TypeError, meth, off42)
        self.assertRaises(TypeError, meth, tzinfo=off42)

    def test_tzinfo_utcfromtimestamp(self):
        import time
        meth = self.theclass.utcfromtimestamp
        ts = time.time()
        base = meth(ts)
        off42 = FixedOffset(42, '42')
        self.assertRaises(TypeError, meth, ts, off42)
        self.assertRaises(TypeError, meth, ts, tzinfo=off42)

    def test_tzinfo_timetuple(self):


        class DST(tzinfo):

            def __init__(self, dstvalue):
                if isinstance(dstvalue, int):
                    dstvalue = timedelta(minutes=dstvalue)
                self.dstvalue = dstvalue

            def dst(self, dt):
                return self.dstvalue
        cls = self.theclass
        for dstvalue, flag in ((-33, 1), (33, 1), (0, 0), (None, -1)):
            d = cls(1, 1, 1, 10, 20, 30, 40, tzinfo=DST(dstvalue))
            t = d.timetuple()
            self.assertEqual(1, t.tm_year)
            self.assertEqual(1, t.tm_mon)
            self.assertEqual(1, t.tm_mday)
            self.assertEqual(10, t.tm_hour)
            self.assertEqual(20, t.tm_min)
            self.assertEqual(30, t.tm_sec)
            self.assertEqual(0, t.tm_wday)
            self.assertEqual(1, t.tm_yday)
            self.assertEqual(flag, t.tm_isdst)
        self.assertRaises(TypeError, cls(1, 1, 1, tzinfo=DST('x')).timetuple)
        self.assertEqual(cls(1, 1, 1, tzinfo=DST(1439)).timetuple().tm_isdst, 1
            )
        self.assertEqual(cls(1, 1, 1, tzinfo=DST(-1439)).timetuple().
            tm_isdst, 1)
        self.assertRaises(ValueError, cls(1, 1, 1, tzinfo=DST(1440)).timetuple)
        self.assertRaises(ValueError, cls(1, 1, 1, tzinfo=DST(-1440)).timetuple
            )

    def test_utctimetuple(self):


        class DST(tzinfo):

            def __init__(self, dstvalue=0):
                if isinstance(dstvalue, int):
                    dstvalue = timedelta(minutes=dstvalue)
                self.dstvalue = dstvalue

            def dst(self, dt):
                return self.dstvalue
        cls = self.theclass
        self.assertRaises(NotImplementedError, cls(1, 1, 1, tzinfo=DST(0)).
            utcoffset)


        class UOFS(DST):

            def __init__(self, uofs, dofs=None):
                DST.__init__(self, dofs)
                self.uofs = timedelta(minutes=uofs)

            def utcoffset(self, dt):
                return self.uofs
        for dstvalue in (-33, 33, 0, None):
            d = cls(1, 2, 3, 10, 20, 30, 40, tzinfo=UOFS(-53, dstvalue))
            t = d.utctimetuple()
            self.assertEqual(d.year, t.tm_year)
            self.assertEqual(d.month, t.tm_mon)
            self.assertEqual(d.day, t.tm_mday)
            self.assertEqual(11, t.tm_hour)
            self.assertEqual(13, t.tm_min)
            self.assertEqual(d.second, t.tm_sec)
            self.assertEqual(d.weekday(), t.tm_wday)
            self.assertEqual(d.toordinal() - date(1, 1, 1).toordinal() + 1,
                t.tm_yday)
            self.assertEqual(0, t.tm_isdst)
        d = cls(1, 2, 3, 10, 20, 30, 40)
        t = d.utctimetuple()
        self.assertEqual(t[:-1], d.timetuple()[:-1])
        self.assertEqual(0, t.tm_isdst)


        class NOFS(DST):

            def utcoffset(self, dt):
                return None
        d = cls(1, 2, 3, 10, 20, 30, 40, tzinfo=NOFS())
        t = d.utctimetuple()
        self.assertEqual(t[:-1], d.timetuple()[:-1])
        self.assertEqual(0, t.tm_isdst)


        class BOFS(DST):

            def utcoffset(self, dt):
                return 'EST'
        d = cls(1, 2, 3, 10, 20, 30, 40, tzinfo=BOFS())
        self.assertRaises(TypeError, d.utctimetuple)
        d = cls(2010, 11, 13, 14, 15, 16, 171819)
        for tz in [timezone.min, timezone.utc, timezone.max]:
            dtz = d.replace(tzinfo=tz)
            self.assertEqual(dtz.utctimetuple()[:-1], dtz.astimezone(
                timezone.utc).timetuple()[:-1])
        tiny = cls(MINYEAR, 1, 1, 0, 0, 37, tzinfo=UOFS(1439))
        self.assertRaises(OverflowError, tiny.utctimetuple)
        huge = cls(MAXYEAR, 12, 31, 23, 59, 37, 999999, tzinfo=UOFS(-1439))
        self.assertRaises(OverflowError, huge.utctimetuple)
        tiny = cls.min.replace(tzinfo=timezone(MINUTE))
        self.assertRaises(OverflowError, tiny.utctimetuple)
        huge = cls.max.replace(tzinfo=timezone(-MINUTE))
        self.assertRaises(OverflowError, huge.utctimetuple)

    def test_tzinfo_isoformat(self):
        zero = FixedOffset(0, '+00:00')
        plus = FixedOffset(220, '+03:40')
        minus = FixedOffset(-231, '-03:51')
        unknown = FixedOffset(None, '')
        cls = self.theclass
        datestr = '0001-02-03'
        for ofs in (None, zero, plus, minus, unknown):
            for us in (0, 987001):
                d = cls(1, 2, 3, 4, 5, 59, us, tzinfo=ofs)
                timestr = '04:05:59' + (us and '.987001' or '')
                ofsstr = ofs is not None and d.tzname() or ''
                tailstr = timestr + ofsstr
                iso = d.isoformat()
                self.assertEqual(iso, datestr + 'T' + tailstr)
                self.assertEqual(iso, d.isoformat('T'))
                self.assertEqual(d.isoformat('k'), datestr + 'k' + tailstr)
                self.assertEqual(d.isoformat('ሴ'), datestr + 'ሴ' + tailstr)
                self.assertEqual(str(d), datestr + ' ' + tailstr)

    def test_replace(self):
        cls = self.theclass
        z100 = FixedOffset(100, '+100')
        zm200 = FixedOffset(timedelta(minutes=-200), '-200')
        args = [1, 2, 3, 4, 5, 6, 7, z100]
        base = cls(*args)
        self.assertEqual(base, base.replace())
        i = 0
        for name, newval in (('year', 2), ('month', 3), ('day', 4), ('hour',
            5), ('minute', 6), ('second', 7), ('microsecond', 8), ('tzinfo',
            zm200)):
            newargs = args[:]
            newargs[i] = newval
            expected = cls(*newargs)
            got = base.replace(**{name: newval})
            self.assertEqual(expected, got)
            i += 1
        self.assertEqual(base.tzname(), '+100')
        base2 = base.replace(tzinfo=None)
        self.assertIsNone(base2.tzinfo)
        self.assertIsNone(base2.tzname())
        base3 = base2.replace(tzinfo=z100)
        self.assertEqual(base, base3)
        self.assertIs(base.tzinfo, base3.tzinfo)
        base = cls(2000, 2, 29)
        self.assertRaises(ValueError, base.replace, year=2001)

    def test_more_astimezone(self):
        fnone = FixedOffset(None, 'None')
        f44m = FixedOffset(44, '44')
        fm5h = FixedOffset(-timedelta(hours=5), 'm300')
        dt = self.theclass.now(tz=f44m)
        self.assertIs(dt.tzinfo, f44m)
        self.assertRaises(ValueError, dt.astimezone, fnone)
        x = dt.astimezone(dt.tzinfo)
        self.assertIs(x.tzinfo, f44m)
        self.assertEqual(x.date(), dt.date())
        self.assertEqual(x.time(), dt.time())
        got = dt.astimezone(fm5h)
        self.assertIs(got.tzinfo, fm5h)
        self.assertEqual(got.utcoffset(), timedelta(hours=-5))
        expected = dt - dt.utcoffset()
        expected += fm5h.utcoffset(dt)
        expected = expected.replace(tzinfo=fm5h)
        self.assertEqual(got.date(), expected.date())
        self.assertEqual(got.time(), expected.time())
        self.assertEqual(got.timetz(), expected.timetz())
        self.assertIs(got.tzinfo, expected.tzinfo)
        self.assertEqual(got, expected)

    @support.run_with_tz('UTC')
    def test_astimezone_default_utc(self):
        dt = self.theclass.now(timezone.utc)
        self.assertEqual(dt.astimezone(None), dt)
        self.assertEqual(dt.astimezone(), dt)

    @support.run_with_tz('EST+05EDT,M3.2.0,M11.1.0')
    def test_astimezone_default_eastern(self):
        dt = self.theclass(2012, 11, 4, 6, 30, tzinfo=timezone.utc)
        local = dt.astimezone()
        self.assertEqual(dt, local)
        self.assertEqual(local.strftime('%z %Z'), '-0500 EST')
        dt = self.theclass(2012, 11, 4, 5, 30, tzinfo=timezone.utc)
        local = dt.astimezone()
        self.assertEqual(dt, local)
        self.assertEqual(local.strftime('%z %Z'), '-0400 EDT')

    @support.run_with_tz('EST+05EDT,M3.2.0,M11.1.0')
    def test_astimezone_default_near_fold(self):
        u = datetime(2015, 11, 1, 5, tzinfo=timezone.utc)
        t = u.astimezone()
        s = t.astimezone()
        self.assertEqual(t.tzinfo, s.tzinfo)

    def test_aware_subtract(self):
        cls = self.theclass


        class OperandDependentOffset(tzinfo):

            def utcoffset(self, t):
                if t.minute < 10:
                    return timedelta(minutes=t.minute)
                else:
                    return timedelta(minutes=59)
        base = cls(8, 9, 10, 11, 12, 13, 14, tzinfo=OperandDependentOffset())
        d0 = base.replace(minute=3)
        d1 = base.replace(minute=9)
        d2 = base.replace(minute=11)
        for x in (d0, d1, d2):
            for y in (d0, d1, d2):
                got = x - y
                expected = timedelta(minutes=x.minute - y.minute)
                self.assertEqual(got, expected)
        base = cls(8, 9, 10, 11, 12, 13, 14)
        d0 = base.replace(minute=3, tzinfo=OperandDependentOffset())
        d1 = base.replace(minute=9, tzinfo=OperandDependentOffset())
        d2 = base.replace(minute=11, tzinfo=OperandDependentOffset())
        for x in (d0, d1, d2):
            for y in (d0, d1, d2):
                got = x - y
                if (x is d0 or x is d1) and (y is d0 or y is d1):
                    expected = timedelta(0)
                elif x is y is d2:
                    expected = timedelta(0)
                elif x is d2:
                    expected = timedelta(minutes=11 - 59 - 0)
                else:
                    assert y is d2
                    expected = timedelta(minutes=0 - (11 - 59))
                self.assertEqual(got, expected)

    def test_mixed_compare(self):
        t1 = datetime(1, 2, 3, 4, 5, 6, 7)
        t2 = datetime(1, 2, 3, 4, 5, 6, 7)
        self.assertEqual(t1, t2)
        t2 = t2.replace(tzinfo=None)
        self.assertEqual(t1, t2)
        t2 = t2.replace(tzinfo=FixedOffset(None, ''))
        self.assertEqual(t1, t2)
        t2 = t2.replace(tzinfo=FixedOffset(0, ''))
        self.assertNotEqual(t1, t2)


        class Varies(tzinfo):

            def __init__(self):
                self.offset = timedelta(minutes=22)

            def utcoffset(self, t):
                self.offset += timedelta(minutes=1)
                return self.offset
        v = Varies()
        t1 = t2.replace(tzinfo=v)
        t2 = t2.replace(tzinfo=v)
        self.assertEqual(t1.utcoffset(), timedelta(minutes=23))
        self.assertEqual(t2.utcoffset(), timedelta(minutes=24))
        self.assertEqual(t1, t2)
        t2 = t2.replace(tzinfo=Varies())
        self.assertTrue(t1 < t2)

    def test_subclass_datetimetz(self):


        class C(self.theclass):
            theAnswer = 42

            def __new__(cls, *args, **kws):
                temp = kws.copy()
                extra = temp.pop('extra')
                result = self.theclass.__new__(cls, *args, **temp)
                result.extra = extra
                return result

            def newmeth(self, start):
                return start + self.hour + self.year
        args = 2002, 12, 31, 4, 5, 6, 500, FixedOffset(-300, 'EST', 1)
        dt1 = self.theclass(*args)
        dt2 = C(*args, **{'extra': 7})
        self.assertEqual(dt2.__class__, C)
        self.assertEqual(dt2.theAnswer, 42)
        self.assertEqual(dt2.extra, 7)
        self.assertEqual(dt1.utcoffset(), dt2.utcoffset())
        self.assertEqual(dt2.newmeth(-7), dt1.hour + dt1.year - 7)


def first_sunday_on_or_after(dt):
    days_to_go = 6 - dt.weekday()
    if days_to_go:
        dt += timedelta(days_to_go)
    return dt


ZERO = timedelta(0)
MINUTE = timedelta(minutes=1)
HOUR = timedelta(hours=1)
DAY = timedelta(days=1)
DSTSTART = datetime(1, 4, 1, 2)
DSTEND = datetime(1, 10, 25, 1)


class USTimeZone(tzinfo):

    def __init__(self, hours, reprname, stdname, dstname):
        self.stdoffset = timedelta(hours=hours)
        self.reprname = reprname
        self.stdname = stdname
        self.dstname = dstname

    def __repr__(self):
        return self.reprname

    def tzname(self, dt):
        if self.dst(dt):
            return self.dstname
        else:
            return self.stdname

    def utcoffset(self, dt):
        return self.stdoffset + self.dst(dt)

    def dst(self, dt):
        if dt is None or dt.tzinfo is None:
            return ZERO
        assert dt.tzinfo is self
        start = first_sunday_on_or_after(DSTSTART.replace(year=dt.year))
        assert start.weekday() == 6 and start.month == 4 and start.day <= 7
        end = first_sunday_on_or_after(DSTEND.replace(year=dt.year))
        assert end.weekday() == 6 and end.month == 10 and end.day >= 25
        if start <= dt.replace(tzinfo=None) < end:
            return HOUR
        else:
            return ZERO


Eastern = USTimeZone(-5, 'Eastern', 'EST', 'EDT')
Central = USTimeZone(-6, 'Central', 'CST', 'CDT')
Mountain = USTimeZone(-7, 'Mountain', 'MST', 'MDT')
Pacific = USTimeZone(-8, 'Pacific', 'PST', 'PDT')
utc_real = FixedOffset(0, 'UTC', 0)
utc_fake = FixedOffset(-12 * 60, 'UTCfake', 0)


class TestTimezoneConversions(unittest.TestCase):
    dston = datetime(2002, 4, 7, 2)
    dstoff = datetime(2002, 10, 27, 1)
    theclass = datetime

    def checkinside(self, dt, tz, utc, dston, dstoff):
        self.assertEqual(dt.dst(), HOUR)
        self.assertEqual(dt.astimezone(tz), dt)
        asutc = dt.astimezone(utc)
        there_and_back = asutc.astimezone(tz)
        if dt.date() == dston.date() and dt.hour == 2:
            self.assertEqual(there_and_back + HOUR, dt)
            self.assertEqual(there_and_back.dst(), ZERO)
            self.assertEqual(there_and_back.astimezone(utc), dt.astimezone(utc)
                )
        else:
            self.assertEqual(dt, there_and_back)
        nexthour_utc = asutc + HOUR
        nexthour_tz = nexthour_utc.astimezone(tz)
        if dt.date() == dstoff.date() and dt.hour == 0:
            self.assertEqual(nexthour_tz, dt.replace(hour=1))
            nexthour_utc += HOUR
            nexthour_tz = nexthour_utc.astimezone(tz)
            self.assertEqual(nexthour_tz, dt.replace(hour=1))
        else:
            self.assertEqual(nexthour_tz - dt, HOUR)

    def checkoutside(self, dt, tz, utc):
        self.assertEqual(dt.dst(), ZERO)
        self.assertEqual(dt.astimezone(tz), dt)
        asutc = dt.astimezone(utc)
        there_and_back = asutc.astimezone(tz)
        self.assertEqual(dt, there_and_back)

    def convert_between_tz_and_utc(self, tz, utc):
        dston = self.dston.replace(tzinfo=tz)
        dstoff = self.dstoff.replace(tzinfo=tz)
        for delta in (timedelta(weeks=13), DAY, HOUR, timedelta(minutes=1),
            timedelta(microseconds=1)):
            self.checkinside(dston, tz, utc, dston, dstoff)
            for during in (dston + delta, dstoff - delta):
                self.checkinside(during, tz, utc, dston, dstoff)
            self.checkoutside(dstoff, tz, utc)
            for outside in (dston - delta, dstoff + delta):
                self.checkoutside(outside, tz, utc)

    def test_easy(self):
        self.convert_between_tz_and_utc(Eastern, utc_real)
        self.convert_between_tz_and_utc(Pacific, utc_real)
        self.convert_between_tz_and_utc(Eastern, utc_fake)
        self.convert_between_tz_and_utc(Pacific, utc_fake)
        self.convert_between_tz_and_utc(Eastern, Pacific)
        self.convert_between_tz_and_utc(Pacific, Eastern)

    def test_tricky(self):
        fourback = self.dston - timedelta(hours=4)
        ninewest = FixedOffset(-9 * 60, '-0900', 0)
        fourback = fourback.replace(tzinfo=ninewest)
        expected = self.dston.replace(hour=3)
        got = fourback.astimezone(Eastern).replace(tzinfo=None)
        self.assertEqual(expected, got)
        sixutc = self.dston.replace(hour=6, tzinfo=utc_real)
        expected = self.dston.replace(hour=1)
        got = sixutc.astimezone(Eastern).replace(tzinfo=None)
        self.assertEqual(expected, got)
        for utc in (utc_real, utc_fake):
            for tz in (Eastern, Pacific):
                first_std_hour = self.dstoff - timedelta(hours=2)
                first_std_hour -= tz.utcoffset(None)
                asutc = first_std_hour + utc.utcoffset(None)
                asutcbase = asutc.replace(tzinfo=utc)
                for tzhour in (0, 1, 1, 2):
                    expectedbase = self.dstoff.replace(hour=tzhour)
                    for minute in (0, 30, 59):
                        expected = expectedbase.replace(minute=minute)
                        asutc = asutcbase.replace(minute=minute)
                        astz = asutc.astimezone(tz)
                        self.assertEqual(astz.replace(tzinfo=None), expected)
                    asutcbase += HOUR

    def test_bogus_dst(self):


        class ok(tzinfo):

            def utcoffset(self, dt):
                return HOUR

            def dst(self, dt):
                return HOUR
        now = self.theclass.now().replace(tzinfo=utc_real)
        now.astimezone(ok())


        class notok(ok):

            def dst(self, dt):
                return None
        self.assertRaises(ValueError, now.astimezone, notok())


        class tricky_notok(ok):

            def dst(self, dt):
                if dt.year == 2000:
                    return None
                else:
                    return 10 * HOUR
        dt = self.theclass(2001, 1, 1).replace(tzinfo=utc_real)
        self.assertRaises(ValueError, dt.astimezone, tricky_notok())

    def test_fromutc(self):
        self.assertRaises(TypeError, Eastern.fromutc)
        now = datetime.utcnow().replace(tzinfo=utc_real)
        self.assertRaises(ValueError, Eastern.fromutc, now)
        now = now.replace(tzinfo=Eastern)
        enow = Eastern.fromutc(now)
        self.assertEqual(enow.tzinfo, Eastern)
        self.assertRaises(TypeError, Eastern.fromutc, now, now)
        self.assertRaises(TypeError, Eastern.fromutc, date.today())


        class FauxUSTimeZone(USTimeZone):

            def fromutc(self, dt):
                return dt + self.stdoffset
        FEastern = FauxUSTimeZone(-5, 'FEastern', 'FEST', 'FEDT')
        start = self.dston.replace(hour=4, tzinfo=Eastern)
        fstart = start.replace(tzinfo=FEastern)
        for wall in (23, 0, 1, 3, 4, 5):
            expected = start.replace(hour=wall)
            if wall == 23:
                expected -= timedelta(days=1)
            got = Eastern.fromutc(start)
            self.assertEqual(expected, got)
            expected = fstart + FEastern.stdoffset
            got = FEastern.fromutc(fstart)
            self.assertEqual(expected, got)
            got = fstart.replace(tzinfo=utc_real).astimezone(FEastern)
            self.assertEqual(expected, got)
            start += HOUR
            fstart += HOUR
        start = self.dstoff.replace(hour=4, tzinfo=Eastern)
        fstart = start.replace(tzinfo=FEastern)
        for wall in (0, 1, 1, 2, 3, 4):
            expected = start.replace(hour=wall)
            got = Eastern.fromutc(start)
            self.assertEqual(expected, got)
            expected = fstart + FEastern.stdoffset
            got = FEastern.fromutc(fstart)
            self.assertEqual(expected, got)
            got = fstart.replace(tzinfo=utc_real).astimezone(FEastern)
            self.assertEqual(expected, got)
            start += HOUR
            fstart += HOUR


class Oddballs(unittest.TestCase):

    def test_bug_1028306(self):
        as_date = date.today()
        as_datetime = datetime.combine(as_date, time())
        self.assertTrue(as_date != as_datetime)
        self.assertTrue(as_datetime != as_date)
        self.assertFalse(as_date == as_datetime)
        self.assertFalse(as_datetime == as_date)
        self.assertRaises(TypeError, lambda : as_date < as_datetime)
        self.assertRaises(TypeError, lambda : as_datetime < as_date)
        self.assertRaises(TypeError, lambda : as_date <= as_datetime)
        self.assertRaises(TypeError, lambda : as_datetime <= as_date)
        self.assertRaises(TypeError, lambda : as_date > as_datetime)
        self.assertRaises(TypeError, lambda : as_datetime > as_date)
        self.assertRaises(TypeError, lambda : as_date >= as_datetime)
        self.assertRaises(TypeError, lambda : as_datetime >= as_date)
        self.assertEqual(as_date.__eq__(as_datetime), True)
        different_day = (as_date.day + 1) % 20 + 1
        as_different = as_datetime.replace(day=different_day)
        self.assertEqual(as_date.__eq__(as_different), False)
        date_sc = SubclassDate(as_date.year, as_date.month, as_date.day)
        self.assertEqual(as_date, date_sc)
        self.assertEqual(date_sc, as_date)
        datetime_sc = SubclassDatetime(as_datetime.year, as_datetime.month,
            as_date.day, 0, 0, 0)
        self.assertEqual(as_datetime, datetime_sc)
        self.assertEqual(datetime_sc, as_datetime)

    def test_extra_attributes(self):
        for x in [date.today(), time(), datetime.utcnow(), timedelta(),
            tzinfo(), timezone(timedelta())]:
            with self.assertRaises(AttributeError):
                x.abc = 1

    def test_check_arg_types(self):


        class Number:

            def __init__(self, value):
                self.value = value

            def __int__(self):
                return self.value
        for xx in [decimal.Decimal(10), decimal.Decimal('10.9'), Number(10)]:
            self.assertEqual(datetime(10, 10, 10, 10, 10, 10, 10), datetime
                (xx, xx, xx, xx, xx, xx, xx))
        with self.assertRaisesRegex(TypeError,
            '^an integer is required \\(got type str\\)$'):
            datetime(10, 10, '10')
        f10 = Number(10.9)
        with self.assertRaisesRegex(TypeError,
            '^__int__ returned non-int \\(type float\\)$'):
            datetime(10, 10, f10)


        class Float(float):
            pass
        s10 = Float(10.9)
        with self.assertRaisesRegex(TypeError,
            '^integer argument expected, got float$'):
            datetime(10, 10, s10)
        with self.assertRaises(TypeError):
            datetime(10.0, 10, 10)
        with self.assertRaises(TypeError):
            datetime(10, 10.0, 10)
        with self.assertRaises(TypeError):
            datetime(10, 10, 10.0)
        with self.assertRaises(TypeError):
            datetime(10, 10, 10, 10.0)
        with self.assertRaises(TypeError):
            datetime(10, 10, 10, 10, 10.0)
        with self.assertRaises(TypeError):
            datetime(10, 10, 10, 10, 10, 10.0)
        with self.assertRaises(TypeError):
            datetime(10, 10, 10, 10, 10, 10, 10.0)


class tzinfo2(tzinfo):

    def fromutc(self, dt):
        """datetime in UTC -> datetime in local time."""
        if not isinstance(dt, datetime):
            raise TypeError('fromutc() requires a datetime argument')
        if dt.tzinfo is not self:
            raise ValueError('dt.tzinfo is not self')
        off0 = dt.replace(fold=0).utcoffset()
        off1 = dt.replace(fold=1).utcoffset()
        if off0 is None or off1 is None or dt.dst() is None:
            raise ValueError
        if off0 == off1:
            ldt = dt + off0
            off1 = ldt.utcoffset()
            if off0 == off1:
                return ldt
        for off in [off0, off1]:
            ldt = dt + off
            if ldt.utcoffset() == off:
                return ldt
            ldt = ldt.replace(fold=1)
            if ldt.utcoffset() == off:
                return ldt
        raise ValueError('No suitable local time found')


class USTimeZone2(tzinfo2):

    def __init__(self, hours, reprname, stdname, dstname):
        self.stdoffset = timedelta(hours=hours)
        self.reprname = reprname
        self.stdname = stdname
        self.dstname = dstname

    def __repr__(self):
        return self.reprname

    def tzname(self, dt):
        if self.dst(dt):
            return self.dstname
        else:
            return self.stdname

    def utcoffset(self, dt):
        return self.stdoffset + self.dst(dt)

    def dst(self, dt):
        if dt is None or dt.tzinfo is None:
            return ZERO
        assert dt.tzinfo is self
        start = first_sunday_on_or_after(DSTSTART.replace(year=dt.year))
        assert start.weekday() == 6 and start.month == 4 and start.day <= 7
        end = first_sunday_on_or_after(DSTEND.replace(year=dt.year))
        assert end.weekday() == 6 and end.month == 10 and end.day >= 25
        dt = dt.replace(tzinfo=None)
        if start + HOUR <= dt < end:
            return HOUR
        elif end <= dt < end + HOUR:
            return ZERO if dt.fold else HOUR
        elif start <= dt < start + HOUR:
            return HOUR if dt.fold else ZERO
        else:
            return ZERO


Eastern2 = USTimeZone2(-5, 'Eastern2', 'EST', 'EDT')
Central2 = USTimeZone2(-6, 'Central2', 'CST', 'CDT')
Mountain2 = USTimeZone2(-7, 'Mountain2', 'MST', 'MDT')
Pacific2 = USTimeZone2(-8, 'Pacific2', 'PST', 'PDT')


class Europe_Vilnius_1941(tzinfo):

    def _utc_fold(self):
        return [datetime(1941, 6, 23, 21, tzinfo=self), datetime(1941, 6, 
            23, 22, tzinfo=self)]

    def _loc_fold(self):
        return [datetime(1941, 6, 23, 23, tzinfo=self), datetime(1941, 6, 
            24, 0, tzinfo=self)]

    def utcoffset(self, dt):
        fold_start, fold_stop = self._loc_fold()
        if dt < fold_start:
            return 3 * HOUR
        if dt < fold_stop:
            return (2 if dt.fold else 3) * HOUR
        return 2 * HOUR

    def dst(self, dt):
        fold_start, fold_stop = self._loc_fold()
        if dt < fold_start:
            return 0 * HOUR
        if dt < fold_stop:
            return (1 if dt.fold else 0) * HOUR
        return 1 * HOUR

    def tzname(self, dt):
        fold_start, fold_stop = self._loc_fold()
        if dt < fold_start:
            return 'MSK'
        if dt < fold_stop:
            return ('MSK', 'CEST')[dt.fold]
        return 'CEST'

    def fromutc(self, dt):
        assert dt.fold == 0
        assert dt.tzinfo is self
        if dt.year != 1941:
            raise NotImplementedError
        fold_start, fold_stop = self._utc_fold()
        if dt < fold_start:
            return dt + 3 * HOUR
        if dt < fold_stop:
            return (dt + 2 * HOUR).replace(fold=1)
        return dt + 2 * HOUR


class TestLocalTimeDisambiguation(unittest.TestCase):

    def test_vilnius_1941_fromutc(self):
        Vilnius = Europe_Vilnius_1941()
        gdt = datetime(1941, 6, 23, 20, 59, 59, tzinfo=timezone.utc)
        ldt = gdt.astimezone(Vilnius)
        self.assertEqual(ldt.strftime('%c %Z%z'),
            'Mon Jun 23 23:59:59 1941 MSK+0300')
        self.assertEqual(ldt.fold, 0)
        self.assertFalse(ldt.dst())
        gdt = datetime(1941, 6, 23, 21, tzinfo=timezone.utc)
        ldt = gdt.astimezone(Vilnius)
        self.assertEqual(ldt.strftime('%c %Z%z'),
            'Mon Jun 23 23:00:00 1941 CEST+0200')
        self.assertEqual(ldt.fold, 1)
        self.assertTrue(ldt.dst())
        gdt = datetime(1941, 6, 23, 22, tzinfo=timezone.utc)
        ldt = gdt.astimezone(Vilnius)
        self.assertEqual(ldt.strftime('%c %Z%z'),
            'Tue Jun 24 00:00:00 1941 CEST+0200')
        self.assertEqual(ldt.fold, 0)
        self.assertTrue(ldt.dst())

    def test_vilnius_1941_toutc(self):
        Vilnius = Europe_Vilnius_1941()
        ldt = datetime(1941, 6, 23, 22, 59, 59, tzinfo=Vilnius)
        gdt = ldt.astimezone(timezone.utc)
        self.assertEqual(gdt.strftime('%c %Z'), 'Mon Jun 23 19:59:59 1941 UTC')
        ldt = datetime(1941, 6, 23, 23, 59, 59, tzinfo=Vilnius)
        gdt = ldt.astimezone(timezone.utc)
        self.assertEqual(gdt.strftime('%c %Z'), 'Mon Jun 23 20:59:59 1941 UTC')
        ldt = datetime(1941, 6, 23, 23, 59, 59, tzinfo=Vilnius, fold=1)
        gdt = ldt.astimezone(timezone.utc)
        self.assertEqual(gdt.strftime('%c %Z'), 'Mon Jun 23 21:59:59 1941 UTC')
        ldt = datetime(1941, 6, 24, 0, tzinfo=Vilnius)
        gdt = ldt.astimezone(timezone.utc)
        self.assertEqual(gdt.strftime('%c %Z'), 'Mon Jun 23 22:00:00 1941 UTC')

    def test_constructors(self):
        t = time(0, fold=1)
        dt = datetime(1, 1, 1, fold=1)
        self.assertEqual(t.fold, 1)
        self.assertEqual(dt.fold, 1)
        with self.assertRaises(TypeError):
            time(0, 0, 0, 0, None, 0)

    def test_member(self):
        dt = datetime(1, 1, 1, fold=1)
        t = dt.time()
        self.assertEqual(t.fold, 1)
        t = dt.timetz()
        self.assertEqual(t.fold, 1)

    def test_replace(self):
        t = time(0)
        dt = datetime(1, 1, 1)
        self.assertEqual(t.replace(fold=1).fold, 1)
        self.assertEqual(dt.replace(fold=1).fold, 1)
        self.assertEqual(t.replace(fold=0).fold, 0)
        self.assertEqual(dt.replace(fold=0).fold, 0)
        t = t.replace(fold=1, tzinfo=Eastern)
        dt = dt.replace(fold=1, tzinfo=Eastern)
        self.assertEqual(t.replace(tzinfo=None).fold, 1)
        self.assertEqual(dt.replace(tzinfo=None).fold, 1)
        with self.assertRaises(ValueError):
            t.replace(fold=2)
        with self.assertRaises(ValueError):
            dt.replace(fold=2)
        with self.assertRaises(TypeError):
            t.replace(1, 1, 1, None, 1)
        with self.assertRaises(TypeError):
            dt.replace(1, 1, 1, 1, 1, 1, 1, None, 1)

    def test_comparison(self):
        t = time(0)
        dt = datetime(1, 1, 1)
        self.assertEqual(t, t.replace(fold=1))
        self.assertEqual(dt, dt.replace(fold=1))

    def test_hash(self):
        t = time(0)
        dt = datetime(1, 1, 1)
        self.assertEqual(hash(t), hash(t.replace(fold=1)))
        self.assertEqual(hash(dt), hash(dt.replace(fold=1)))

    @support.run_with_tz('EST+05EDT,M3.2.0,M11.1.0')
    def test_fromtimestamp(self):
        s = 1414906200
        dt0 = datetime.fromtimestamp(s)
        dt1 = datetime.fromtimestamp(s + 3600)
        self.assertEqual(dt0.fold, 0)
        self.assertEqual(dt1.fold, 1)

    @support.run_with_tz('Australia/Lord_Howe')
    def test_fromtimestamp_lord_howe(self):
        tm = _time.localtime(1400000000.0)
        if _time.strftime('%Z%z', tm) != 'LHST+1030':
            self.skipTest(
                'Australia/Lord_Howe timezone is not supported on this platform'
                )
        s = 1428158700
        t0 = datetime.fromtimestamp(s)
        t1 = datetime.fromtimestamp(s + 1800)
        self.assertEqual(t0, t1)
        self.assertEqual(t0.fold, 0)
        self.assertEqual(t1.fold, 1)

    @support.run_with_tz('EST+05EDT,M3.2.0,M11.1.0')
    def test_timestamp(self):
        dt0 = datetime(2014, 11, 2, 1, 30)
        dt1 = dt0.replace(fold=1)
        self.assertEqual(dt0.timestamp() + 3600, dt1.timestamp())

    @support.run_with_tz('Australia/Lord_Howe')
    def test_timestamp_lord_howe(self):
        tm = _time.localtime(1400000000.0)
        if _time.strftime('%Z%z', tm) != 'LHST+1030':
            self.skipTest(
                'Australia/Lord_Howe timezone is not supported on this platform'
                )
        t = datetime(2015, 4, 5, 1, 45)
        s0 = t.replace(fold=0).timestamp()
        s1 = t.replace(fold=1).timestamp()
        self.assertEqual(s0 + 1800, s1)

    @support.run_with_tz('EST+05EDT,M3.2.0,M11.1.0')
    def test_astimezone(self):
        dt0 = datetime(2014, 11, 2, 1, 30)
        dt1 = dt0.replace(fold=1)
        adt0 = dt0.astimezone()
        adt1 = dt1.astimezone()
        self.assertEqual(adt0.tzname(), 'EDT')
        self.assertEqual(adt1.tzname(), 'EST')
        self.assertEqual(adt0 + HOUR, adt1)
        self.assertEqual(adt0.fold, 0)
        self.assertEqual(adt1.fold, 0)

    def test_pickle_fold(self):
        t = time(fold=1)
        dt = datetime(1, 1, 1, fold=1)
        for pickler, unpickler, proto in pickle_choices:
            for x in [t, dt]:
                s = pickler.dumps(x, proto)
                y = unpickler.loads(s)
                self.assertEqual(x, y)
                self.assertEqual(0 if proto < 4 else x.fold, y.fold)

    def test_repr(self):
        t = time(fold=1)
        dt = datetime(1, 1, 1, fold=1)
        self.assertEqual(repr(t), 'datetime.time(0, 0, fold=1)')
        self.assertEqual(repr(dt), 'datetime.datetime(1, 1, 1, 0, 0, fold=1)')

    def test_dst(self):
        dt_summer = datetime(2002, 10, 27, 1, tzinfo=Eastern2
            ) - timedelta.resolution
        dt_winter = datetime(2002, 10, 27, 2, tzinfo=Eastern2)
        self.assertEqual(dt_summer.dst(), HOUR)
        self.assertEqual(dt_winter.dst(), ZERO)
        self.assertEqual(dt_summer.replace(fold=1).dst(), HOUR)
        self.assertEqual(dt_winter.replace(fold=1).dst(), ZERO)
        for minute in [0, 30, 59]:
            dt = datetime(2002, 10, 27, 1, minute, tzinfo=Eastern2)
            self.assertEqual(dt.dst(), HOUR)
            self.assertEqual(dt.replace(fold=1).dst(), ZERO)
        for minute in [0, 30, 59]:
            dt = datetime(2002, 4, 7, 2, minute, tzinfo=Eastern2)
            self.assertEqual(dt.dst(), ZERO)
            self.assertEqual(dt.replace(fold=1).dst(), HOUR)

    def test_utcoffset(self):
        dt_summer = datetime(2002, 10, 27, 1, tzinfo=Eastern2
            ) - timedelta.resolution
        dt_winter = datetime(2002, 10, 27, 2, tzinfo=Eastern2)
        self.assertEqual(dt_summer.utcoffset(), -4 * HOUR)
        self.assertEqual(dt_winter.utcoffset(), -5 * HOUR)
        self.assertEqual(dt_summer.replace(fold=1).utcoffset(), -4 * HOUR)
        self.assertEqual(dt_winter.replace(fold=1).utcoffset(), -5 * HOUR)

    def test_fromutc(self):
        u_summer = datetime(2002, 10, 27, 6, tzinfo=Eastern2
            ) - timedelta.resolution
        u_winter = datetime(2002, 10, 27, 7, tzinfo=Eastern2)
        t_summer = Eastern2.fromutc(u_summer)
        t_winter = Eastern2.fromutc(u_winter)
        self.assertEqual(t_summer, u_summer - 4 * HOUR)
        self.assertEqual(t_winter, u_winter - 5 * HOUR)
        self.assertEqual(t_summer.fold, 0)
        self.assertEqual(t_winter.fold, 0)
        u = datetime(2002, 10, 27, 5, 30, tzinfo=Eastern2)
        t0 = Eastern2.fromutc(u)
        u += HOUR
        t1 = Eastern2.fromutc(u)
        self.assertEqual(t0, t1)
        self.assertEqual(t0.fold, 0)
        self.assertEqual(t1.fold, 1)
        u = datetime(2002, 10, 27, 1, 30, tzinfo=Eastern2)
        t = Eastern2.fromutc(u)
        self.assertEqual((t.day, t.hour), (26, 21))
        u = datetime(2002, 10, 27, 6, 30, tzinfo=Eastern2)
        t = Eastern2.fromutc(u)
        self.assertEqual((t.day, t.hour), (27, 1))
        u = datetime(2002, 4, 7, 2, 0, tzinfo=Eastern2)
        t = Eastern2.fromutc(u)
        self.assertEqual((t.day, t.hour), (6, 21))

    def test_mixed_compare_regular(self):
        t = datetime(2000, 1, 1, tzinfo=Eastern2)
        self.assertEqual(t, t.astimezone(timezone.utc))
        t = datetime(2000, 6, 1, tzinfo=Eastern2)
        self.assertEqual(t, t.astimezone(timezone.utc))

    def test_mixed_compare_fold(self):
        t_fold = datetime(2002, 10, 27, 1, 45, tzinfo=Eastern2)
        t_fold_utc = t_fold.astimezone(timezone.utc)
        self.assertNotEqual(t_fold, t_fold_utc)

    def test_mixed_compare_gap(self):
        t_gap = datetime(2002, 4, 7, 2, 45, tzinfo=Eastern2)
        t_gap_utc = t_gap.astimezone(timezone.utc)
        self.assertNotEqual(t_gap, t_gap_utc)

    def test_hash_aware(self):
        t = datetime(2000, 1, 1, tzinfo=Eastern2)
        self.assertEqual(hash(t), hash(t.replace(fold=1)))
        t_fold = datetime(2002, 10, 27, 1, 45, tzinfo=Eastern2)
        t_gap = datetime(2002, 4, 7, 2, 45, tzinfo=Eastern2)
        self.assertEqual(hash(t_fold), hash(t_fold.replace(fold=1)))
        self.assertEqual(hash(t_gap), hash(t_gap.replace(fold=1)))


SEC = timedelta(0, 1)


def pairs(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


class ZoneInfo(tzinfo):
    zoneroot = '/usr/share/zoneinfo'

    def __init__(self, ut, ti):
        """

        :param ut: array
            Array of transition point timestamps
        :param ti: list
            A list of (offset, isdst, abbr) tuples
        :return: None
        """
        self.ut = ut
        self.ti = ti
        self.lt = self.invert(ut, ti)

    @staticmethod
    def invert(ut, ti):
        lt = array('q', ut), array('q', ut)
        if ut:
            offset = ti[0][0] // SEC
            lt[0][0] += offset
            lt[1][0] += offset
            for i in range(1, len(ut)):
                lt[0][i] += ti[i - 1][0] // SEC
                lt[1][i] += ti[i][0] // SEC
        return lt

    @classmethod
    def fromfile(cls, fileobj):
        if fileobj.read(4).decode() != 'TZif':
            raise ValueError('not a zoneinfo file')
        fileobj.seek(32)
        counts = array('i')
        counts.fromfile(fileobj, 3)
        if sys.byteorder != 'big':
            counts.byteswap()
        ut = array('i')
        ut.fromfile(fileobj, counts[0])
        if sys.byteorder != 'big':
            ut.byteswap()
        type_indices = array('B')
        type_indices.fromfile(fileobj, counts[0])
        ttis = []
        for i in range(counts[1]):
            ttis.append(struct.unpack('>lbb', fileobj.read(6)))
        abbrs = fileobj.read(counts[2])
        for i, (gmtoff, isdst, abbrind) in enumerate(ttis):
            abbr = abbrs[abbrind:abbrs.find(0, abbrind)].decode()
            ttis[i] = timedelta(0, gmtoff), isdst, abbr
        ti = [None] * len(ut)
        for i, idx in enumerate(type_indices):
            ti[i] = ttis[idx]
        self = cls(ut, ti)
        return self

    @classmethod
    def fromname(cls, name):
        path = os.path.join(cls.zoneroot, name)
        with open(path, 'rb') as f:
            return cls.fromfile(f)
    EPOCHORDINAL = date(1970, 1, 1).toordinal()

    def fromutc(self, dt):
        """datetime in UTC -> datetime in local time."""
        if not isinstance(dt, datetime):
            raise TypeError('fromutc() requires a datetime argument')
        if dt.tzinfo is not self:
            raise ValueError('dt.tzinfo is not self')
        timestamp = (dt.toordinal() - self.EPOCHORDINAL
            ) * 86400 + dt.hour * 3600 + dt.minute * 60 + dt.second
        if timestamp < self.ut[1]:
            tti = self.ti[0]
            fold = 0
        else:
            idx = bisect.bisect_right(self.ut, timestamp)
            assert self.ut[idx - 1] <= timestamp
            assert idx == len(self.ut) or timestamp < self.ut[idx]
            tti_prev, tti = self.ti[idx - 2:idx]
            shift = tti_prev[0] - tti[0]
            fold = shift > timedelta(0, timestamp - self.ut[idx - 1])
        dt += tti[0]
        if fold:
            return dt.replace(fold=1)
        else:
            return dt

    def _find_ti(self, dt, i):
        timestamp = (dt.toordinal() - self.EPOCHORDINAL
            ) * 86400 + dt.hour * 3600 + dt.minute * 60 + dt.second
        lt = self.lt[dt.fold]
        idx = bisect.bisect_right(lt, timestamp)
        return self.ti[max(0, idx - 1)][i]

    def utcoffset(self, dt):
        return self._find_ti(dt, 0)

    def dst(self, dt):
        isdst = self._find_ti(dt, 1)
        return ZERO if isdst else HOUR

    def tzname(self, dt):
        return self._find_ti(dt, 2)

    @classmethod
    def zonenames(cls, zonedir=None):
        if zonedir is None:
            zonedir = cls.zoneroot
        zone_tab = os.path.join(zonedir, 'zone.tab')
        try:
            f = open(zone_tab)
        except OSError:
            return
        with f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    yield line.split()[2]

    @classmethod
    def stats(cls, start_year=1):
        count = gap_count = fold_count = zeros_count = 0
        min_gap = min_fold = timedelta.max
        max_gap = max_fold = ZERO
        min_gap_datetime = max_gap_datetime = datetime.min
        min_gap_zone = max_gap_zone = None
        min_fold_datetime = max_fold_datetime = datetime.min
        min_fold_zone = max_fold_zone = None
        stats_since = datetime(start_year, 1, 1)
        for zonename in cls.zonenames():
            count += 1
            tz = cls.fromname(zonename)
            for dt, shift in tz.transitions():
                if dt < stats_since:
                    continue
                if shift > ZERO:
                    gap_count += 1
                    if (shift, dt) > (max_gap, max_gap_datetime):
                        max_gap = shift
                        max_gap_zone = zonename
                        max_gap_datetime = dt
                    if (shift, datetime.max - dt) < (min_gap, datetime.max -
                        min_gap_datetime):
                        min_gap = shift
                        min_gap_zone = zonename
                        min_gap_datetime = dt
                elif shift < ZERO:
                    fold_count += 1
                    shift = -shift
                    if (shift, dt) > (max_fold, max_fold_datetime):
                        max_fold = shift
                        max_fold_zone = zonename
                        max_fold_datetime = dt
                    if (shift, datetime.max - dt) < (min_fold, datetime.max -
                        min_fold_datetime):
                        min_fold = shift
                        min_fold_zone = zonename
                        min_fold_datetime = dt
                else:
                    zeros_count += 1
        trans_counts = gap_count, fold_count, zeros_count
        print('Number of zones:       %5d' % count)
        print(
            'Number of transitions: %5d = %d (gaps) + %d (folds) + %d (zeros)'
             % ((sum(trans_counts),) + trans_counts))
        print('Min gap:         %16s at %s in %s' % (min_gap,
            min_gap_datetime, min_gap_zone))
        print('Max gap:         %16s at %s in %s' % (max_gap,
            max_gap_datetime, max_gap_zone))
        print('Min fold:        %16s at %s in %s' % (min_fold,
            min_fold_datetime, min_fold_zone))
        print('Max fold:        %16s at %s in %s' % (max_fold,
            max_fold_datetime, max_fold_zone))

    def transitions(self):
        for (_, prev_ti), (t, ti) in pairs(zip(self.ut, self.ti)):
            shift = ti[0] - prev_ti[0]
            yield datetime.utcfromtimestamp(t), shift

    def nondst_folds(self):
        """Find all folds with the same value of isdst on both sides of the transition."""
        for (_, prev_ti), (t, ti) in pairs(zip(self.ut, self.ti)):
            shift = ti[0] - prev_ti[0]
            if shift < ZERO and ti[1] == prev_ti[1]:
                yield datetime.utcfromtimestamp(t), -shift, prev_ti[2], ti[2]

    @classmethod
    def print_all_nondst_folds(cls, same_abbr=False, start_year=1):
        count = 0
        for zonename in cls.zonenames():
            tz = cls.fromname(zonename)
            for dt, shift, prev_abbr, abbr in tz.nondst_folds():
                if dt.year < start_year or same_abbr and prev_abbr != abbr:
                    continue
                count += 1
                print('%3d) %-30s %s %10s %5s -> %s' % (count, zonename, dt,
                    shift, prev_abbr, abbr))

    def folds(self):
        for t, shift in self.transitions():
            if shift < ZERO:
                yield t, -shift

    def gaps(self):
        for t, shift in self.transitions():
            if shift > ZERO:
                yield t, shift

    def zeros(self):
        for t, shift in self.transitions():
            if not shift:
                yield t


class ZoneInfoTest(unittest.TestCase):
    zonename = 'America/New_York'

    def setUp(self):
        if sys.platform == 'win32':
            self.skipTest('Skipping zoneinfo tests on Windows')
        try:
            self.tz = ZoneInfo.fromname(self.zonename)
        except FileNotFoundError as err:
            self.skipTest('Skipping %s: %s' % (self.zonename, err))

    def assertEquivDatetimes(self, a, b):
        self.assertEqual((a.replace(tzinfo=None), a.fold, id(a.tzinfo)), (b
            .replace(tzinfo=None), b.fold, id(b.tzinfo)))

    def test_folds(self):
        tz = self.tz
        for dt, shift in tz.folds():
            for x in [0 * shift, 0.5 * shift, shift - timedelta.resolution]:
                udt = dt + x
                ldt = tz.fromutc(udt.replace(tzinfo=tz))
                self.assertEqual(ldt.fold, 1)
                adt = udt.replace(tzinfo=timezone.utc).astimezone(tz)
                self.assertEquivDatetimes(adt, ldt)
                utcoffset = ldt.utcoffset()
                self.assertEqual(ldt.replace(tzinfo=None), udt + utcoffset)
                self.assertEquivDatetimes(ldt.astimezone(timezone.utc), udt
                    .replace(tzinfo=timezone.utc))
            for x in [-timedelta.resolution, shift]:
                udt = dt + x
                udt = udt.replace(tzinfo=tz)
                ldt = tz.fromutc(udt)
                self.assertEqual(ldt.fold, 0)

    def test_gaps(self):
        tz = self.tz
        for dt, shift in tz.gaps():
            for x in [0 * shift, 0.5 * shift, shift - timedelta.resolution]:
                udt = dt + x
                udt = udt.replace(tzinfo=tz)
                ldt = tz.fromutc(udt)
                self.assertEqual(ldt.fold, 0)
                adt = udt.replace(tzinfo=timezone.utc).astimezone(tz)
                self.assertEquivDatetimes(adt, ldt)
                utcoffset = ldt.utcoffset()
                self.assertEqual(ldt.replace(tzinfo=None), udt.replace(
                    tzinfo=None) + utcoffset)
                ldt = tz.fromutc(dt.replace(tzinfo=tz)) - shift + x
                self.assertLess(ldt.replace(fold=1).utcoffset(), ldt.
                    replace(fold=0).utcoffset(), 'At %s.' % ldt)
            for x in [-timedelta.resolution, shift]:
                udt = dt + x
                ldt = tz.fromutc(udt.replace(tzinfo=tz))
                self.assertEqual(ldt.fold, 0)

    def test_system_transitions(self):
        if 'Riyadh8' in self.zonename or self.zonename.startswith('right/'):
            self.skipTest('Skipping %s' % self.zonename)
        tz = self.tz
        TZ = os.environ.get('TZ')
        os.environ['TZ'] = self.zonename
        try:
            _time.tzset()
            for udt, shift in tz.transitions():
                if udt.year >= 2037:
                    break
                s0 = (udt - datetime(1970, 1, 1)) // SEC
                ss = shift // SEC
                for x in [-40 * 3600, -20 * 3600, -1, 0, ss - 1, ss + 20 * 
                    3600, ss + 40 * 3600]:
                    s = s0 + x
                    sdt = datetime.fromtimestamp(s)
                    tzdt = datetime.fromtimestamp(s, tz).replace(tzinfo=None)
                    self.assertEquivDatetimes(sdt, tzdt)
                    s1 = sdt.timestamp()
                    self.assertEqual(s, s1)
                if ss > 0:
                    dt = datetime.fromtimestamp(s0) - shift / 2
                    ts0 = dt.timestamp()
                    ts1 = dt.replace(fold=1).timestamp()
                    self.assertEqual(ts0, s0 + ss / 2)
                    self.assertEqual(ts1, s0 - ss / 2)
        finally:
            if TZ is None:
                del os.environ['TZ']
            else:
                os.environ['TZ'] = TZ
            _time.tzset()


class ZoneInfoCompleteTest(unittest.TestSuite):

    def __init__(self):
        tests = []
        if is_resource_enabled('tzdata'):
            for name in ZoneInfo.zonenames():
                Test = type('ZoneInfoTest[%s]' % name, (ZoneInfoTest,), {})
                Test.zonename = name
                for method in dir(Test):
                    if method.startswith('test_'):
                        tests.append(Test(method))
        super().__init__(tests)


class IranTest(ZoneInfoTest):
    zonename = 'Asia/Tehran'


def load_tests(loader, standard_tests, pattern):
    standard_tests.addTest(ZoneInfoCompleteTest())
    return standard_tests


if __name__ == '__main__':
    unittest.main()
