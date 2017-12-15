from test import support
import decimal
import enum
import locale
import math
import platform
import sys
import sysconfig
import time
import unittest
try:
    import threading
except ImportError:
    threading = None
try:
    import _testcapi
except ImportError:
    _testcapi = None
SIZEOF_INT = sysconfig.get_config_var('SIZEOF_INT') or 4
TIME_MAXYEAR = (1 << 8 * SIZEOF_INT - 1) - 1
TIME_MINYEAR = -TIME_MAXYEAR - 1
SEC_TO_US = 10 ** 6
US_TO_NS = 10 ** 3
MS_TO_NS = 10 ** 6
SEC_TO_NS = 10 ** 9
NS_TO_SEC = 10 ** 9


class _PyTime(enum.IntEnum):
    ROUND_FLOOR = 0
    ROUND_CEILING = 1
    ROUND_HALF_EVEN = 2


ROUNDING_MODES = (_PyTime.ROUND_FLOOR, decimal.ROUND_FLOOR), (_PyTime.
    ROUND_CEILING, decimal.ROUND_CEILING), (_PyTime.ROUND_HALF_EVEN,
    decimal.ROUND_HALF_EVEN)


class TimeTestCase(unittest.TestCase):

    def setUp(self):
        self.t = time.time()

    def test_data_attributes(self):
        time.altzone
        time.daylight
        time.timezone
        time.tzname

    def test_time(self):
        time.time()
        info = time.get_clock_info('time')
        self.assertFalse(info.monotonic)
        self.assertTrue(info.adjustable)

    def test_clock(self):
        time.clock()
        info = time.get_clock_info('clock')
        self.assertTrue(info.monotonic)
        self.assertFalse(info.adjustable)

    @unittest.skipUnless(hasattr(time, 'clock_gettime'),
        'need time.clock_gettime()')
    def test_clock_realtime(self):
        time.clock_gettime(time.CLOCK_REALTIME)

    @unittest.skipUnless(hasattr(time, 'clock_gettime'),
        'need time.clock_gettime()')
    @unittest.skipUnless(hasattr(time, 'CLOCK_MONOTONIC'),
        'need time.CLOCK_MONOTONIC')
    def test_clock_monotonic(self):
        a = time.clock_gettime(time.CLOCK_MONOTONIC)
        b = time.clock_gettime(time.CLOCK_MONOTONIC)
        self.assertLessEqual(a, b)

    @unittest.skipUnless(hasattr(time, 'clock_getres'),
        'need time.clock_getres()')
    def test_clock_getres(self):
        res = time.clock_getres(time.CLOCK_REALTIME)
        self.assertGreater(res, 0.0)
        self.assertLessEqual(res, 1.0)

    @unittest.skipUnless(hasattr(time, 'clock_settime'),
        'need time.clock_settime()')
    def test_clock_settime(self):
        t = time.clock_gettime(time.CLOCK_REALTIME)
        try:
            time.clock_settime(time.CLOCK_REALTIME, t)
        except PermissionError:
            pass
        if hasattr(time, 'CLOCK_MONOTONIC'):
            self.assertRaises(OSError, time.clock_settime, time.
                CLOCK_MONOTONIC, 0)

    def test_conversions(self):
        self.assertEqual(time.ctime(self.t), time.asctime(time.localtime(
            self.t)))
        self.assertEqual(int(time.mktime(time.localtime(self.t))), int(self.t))

    def test_sleep(self):
        self.assertRaises(ValueError, time.sleep, -2)
        self.assertRaises(ValueError, time.sleep, -1)
        time.sleep(1.2)

    def test_strftime(self):
        tt = time.gmtime(self.t)
        for directive in ('a', 'A', 'b', 'B', 'c', 'd', 'H', 'I', 'j', 'm',
            'M', 'p', 'S', 'U', 'w', 'W', 'x', 'X', 'y', 'Y', 'Z', '%'):
            format = ' %' + directive
            try:
                time.strftime(format, tt)
            except ValueError:
                self.fail('conversion specifier: %r failed.' % format)

    def _bounds_checking(self, func):
        func((1900, 0, 1, 0, 0, 0, 0, 1, -1))
        func((1900, 12, 1, 0, 0, 0, 0, 1, -1))
        self.assertRaises(ValueError, func, (1900, -1, 1, 0, 0, 0, 0, 1, -1))
        self.assertRaises(ValueError, func, (1900, 13, 1, 0, 0, 0, 0, 1, -1))
        func((1900, 1, 0, 0, 0, 0, 0, 1, -1))
        func((1900, 1, 31, 0, 0, 0, 0, 1, -1))
        self.assertRaises(ValueError, func, (1900, 1, -1, 0, 0, 0, 0, 1, -1))
        self.assertRaises(ValueError, func, (1900, 1, 32, 0, 0, 0, 0, 1, -1))
        func((1900, 1, 1, 23, 0, 0, 0, 1, -1))
        self.assertRaises(ValueError, func, (1900, 1, 1, -1, 0, 0, 0, 1, -1))
        self.assertRaises(ValueError, func, (1900, 1, 1, 24, 0, 0, 0, 1, -1))
        func((1900, 1, 1, 0, 59, 0, 0, 1, -1))
        self.assertRaises(ValueError, func, (1900, 1, 1, 0, -1, 0, 0, 1, -1))
        self.assertRaises(ValueError, func, (1900, 1, 1, 0, 60, 0, 0, 1, -1))
        self.assertRaises(ValueError, func, (1900, 1, 1, 0, 0, -1, 0, 1, -1))
        func((1900, 1, 1, 0, 0, 60, 0, 1, -1))
        func((1900, 1, 1, 0, 0, 61, 0, 1, -1))
        self.assertRaises(ValueError, func, (1900, 1, 1, 0, 0, 62, 0, 1, -1))
        self.assertEqual(func((1900, 1, 1, 0, 0, 0, -1, 1, -1)), func((1900,
            1, 1, 0, 0, 0, +6, 1, -1)))
        self.assertRaises(ValueError, func, (1900, 1, 1, 0, 0, 0, -2, 1, -1))
        func((1900, 1, 1, 0, 0, 0, 0, 0, -1))
        func((1900, 1, 1, 0, 0, 0, 0, 366, -1))
        self.assertRaises(ValueError, func, (1900, 1, 1, 0, 0, 0, 0, -1, -1))
        self.assertRaises(ValueError, func, (1900, 1, 1, 0, 0, 0, 0, 367, -1))

    def test_strftime_bounding_check(self):
        self._bounds_checking(lambda tup: time.strftime('', tup))

    def test_strftime_format_check(self):
        for x in ['', 'A', '%A', '%AA']:
            for y in range(0, 16):
                for z in ['%', 'A%', 'AA%', '%A%', 'A%A%', '%#']:
                    try:
                        time.strftime(x * y + z)
                    except ValueError:
                        pass

    def test_default_values_for_zero(self):
        expected = '2000 01 01 00 00 00 1 001'
        with support.check_warnings():
            result = time.strftime('%Y %m %d %H %M %S %w %j', (2000,) + (0,
                ) * 8)
        self.assertEqual(expected, result)

    def test_strptime(self):
        tt = time.gmtime(self.t)
        for directive in ('a', 'A', 'b', 'B', 'c', 'd', 'H', 'I', 'j', 'm',
            'M', 'p', 'S', 'U', 'w', 'W', 'x', 'X', 'y', 'Y', 'Z', '%'):
            format = '%' + directive
            strf_output = time.strftime(format, tt)
            try:
                time.strptime(strf_output, format)
            except ValueError:
                self.fail("conversion specifier %r failed with '%s' input." %
                    (format, strf_output))

    def test_strptime_bytes(self):
        self.assertRaises(TypeError, time.strptime, b'2009', '%Y')
        self.assertRaises(TypeError, time.strptime, '2009', b'%Y')

    def test_strptime_exception_context(self):
        with self.assertRaises(ValueError) as e:
            time.strptime('', '%D')
        self.assertIs(e.exception.__suppress_context__, True)
        with self.assertRaises(ValueError) as e:
            time.strptime('19', '%Y %')
        self.assertIs(e.exception.__suppress_context__, True)

    def test_asctime(self):
        time.asctime(time.gmtime(self.t))
        for bigyear in (TIME_MAXYEAR, TIME_MINYEAR):
            asc = time.asctime((bigyear, 6, 1) + (0,) * 6)
            self.assertEqual(asc[-len(str(bigyear)):], str(bigyear))
        self.assertRaises(OverflowError, time.asctime, (TIME_MAXYEAR + 1,) +
            (0,) * 8)
        self.assertRaises(OverflowError, time.asctime, (TIME_MINYEAR - 1,) +
            (0,) * 8)
        self.assertRaises(TypeError, time.asctime, 0)
        self.assertRaises(TypeError, time.asctime, ())
        self.assertRaises(TypeError, time.asctime, (0,) * 10)

    def test_asctime_bounding_check(self):
        self._bounds_checking(time.asctime)

    def test_ctime(self):
        t = time.mktime((1973, 9, 16, 1, 3, 52, 0, 0, -1))
        self.assertEqual(time.ctime(t), 'Sun Sep 16 01:03:52 1973')
        t = time.mktime((2000, 1, 1, 0, 0, 0, 0, 0, -1))
        self.assertEqual(time.ctime(t), 'Sat Jan  1 00:00:00 2000')
        for year in [-100, 100, 1000, 2000, 2050, 10000]:
            try:
                testval = time.mktime((year, 1, 10) + (0,) * 6)
            except (ValueError, OverflowError):
                pass
            else:
                self.assertEqual(time.ctime(testval)[20:], str(year))

    @unittest.skipUnless(hasattr(time, 'tzset'),
        'time module has no attribute tzset')
    def test_tzset(self):
        from os import environ
        xmas2002 = 1040774400.0
        eastern = 'EST+05EDT,M4.1.0,M10.5.0'
        victoria = 'AEST-10AEDT-11,M10.5.0,M3.5.0'
        utc = 'UTC+0'
        org_TZ = environ.get('TZ', None)
        try:
            environ['TZ'] = eastern
            time.tzset()
            environ['TZ'] = utc
            time.tzset()
            self.assertEqual(time.gmtime(xmas2002), time.localtime(xmas2002))
            self.assertEqual(time.daylight, 0)
            self.assertEqual(time.timezone, 0)
            self.assertEqual(time.localtime(xmas2002).tm_isdst, 0)
            environ['TZ'] = eastern
            time.tzset()
            self.assertNotEqual(time.gmtime(xmas2002), time.localtime(xmas2002)
                )
            self.assertEqual(time.tzname, ('EST', 'EDT'))
            self.assertEqual(len(time.tzname), 2)
            self.assertEqual(time.daylight, 1)
            self.assertEqual(time.timezone, 18000)
            self.assertEqual(time.altzone, 14400)
            self.assertEqual(time.localtime(xmas2002).tm_isdst, 0)
            self.assertEqual(len(time.tzname), 2)
            environ['TZ'] = victoria
            time.tzset()
            self.assertNotEqual(time.gmtime(xmas2002), time.localtime(xmas2002)
                )
            self.assertIn(time.tzname[0], 'AESTEST', time.tzname[0])
            self.assertTrue(time.tzname[1] in ('AEDT', 'EDT'), str(time.
                tzname[1]))
            self.assertEqual(len(time.tzname), 2)
            self.assertEqual(time.daylight, 1)
            self.assertEqual(time.timezone, -36000)
            self.assertEqual(time.altzone, -39600)
            self.assertEqual(time.localtime(xmas2002).tm_isdst, 1)
        finally:
            if org_TZ is not None:
                environ['TZ'] = org_TZ
            elif 'TZ' in environ:
                del environ['TZ']
            time.tzset()

    def test_insane_timestamps(self):
        for func in (time.ctime, time.gmtime, time.localtime):
            for unreasonable in (-1e+200, 1e+200):
                self.assertRaises(OverflowError, func, unreasonable)

    def test_ctime_without_arg(self):
        time.ctime()
        time.ctime(None)

    def test_gmtime_without_arg(self):
        gt0 = time.gmtime()
        gt1 = time.gmtime(None)
        t0 = time.mktime(gt0)
        t1 = time.mktime(gt1)
        self.assertAlmostEqual(t1, t0, delta=0.2)

    def test_localtime_without_arg(self):
        lt0 = time.localtime()
        lt1 = time.localtime(None)
        t0 = time.mktime(lt0)
        t1 = time.mktime(lt1)
        self.assertAlmostEqual(t1, t0, delta=0.2)

    def test_mktime(self):
        for t in (-2, -1, 0, 1):
            if sys.platform.startswith('aix') and t == -1:
                continue
            try:
                tt = time.localtime(t)
            except (OverflowError, OSError):
                pass
            else:
                self.assertEqual(time.mktime(tt), t)

    @unittest.skipUnless(platform.libc_ver()[0] != 'glibc',
        'disabled because of a bug in glibc. Issue #13309')
    def test_mktime_error(self):
        tt = time.gmtime(self.t)
        tzname = time.strftime('%Z', tt)
        self.assertNotEqual(tzname, 'LMT')
        try:
            time.mktime((-1, 1, 1, 0, 0, 0, -1, -1, -1))
        except OverflowError:
            pass
        self.assertEqual(time.strftime('%Z', tt), tzname)

    @unittest.skipUnless(hasattr(time, 'monotonic'), 'need time.monotonic')
    def test_monotonic(self):
        times = [time.monotonic() for n in range(100)]
        t1 = times[0]
        for t2 in times[1:]:
            self.assertGreaterEqual(t2, t1, 'times=%s' % times)
            t1 = t2
        t1 = time.monotonic()
        time.sleep(0.5)
        t2 = time.monotonic()
        dt = t2 - t1
        self.assertGreater(t2, t1)
        self.assertTrue(0.45 <= dt <= 1.0, dt)
        info = time.get_clock_info('monotonic')
        self.assertTrue(info.monotonic)
        self.assertFalse(info.adjustable)

    def test_perf_counter(self):
        time.perf_counter()

    def test_process_time(self):
        start = time.process_time()
        time.sleep(0.1)
        stop = time.process_time()
        self.assertLess(stop - start, 0.02)
        info = time.get_clock_info('process_time')
        self.assertTrue(info.monotonic)
        self.assertFalse(info.adjustable)

    @unittest.skipUnless(hasattr(time, 'monotonic'), 'need time.monotonic')
    @unittest.skipUnless(hasattr(time, 'clock_settime'),
        'need time.clock_settime')
    def test_monotonic_settime(self):
        t1 = time.monotonic()
        realtime = time.clock_gettime(time.CLOCK_REALTIME)
        try:
            time.clock_settime(time.CLOCK_REALTIME, realtime - 3600)
        except PermissionError as err:
            self.skipTest(err)
        t2 = time.monotonic()
        time.clock_settime(time.CLOCK_REALTIME, realtime)
        self.assertGreaterEqual(t2, t1)

    def test_localtime_failure(self):
        invalid_time_t = None
        for time_t in (-1, 2 ** 30, 2 ** 33, 2 ** 60):
            try:
                time.localtime(time_t)
            except OverflowError:
                self.skipTest('need 64-bit time_t')
            except OSError:
                invalid_time_t = time_t
                break
        if invalid_time_t is None:
            self.skipTest('unable to find an invalid time_t value')
        self.assertRaises(OSError, time.localtime, invalid_time_t)
        self.assertRaises(OSError, time.ctime, invalid_time_t)

    def test_get_clock_info(self):
        clocks = ['clock', 'perf_counter', 'process_time', 'time']
        if hasattr(time, 'monotonic'):
            clocks.append('monotonic')
        for name in clocks:
            info = time.get_clock_info(name)
            self.assertIsInstance(info.implementation, str)
            self.assertNotEqual(info.implementation, '')
            self.assertIsInstance(info.monotonic, bool)
            self.assertIsInstance(info.resolution, float)
            self.assertGreater(info.resolution, 0.0)
            self.assertLessEqual(info.resolution, 1.0)
            self.assertIsInstance(info.adjustable, bool)
        self.assertRaises(ValueError, time.get_clock_info, 'xxx')


class TestLocale(unittest.TestCase):

    def setUp(self):
        self.oldloc = locale.setlocale(locale.LC_ALL)

    def tearDown(self):
        locale.setlocale(locale.LC_ALL, self.oldloc)

    def test_bug_3061(self):
        try:
            tmp = locale.setlocale(locale.LC_ALL, 'fr_FR')
        except locale.Error:
            self.skipTest('could not set locale.LC_ALL to fr_FR')
        time.strftime('%B', (2009, 2, 1, 0, 0, 0, 0, 0, 0))


class _TestAsctimeYear:
    _format = '%d'

    def yearstr(self, y):
        return time.asctime((y,) + (0,) * 8).split()[-1]

    def test_large_year(self):
        self.assertEqual(self.yearstr(12345), '12345')
        self.assertEqual(self.yearstr(123456789), '123456789')


class _TestStrftimeYear:
    if time.strftime('%Y', (1,) + (0,) * 8) == '0001':
        _format = '%04d'
    else:
        _format = '%d'

    def yearstr(self, y):
        return time.strftime('%Y', (y,) + (0,) * 8)

    def test_4dyear(self):
        if self._format == '%04d':
            self.test_year('%04d')
        else:

            def year4d(y):
                return time.strftime('%4Y', (y,) + (0,) * 8)
            self.test_year('%04d', func=year4d)

    def skip_if_not_supported(y):
        msg = 'strftime() is limited to [1; 9999] with Visual Studio'
        try:
            time.strftime('%Y', (y,) + (0,) * 8)
        except ValueError:
            cond = False
        else:
            cond = True
        return unittest.skipUnless(cond, msg)

    @skip_if_not_supported(10000)
    def test_large_year(self):
        return super().test_large_year()

    @skip_if_not_supported(0)
    def test_negative(self):
        return super().test_negative()
    del skip_if_not_supported


class _Test4dYear:
    _format = '%d'

    def test_year(self, fmt=None, func=None):
        fmt = fmt or self._format
        func = func or self.yearstr
        self.assertEqual(func(1), fmt % 1)
        self.assertEqual(func(68), fmt % 68)
        self.assertEqual(func(69), fmt % 69)
        self.assertEqual(func(99), fmt % 99)
        self.assertEqual(func(999), fmt % 999)
        self.assertEqual(func(9999), fmt % 9999)

    def test_large_year(self):
        self.assertEqual(self.yearstr(12345), '12345')
        self.assertEqual(self.yearstr(123456789), '123456789')
        self.assertEqual(self.yearstr(TIME_MAXYEAR), str(TIME_MAXYEAR))
        self.assertRaises(OverflowError, self.yearstr, TIME_MAXYEAR + 1)

    def test_negative(self):
        self.assertEqual(self.yearstr(-1), self._format % -1)
        self.assertEqual(self.yearstr(-1234), '-1234')
        self.assertEqual(self.yearstr(-123456), '-123456')
        self.assertEqual(self.yearstr(-123456789), str(-123456789))
        self.assertEqual(self.yearstr(-1234567890), str(-1234567890))
        self.assertEqual(self.yearstr(TIME_MINYEAR + 1900), str(
            TIME_MINYEAR + 1900))
        self.yearstr(TIME_MINYEAR)
        self.assertRaises(OverflowError, self.yearstr, TIME_MINYEAR - 1)


class TestAsctime4dyear(_TestAsctimeYear, _Test4dYear, unittest.TestCase):
    pass


class TestStrftime4dyear(_TestStrftimeYear, _Test4dYear, unittest.TestCase):
    pass


class TestPytime(unittest.TestCase):

    @unittest.skipUnless(time._STRUCT_TM_ITEMS == 11, 'needs tm_zone support')
    def test_localtime_timezone(self):
        lt = time.localtime()
        self.assertTrue(hasattr(lt, 'tm_gmtoff'))
        self.assertTrue(hasattr(lt, 'tm_zone'))
        if lt.tm_gmtoff is None:
            self.assertTrue(not hasattr(time, 'timezone'))
        else:
            self.assertEqual(lt.tm_gmtoff, -[time.timezone, time.altzone][
                lt.tm_isdst])
        if lt.tm_zone is None:
            self.assertTrue(not hasattr(time, 'tzname'))
        else:
            self.assertEqual(lt.tm_zone, time.tzname[lt.tm_isdst])
        t = time.mktime(lt)
        t9 = time.mktime(lt[:9])
        self.assertEqual(t, t9)
        new_lt = time.localtime(t)
        new_lt9 = time.localtime(t9)
        self.assertEqual(new_lt, lt)
        self.assertEqual(new_lt.tm_gmtoff, lt.tm_gmtoff)
        self.assertEqual(new_lt.tm_zone, lt.tm_zone)
        self.assertEqual(new_lt9, lt)
        self.assertEqual(new_lt.tm_gmtoff, lt.tm_gmtoff)
        self.assertEqual(new_lt9.tm_zone, lt.tm_zone)

    @unittest.skipUnless(time._STRUCT_TM_ITEMS == 11, 'needs tm_zone support')
    def test_strptime_timezone(self):
        t = time.strptime('UTC', '%Z')
        self.assertEqual(t.tm_zone, 'UTC')
        t = time.strptime('+0500', '%z')
        self.assertEqual(t.tm_gmtoff, 5 * 3600)

    @unittest.skipUnless(time._STRUCT_TM_ITEMS == 11, 'needs tm_zone support')
    def test_short_times(self):
        import pickle
        st = (
            b'ctime\nstruct_time\np0\n((I2007\nI8\nI11\nI1\nI24\nI49\nI5\nI223\nI1\ntp1\n(dp2\ntp3\nRp4\n.'
            )
        lt = pickle.loads(st)
        self.assertIs(lt.tm_gmtoff, None)
        self.assertIs(lt.tm_zone, None)


@unittest.skipIf(_testcapi is None, 'need the _testcapi module')
class CPyTimeTestCase:
    """
    Base class to test the C _PyTime_t API.
    """
    OVERFLOW_SECONDS = None

    def setUp(self):
        from _testcapi import SIZEOF_TIME_T
        bits = SIZEOF_TIME_T * 8 - 1
        self.time_t_min = -2 ** bits
        self.time_t_max = 2 ** bits - 1

    def time_t_filter(self, seconds):
        return self.time_t_min <= seconds <= self.time_t_max

    def _rounding_values(self, use_float):
        """Build timestamps used to test rounding."""
        units = [1, US_TO_NS, MS_TO_NS, SEC_TO_NS]
        if use_float:
            units.append(0.001)
        values = (1, 2, 5, 7, 123, 456, 1234, 9, 99, 999, 9999, 99999, 
            999999, 499, 500, 501, 1499, 1500, 1501, 2500, 3500, 4500)
        ns_timestamps = [0]
        for unit in units:
            for value in values:
                ns = value * unit
                ns_timestamps.extend((-ns, ns))
        for pow2 in (0, 5, 10, 15, 22, 23, 24, 30, 33):
            ns = 2 ** pow2 * SEC_TO_NS
            ns_timestamps.extend((-ns - 1, -ns, -ns + 1, ns - 1, ns, ns + 1))
        for seconds in (_testcapi.INT_MIN, _testcapi.INT_MAX):
            ns_timestamps.append(seconds * SEC_TO_NS)
        if use_float:
            for pow2 in (3, 7, 10, 15):
                ns = 2.0 ** -pow2
                ns_timestamps.extend((-ns, ns))
        ns = 2 ** 63 // SEC_TO_NS * SEC_TO_NS
        ns_timestamps.extend((-ns, ns))
        return ns_timestamps

    def _check_rounding(self, pytime_converter, expected_func, use_float,
        unit_to_sec, value_filter=None):

        def convert_values(ns_timestamps):
            if use_float:
                unit_to_ns = SEC_TO_NS / float(unit_to_sec)
                values = [(ns / unit_to_ns) for ns in ns_timestamps]
            else:
                unit_to_ns = SEC_TO_NS // unit_to_sec
                values = [(ns // unit_to_ns) for ns in ns_timestamps]
            if value_filter:
                values = filter(value_filter, values)
            return sorted(set(values))
        ns_timestamps = self._rounding_values(use_float)
        valid_values = convert_values(ns_timestamps)
        for time_rnd, decimal_rnd in ROUNDING_MODES:
            context = decimal.getcontext()
            context.rounding = decimal_rnd
            for value in valid_values:
                debug_info = {'value': value, 'rounding': decimal_rnd}
                try:
                    result = pytime_converter(value, time_rnd)
                    expected = expected_func(value)
                except Exception as exc:
                    self.fail('Error on timestamp conversion: %s' % debug_info)
                self.assertEqual(result, expected, debug_info)
        ns = self.OVERFLOW_SECONDS * SEC_TO_NS
        ns_timestamps = -ns, ns
        overflow_values = convert_values(ns_timestamps)
        for time_rnd, _ in ROUNDING_MODES:
            for value in overflow_values:
                debug_info = {'value': value, 'rounding': time_rnd}
                with self.assertRaises(OverflowError, msg=debug_info):
                    pytime_converter(value, time_rnd)

    def check_int_rounding(self, pytime_converter, expected_func,
        unit_to_sec=1, value_filter=None):
        self._check_rounding(pytime_converter, expected_func, False,
            unit_to_sec, value_filter)

    def check_float_rounding(self, pytime_converter, expected_func,
        unit_to_sec=1, value_filter=None):
        self._check_rounding(pytime_converter, expected_func, True,
            unit_to_sec, value_filter)

    def decimal_round(self, x):
        d = decimal.Decimal(x)
        d = d.quantize(1)
        return int(d)


class TestCPyTime(CPyTimeTestCase, unittest.TestCase):
    """
    Test the C _PyTime_t API.
    """
    OVERFLOW_SECONDS = math.ceil((2 ** 63 + 1) / SEC_TO_NS)

    def test_FromSeconds(self):
        from _testcapi import PyTime_FromSeconds

        def c_int_filter(secs):
            return _testcapi.INT_MIN <= secs <= _testcapi.INT_MAX
        self.check_int_rounding(lambda secs, rnd: PyTime_FromSeconds(secs),
            lambda secs: secs * SEC_TO_NS, value_filter=c_int_filter)

    def test_FromSecondsObject(self):
        from _testcapi import PyTime_FromSecondsObject
        self.check_int_rounding(PyTime_FromSecondsObject, lambda secs: secs *
            SEC_TO_NS)
        self.check_float_rounding(PyTime_FromSecondsObject, lambda ns: self
            .decimal_round(ns * SEC_TO_NS))

    def test_AsSecondsDouble(self):
        from _testcapi import PyTime_AsSecondsDouble

        def float_converter(ns):
            if abs(ns) % SEC_TO_NS == 0:
                return float(ns // SEC_TO_NS)
            else:
                return float(ns) / SEC_TO_NS
        self.check_int_rounding(lambda ns, rnd: PyTime_AsSecondsDouble(ns),
            float_converter, NS_TO_SEC)

    def create_decimal_converter(self, denominator):
        denom = decimal.Decimal(denominator)

        def converter(value):
            d = decimal.Decimal(value) / denom
            return self.decimal_round(d)
        return converter

    def test_AsTimeval(self):
        from _testcapi import PyTime_AsTimeval
        us_converter = self.create_decimal_converter(US_TO_NS)

        def timeval_converter(ns):
            us = us_converter(ns)
            return divmod(us, SEC_TO_US)
        if sys.platform == 'win32':
            from _testcapi import LONG_MIN, LONG_MAX

            def seconds_filter(secs):
                return LONG_MIN <= secs <= LONG_MAX
        else:
            seconds_filter = self.time_t_filter
        self.check_int_rounding(PyTime_AsTimeval, timeval_converter,
            NS_TO_SEC, value_filter=seconds_filter)

    @unittest.skipUnless(hasattr(_testcapi, 'PyTime_AsTimespec'),
        'need _testcapi.PyTime_AsTimespec')
    def test_AsTimespec(self):
        from _testcapi import PyTime_AsTimespec

        def timespec_converter(ns):
            return divmod(ns, SEC_TO_NS)
        self.check_int_rounding(lambda ns, rnd: PyTime_AsTimespec(ns),
            timespec_converter, NS_TO_SEC, value_filter=self.time_t_filter)

    def test_AsMilliseconds(self):
        from _testcapi import PyTime_AsMilliseconds
        self.check_int_rounding(PyTime_AsMilliseconds, self.
            create_decimal_converter(MS_TO_NS), NS_TO_SEC)

    def test_AsMicroseconds(self):
        from _testcapi import PyTime_AsMicroseconds
        self.check_int_rounding(PyTime_AsMicroseconds, self.
            create_decimal_converter(US_TO_NS), NS_TO_SEC)


class TestOldPyTime(CPyTimeTestCase, unittest.TestCase):
    """
    Test the old C _PyTime_t API: _PyTime_ObjectToXXX() functions.
    """
    OVERFLOW_SECONDS = 2 ** 64

    def test_object_to_time_t(self):
        from _testcapi import pytime_object_to_time_t
        self.check_int_rounding(pytime_object_to_time_t, lambda secs: secs,
            value_filter=self.time_t_filter)
        self.check_float_rounding(pytime_object_to_time_t, self.
            decimal_round, value_filter=self.time_t_filter)

    def create_converter(self, sec_to_unit):

        def converter(secs):
            floatpart, intpart = math.modf(secs)
            intpart = int(intpart)
            floatpart *= sec_to_unit
            floatpart = self.decimal_round(floatpart)
            if floatpart < 0:
                floatpart += sec_to_unit
                intpart -= 1
            elif floatpart >= sec_to_unit:
                floatpart -= sec_to_unit
                intpart += 1
            return intpart, floatpart
        return converter

    def test_object_to_timeval(self):
        from _testcapi import pytime_object_to_timeval
        self.check_int_rounding(pytime_object_to_timeval, lambda secs: (
            secs, 0), value_filter=self.time_t_filter)
        self.check_float_rounding(pytime_object_to_timeval, self.
            create_converter(SEC_TO_US), value_filter=self.time_t_filter)

    def test_object_to_timespec(self):
        from _testcapi import pytime_object_to_timespec
        self.check_int_rounding(pytime_object_to_timespec, lambda secs: (
            secs, 0), value_filter=self.time_t_filter)
        self.check_float_rounding(pytime_object_to_timespec, self.
            create_converter(SEC_TO_NS), value_filter=self.time_t_filter)


if __name__ == '__main__':
    unittest.main()
