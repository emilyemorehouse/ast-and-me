from test import support
support.requires('audio')
from test.support import findfile
ossaudiodev = support.import_module('ossaudiodev')
import errno
import sys
import sunau
import time
import audioop
import unittest
try:
    from ossaudiodev import AFMT_S16_NE
except ImportError:
    if sys.byteorder == 'little':
        AFMT_S16_NE = ossaudiodev.AFMT_S16_LE
    else:
        AFMT_S16_NE = ossaudiodev.AFMT_S16_BE


def read_sound_file(path):
    with open(path, 'rb') as fp:
        au = sunau.open(fp)
        rate = au.getframerate()
        nchannels = au.getnchannels()
        encoding = au._encoding
        fp.seek(0)
        data = fp.read()
    if encoding != sunau.AUDIO_FILE_ENCODING_MULAW_8:
        raise RuntimeError('Expect .au file with 8-bit mu-law samples')
    data = audioop.ulaw2lin(data, 2)
    return data, rate, 16, nchannels


class OSSAudioDevTests(unittest.TestCase):

    def play_sound_file(self, data, rate, ssize, nchannels):
        try:
            dsp = ossaudiodev.open('w')
        except OSError as msg:
            if msg.args[0] in (errno.EACCES, errno.ENOENT, errno.ENODEV,
                errno.EBUSY):
                raise unittest.SkipTest(msg)
            raise
        dsp.bufsize()
        dsp.obufcount()
        dsp.obuffree()
        dsp.getptr()
        dsp.fileno()
        self.assertFalse(dsp.closed)
        self.assertEqual(dsp.name, '/dev/dsp')
        self.assertEqual(dsp.mode, 'w', 'bad dsp.mode: %r' % dsp.mode)
        for attr in ('closed', 'name', 'mode'):
            try:
                setattr(dsp, attr, 42)
            except (TypeError, AttributeError):
                pass
            else:
                self.fail('dsp.%s not read-only' % attr)
        expected_time = float(len(data)) / (ssize / 8) / nchannels / rate
        dsp.setparameters(AFMT_S16_NE, nchannels, rate)
        self.assertTrue(abs(expected_time - 3.51) < 0.01, expected_time)
        t1 = time.time()
        dsp.write(data)
        dsp.close()
        t2 = time.time()
        elapsed_time = t2 - t1
        percent_diff = abs(elapsed_time - expected_time) / expected_time * 100
        self.assertTrue(percent_diff <= 10.0, 
            'elapsed time (%s) > 10%% off of expected time (%s)' % (
            elapsed_time, expected_time))

    def set_parameters(self, dsp):
        config1 = ossaudiodev.AFMT_U8, 1, 8000
        config2 = AFMT_S16_NE, 2, 44100
        for config in [config1, config2]:
            fmt, channels, rate = config
            if dsp.setfmt(fmt) == fmt and dsp.channels(channels
                ) == channels and dsp.speed(rate) == rate:
                break
        else:
            raise RuntimeError(
                'unable to set audio sampling parameters: you must have really weird audio hardware'
                )
        result = dsp.setparameters(fmt, channels, rate, False)
        self.assertEqual(result, (fmt, channels, rate), 
            'setparameters%r: returned %r' % (config, result))
        result = dsp.setparameters(fmt, channels, rate, True)
        self.assertEqual(result, (fmt, channels, rate), 
            'setparameters%r: returned %r' % (config, result))

    def set_bad_parameters(self, dsp):
        fmt = AFMT_S16_NE
        rate = 44100
        channels = 2
        for config in [(fmt, 300, rate), (fmt, -5, rate), (fmt, channels, -50)
            ]:
            fmt, channels, rate = config
            result = dsp.setparameters(fmt, channels, rate, False)
            self.assertNotEqual(result, config,
                'unexpectedly got requested configuration')
            try:
                result = dsp.setparameters(fmt, channels, rate, True)
            except ossaudiodev.OSSAudioError as err:
                pass
            else:
                self.fail('expected OSSAudioError')

    def test_playback(self):
        sound_info = read_sound_file(findfile('audiotest.au'))
        self.play_sound_file(*sound_info)

    def test_set_parameters(self):
        dsp = ossaudiodev.open('w')
        try:
            self.set_parameters(dsp)
        finally:
            dsp.close()
            self.assertTrue(dsp.closed)

    def test_mixer_methods(self):
        with ossaudiodev.openmixer() as mixer:
            self.assertGreaterEqual(mixer.fileno(), 0)

    def test_with(self):
        with ossaudiodev.open('w') as dsp:
            pass
        self.assertTrue(dsp.closed)

    def test_on_closed(self):
        dsp = ossaudiodev.open('w')
        dsp.close()
        self.assertRaises(ValueError, dsp.fileno)
        self.assertRaises(ValueError, dsp.read, 1)
        self.assertRaises(ValueError, dsp.write, b'x')
        self.assertRaises(ValueError, dsp.writeall, b'x')
        self.assertRaises(ValueError, dsp.bufsize)
        self.assertRaises(ValueError, dsp.obufcount)
        self.assertRaises(ValueError, dsp.obufcount)
        self.assertRaises(ValueError, dsp.obuffree)
        self.assertRaises(ValueError, dsp.getptr)
        mixer = ossaudiodev.openmixer()
        mixer.close()
        self.assertRaises(ValueError, mixer.fileno)


def test_main():
    try:
        dsp = ossaudiodev.open('w')
    except (ossaudiodev.error, OSError) as msg:
        if msg.args[0] in (errno.EACCES, errno.ENOENT, errno.ENODEV, errno.
            EBUSY):
            raise unittest.SkipTest(msg)
        raise
    dsp.close()
    support.run_unittest(__name__)


if __name__ == '__main__':
    test_main()
