import random
import unittest
import re
import sys
import test.support
if getattr(sys, 'float_repr_style', '') != 'short':
    raise unittest.SkipTest(
        'correctly-rounded string->float conversions not available on this system'
        )
strtod_parser = re.compile(
    """    # A numeric string consists of:
    (?P<sign>[-+])?          # an optional sign, followed by
    (?=\\d|\\.\\d)              # a number with at least one digit
    (?P<int>\\d*)             # having a (possibly empty) integer part
    (?:\\.(?P<frac>\\d*))?     # followed by an optional fractional part
    (?:E(?P<exp>[-+]?\\d+))?  # and an optional exponent
    \\Z
"""
    , re.VERBOSE | re.IGNORECASE).match


def strtod(s, mant_dig=53, min_exp=-1021, max_exp=1024):
    """Convert a finite decimal string to a hex string representing an
    IEEE 754 binary64 float.  Return 'inf' or '-inf' on overflow.
    This function makes no use of floating-point arithmetic at any
    stage."""
    m = strtod_parser(s)
    if m is None:
        raise ValueError('invalid numeric string')
    fraction = m.group('frac') or ''
    intpart = int(m.group('int') + fraction)
    exp = int(m.group('exp') or '0') - len(fraction)
    negative = m.group('sign') == '-'
    a, b = intpart * 10 ** max(exp, 0), 10 ** max(0, -exp)
    if not a:
        return '-0x0.0p+0' if negative else '0x0.0p+0'
    d = a.bit_length() - b.bit_length()
    d += (a >> d if d >= 0 else a << -d) >= b
    e = max(d, min_exp) - mant_dig
    a, b = a << max(-e, 0), b << max(e, 0)
    q, r = divmod(a, b)
    if 2 * r > b or 2 * r == b and q & 1:
        q += 1
        if q.bit_length() == mant_dig + 1:
            q //= 2
            e += 1
    assert q.bit_length() <= mant_dig and e >= min_exp - mant_dig
    assert q.bit_length() == mant_dig or e == min_exp - mant_dig
    if e + q.bit_length() > max_exp:
        return '-inf' if negative else 'inf'
    if not q:
        return '-0x0.0p+0' if negative else '0x0.0p+0'
    hexdigs = 1 + (mant_dig - 2) // 4
    shift = 3 - (mant_dig - 2) % 4
    q, e = q << shift, e - shift
    return '{}0x{:x}.{:0{}x}p{:+d}'.format('-' if negative else '', q // 16 **
        hexdigs, q % 16 ** hexdigs, hexdigs, e + 4 * hexdigs)


TEST_SIZE = 10


class StrtodTests(unittest.TestCase):

    def check_strtod(self, s):
        """Compare the result of Python's builtin correctly rounded
        string->float conversion (using float) to a pure Python
        correctly rounded string->float implementation.  Fail if the
        two methods give different results."""
        try:
            fs = float(s)
        except OverflowError:
            got = '-inf' if s[0] == '-' else 'inf'
        except MemoryError:
            got = 'memory error'
        else:
            got = fs.hex()
        expected = strtod(s)
        self.assertEqual(expected, got,
            'Incorrectly rounded str->float conversion for {}: expected {}, got {}'
            .format(s, expected, got))

    def test_short_halfway_cases(self):
        for k in (0, 5, 10, 15, 20):
            upper = -(-2 ** 54 // 5 ** k)
            lower = -(-2 ** 53 // 5 ** k)
            if lower % 2 == 0:
                lower += 1
            for i in range(TEST_SIZE):
                n, e = random.randrange(lower, upper, 2), k
                while n % 5 == 0:
                    n, e = n // 5, e + 1
                assert n % 10 in (1, 3, 7, 9)
                digits, exponent = n, e
                while digits < 10 ** 20:
                    s = '{}e{}'.format(digits, exponent)
                    self.check_strtod(s)
                    s = '{}e{}'.format(digits * 10 ** 40, exponent - 40)
                    self.check_strtod(s)
                    digits *= 2
                digits, exponent = n, e
                while digits < 10 ** 20:
                    s = '{}e{}'.format(digits, exponent)
                    self.check_strtod(s)
                    s = '{}e{}'.format(digits * 10 ** 40, exponent - 40)
                    self.check_strtod(s)
                    digits *= 5
                    exponent -= 1

    def test_halfway_cases(self):
        for i in range(100 * TEST_SIZE):
            bits = random.randrange(2047 * 2 ** 52)
            e, m = divmod(bits, 2 ** 52)
            if e:
                m, e = m + 2 ** 52, e - 1
            e -= 1074
            m, e = 2 * m + 1, e - 1
            if e >= 0:
                digits = m << e
                exponent = 0
            else:
                digits = m * 5 ** -e
                exponent = e
            s = '{}e{}'.format(digits, exponent)
            self.check_strtod(s)

    def test_boundaries(self):
        boundaries = [(10000000000000000000, -19, 1110), (
            17976931348623159077, 289, 1995), (22250738585072013831, -327, 
            4941), (0, -327, 4941)]
        for n, e, u in boundaries:
            for j in range(1000):
                digits = n + random.randrange(-3 * u, 3 * u)
                exponent = e
                s = '{}e{}'.format(digits, exponent)
                self.check_strtod(s)
                n *= 10
                u *= 10
                e -= 1

    def test_underflow_boundary(self):
        for exponent in range(-400, -320):
            base = 10 ** -exponent // 2 ** 1075
            for j in range(TEST_SIZE):
                digits = base + random.randrange(-1000, 1000)
                s = '{}e{}'.format(digits, exponent)
                self.check_strtod(s)

    def test_bigcomp(self):
        for ndigs in (5, 10, 14, 15, 16, 17, 18, 19, 20, 40, 41, 50):
            dig10 = 10 ** ndigs
            for i in range(10 * TEST_SIZE):
                digits = random.randrange(dig10)
                exponent = random.randrange(-400, 400)
                s = '{}e{}'.format(digits, exponent)
                self.check_strtod(s)

    def test_parsing(self):
        digits = '000000123456789'
        signs = '+', '-', ''
        for i in range(1000):
            for j in range(TEST_SIZE):
                s = random.choice(signs)
                intpart_len = random.randrange(5)
                s += ''.join(random.choice(digits) for _ in range(intpart_len))
                if random.choice([True, False]):
                    s += '.'
                    fracpart_len = random.randrange(5)
                    s += ''.join(random.choice(digits) for _ in range(
                        fracpart_len))
                else:
                    fracpart_len = 0
                if random.choice([True, False]):
                    s += random.choice(['e', 'E'])
                    s += random.choice(signs)
                    exponent_len = random.randrange(1, 4)
                    s += ''.join(random.choice(digits) for _ in range(
                        exponent_len))
                if intpart_len + fracpart_len:
                    self.check_strtod(s)
                else:
                    try:
                        float(s)
                    except ValueError:
                        pass
                    else:
                        assert False, 'expected ValueError'

    @test.support.bigmemtest(size=test.support._2G + 10, memuse=3, dry_run=
        False)
    def test_oversized_digit_strings(self, maxsize):
        s = '1.' + '1' * maxsize
        with self.assertRaises(ValueError):
            float(s)
        del s
        s = '0.' + '0' * maxsize + '1'
        with self.assertRaises(ValueError):
            float(s)
        del s

    def test_large_exponents(self):

        def positive_exp(n):
            """ Long string with value 1.0 and exponent n"""
            return '0.{}1e+{}'.format('0' * (n - 1), n)

        def negative_exp(n):
            """ Long string with value 1.0 and exponent -n"""
            return '1{}e-{}'.format('0' * n, n)
        self.assertEqual(float(positive_exp(10000)), 1.0)
        self.assertEqual(float(positive_exp(20000)), 1.0)
        self.assertEqual(float(positive_exp(30000)), 1.0)
        self.assertEqual(float(negative_exp(10000)), 1.0)
        self.assertEqual(float(negative_exp(20000)), 1.0)
        self.assertEqual(float(negative_exp(30000)), 1.0)

    def test_particular(self):
        test_strings = ['2183167012312112312312.23538020374420446192e-370',
            '12579816049008305546974391768996369464963024663104e-357',
            '17489628565202117263145367596028389348922981857013e-357',
            '18487398785991994634182916638542680759613590482273e-357',
            '32002864200581033134358724675198044527469366773928e-358',
            '94393431193180696942841837085033647913224148539854e-358',
            '73608278998966969345824653500136787876436005957953e-358',
            '64774478836417299491718435234611299336288082136054e-358',
            '13704940134126574534878641876947980878824688451169e-357',
            '46697445774047060960624497964425416610480524760471e-358',
            '28639097178261763178489759107321392745108491825303e-311',
            '1.00000000000000001e44',
            '1.0000000000000000100000000000000000000001e44',
            '99999999999999994487665465554760717039532578546e-47',
            '9654371763336549317990355136719971183455700459144696213413350821416312194420007991306908470147322020121018368e0'
            ,
            '104308485241983990666713401708072175773165034278685682646111762292409330928739751702404658197872319129036519947435319418387839758990478549477777586673075945844895981012024387992135617064532141489278815239849108105951619997829153633535314849999674266169258928940692239684771590065027025835804863585454872499320500023126142553932654370362024104462255244034053203998964360882487378334860197725139151265590832887433736189468858614521708567646743455601905935595381852723723645799866672558576993978025033590728687206296379801363024094048327273913079612469982585674824156000783167963081616214710691759864332339239688734656548790656486646106983450809073750535624894296242072010195710276073042036425579852459556183541199012652571123898996574563824424330960027873516082763671875e-1075'
            , '247032822920623295e-341',
            '99037485700245683102805043437346965248029601286431e-373',
            '99617639833743863161109961162881027406769510558457e-373',
            '98852915025769345295749278351563179840130565591462e-372',
            '99059944827693569659153042769690930905148015876788e-373',
            '98914979205069368270421829889078356254059760327101e-372',
            '1000000000000000000000000000000000000000e-16',
            '10000000000000000000000000000000000000000e-17',
            '991633793189150720000000000000000000000000000000000000000e-33',
            '4106250198039490000000000000000000000000000000000000000e-38',
            '10.900000000000000012345678912345678912345',
            '11651287494059419563861790709256988151903479322938522856916519154189084656466977171489691608488398792047332126810029685763620092606534076968286334920536334924763766067178320990794927368304039797998410780646182269333271282839761794603623958163297658510063352026077076106072540390412314438457161207373275477458821194440646557259102208197382844892733860255628785183174541939743301249188486945446244053689504749943655197464973191717009938776287102040358299419343976193341216682148401588363162253931420379903449798213003874174172790742957567330246138038659650118748200625752770984217933648838167281879845022933912352785884444833681591202045229462491699354638895656152216187535257259042082360747878839946016222830869374205287663441403533948204085390898399055004119873046875e-1075'
            ,
            '5254406533529552661096610603582028195612589849649138922565278497589560452182570597137658742514361936194432482059988700016338656575174473559922258529459120166686600002102838072098506622244175047522649953606315120077538558010753730576321577387528008403025962370502479105305382500086822727836607781816280407336531214924364088126680234780012085291903592543223403975751852488447885154107229587846409265285440430901153525136408849880173424692750069991045196209464308187671479664954854065777039726878381767789934729895619590000470366389383963331466851379030183764964083197053338684769252973171365139701890736933147103189912528110505014483268752328506004517760913030437151571912928276140468769502257147431182910347804663250851413437345649151934269945872064326973371182115272789687312946393533547747886024677951678751174816604738791256853675690543663283782215866825e-1180'
            , '2602129298404963083833853479113577253105939995688e2',
            '260212929840496308383385347911357725310593999568896e0',
            '26021292984049630838338534791135772531059399956889601e-2',
            '260212929840496308383385347911357725310593999568895e0',
            '260212929840496308383385347911357725310593999568897e0',
            '260212929840496308383385347911357725310593999568996e0',
            '260212929840496308383385347911357725310593999568866e0',
            '9007199254740992.00',
            '179769313486231580793728971405303415079934132710037826936173778980444968292764750946649017977587207096330286416692887910946555547851940402630657488671505820681908902000708383676273854845817711531764475730270069855571366959622842914819860834936475292719074168444365510704342711559699508093042880177904174497792'
            ,
            '179769313486231580793728971405303415079934132710037826936173778980444968292764750946649017977587207096330286416692887910946555547851940402630657488671505820681908902000708383676273854845817711531764475730270069855571366959622842914819860834936475292719074168444365510704342711559699508093042880177904174497791.999'
            ,
            '179769313486231580793728971405303415079934132710037826936173778980444968292764750946649017977587207096330286416692887910946555547851940402630657488671505820681908902000708383676273854845817711531764475730270069855571366959622842914819860834936475292719074168444365510704342711559699508093042880177904174497792.001'
            , '999999999999999944488848768742172978818416595458984375e-54',
            '9999999999999999444888487687421729788184165954589843749999999e-54'
            ,
            '9999999999999999444888487687421729788184165954589843750000001e-54'
            ,
            '0.000000000000000000000000000000000000000010000000000000000057612911342378542997169042119121403423543508714776317814976295686899169228986994124665807319451982237978882039897143840789794921875'
            ]
        for s in test_strings:
            self.check_strtod(s)


if __name__ == '__main__':
    unittest.main()
