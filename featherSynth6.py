# A synthio-based implementation of FeatherSynth.
# Uses an I2S amplifier instead of simple PWM.
#
# version 6, in dev
#
# TODO: Use "detuning" to get a fatter sound?
#
# For the Featheremin project - https://github.com/RobCranfill/featheremin
#
import audiobusio
import audiomixer
import board
import microcontroller
import random
import synthio
import time
import ulab.numpy as numpy


SYNTH_RATE    = 22050
SAMPLE_RATE   = 28000
SAMPLE_SIZE   =   512
SAMPLE_VOLUME = 32000
BUFFER_SIZE   =  4 * 1024 # up from 2K; necessary?

# A do-nothing 'BlockInput' for the LFOs
LFO_NONE = 1.0


FAT_DETUNE = 0.005  # how much to detune, 0.7% here
 

class FeatherSynth:
    '''
        Our new synthio-based synth.

        Can change waveform, TODO: envelope, and add tremolo or vibrato.

        TODO: Triangle wave? saw up vs saw down? (it is a rising sawtooth now.)

    '''
    def __init__(self, stereo, i2s_bit_clock, i2s_word_select, i2s_data) -> None:

        if stereo:
            self._channels = 2
        else:
            self._channels = 1

        self._audio = audiobusio.I2SOut(i2s_bit_clock, i2s_word_select, i2s_data)

        # As per https://github.com/todbot/circuitpython-synthio-tricks use a mixer:
        self._mixer = audiomixer.Mixer(channel_count=self._channels, sample_rate=SYNTH_RATE, buffer_size=BUFFER_SIZE)

        self._mixer.voice[0].level = 1.0  


        # TODO: if envelope not given, "the default envelope, instantly turns notes on and off"
        # which may be what we want!
        env = synthio.Envelope(attack_time=0.1, decay_time=0.05, release_time=0.2, attack_level=1.0, sustain_level=0.8)
        self._synth = synthio.Synthesizer(channel_count=self._channels, sample_rate=SYNTH_RATE, envelope=env)

        self._audio.play(self._mixer)
        self._mixer.voice[0].play(self._synth)

# FIXME: keep this? not sure

        # Build some waveforms
        #
        self._WAVE_SINE = numpy.array(
            numpy.sin(numpy.linspace(0, 2*numpy.pi, SAMPLE_SIZE, endpoint=False)) * SAMPLE_VOLUME, dtype=numpy.int16)

        # this is a rising sawtooth, going from -SAMPLE_VOLUME down to +SAMPLE_VOLUME
        # TODO: does a falling sawtooth sound different?
        self._WAVE_SAW = numpy.linspace(SAMPLE_VOLUME, -SAMPLE_VOLUME, num=SAMPLE_SIZE, dtype=numpy.int16)

        # print(f"wave_sine: {self._WAVE_SINE}")
        # print(f"wave_saw: {self._WAVE_SAW}")


        # TODO: Set the default waveform - sine?
        #
        # self._waveform = None # 'None' gets you a square wave.
        self._waveform = self._WAVE_SINE

        # These two LFOs persist, but can be modified on the fly.
        #
        # TODO: should/can we use a smaller wave for the LFO envelopes?
        self._trem_LFO = synthio.LFO(rate=10, waveform=self._WAVE_SINE)
        self._trem_current = LFO_NONE

        self._vib_LFO = synthio.LFO(rate=5, waveform=self._WAVE_SINE)
        self._vib_current = LFO_NONE

        self._drone1 = None
        self._drone2 = None

        self.setNumOscs(1)

        
    def setVolume(self, level):
        """
        Volume, from 0.0 to 1.0
        """
        self._mixer.voice[0].level = level

    # setters for waveform
    def setWaveformSine(self) -> None:
        self._waveform = self._WAVE_SINE

    def setWaveformSaw(self) -> None:
        self._waveform = self._WAVE_SAW

    def setWaveformSquare(self) -> None:
        self._waveform = None

    # setters for tremolo and vibrato
    def setTremolo(self, tremFreq) -> None:
        self._trem_LFO.rate = tremFreq
        self._trem_current = self._trem_LFO

    def clearTremolo(self) -> None:
        self._trem_current = LFO_NONE

    def setVibrato(self, vibFreq) -> None:
        self._vib_LFO.rate = vibFreq
        self._vib_current = self._vib_LFO

    def clearVibrato(self) -> None:
        self._vib_current = LFO_NONE


    '''
        Play a note.
        Uses the current values set for vibrato and tremolo.
    '''
    def play(self, midi_note_value):

        # print(f"note {midi_note_value}")

        notes = []
        for i in range(self._numOscs):
            f = synthio.midi_to_hz(midi_note_value) * (1 + i*FAT_DETUNE)
            notes.append(synthio.Note(frequency=f,
                         waveform=self._waveform, amplitude=self._trem_current, bend=self._vib_current))
        self._synth.release_all_then_press(notes)

        # note = synthio.Note(synthio.midi_to_hz(midi_note_value), 
                            # waveform=self._waveform, amplitude=self._trem_current, bend=self._vib_current)
        # self._synth.release_all_then_press((note))


    # we'd rather create the notes once, then change their frequency. or does it matter?
    # probably does!
    #
    # takes frequencies (in Hz) not MIDI notes.
    #
    def startDrone(self, f1, f2):
        self._drone1 = synthio.Note(f1, waveform=self._waveform, amplitude=1, bend=1)
        self._drone2 = synthio.Note(f2, waveform=self._waveform, amplitude=1, bend=1)
        self._synth.release_all_then_press((self._drone1, self._drone2))

    def drone(self, f1, f2):
        if self._drone1 == None or self._drone2 == None:
            print("must start drone!")
            return
        # print(f"drone {f1}, {f2}")
        if f1 < 0 or f1 > 32767 or f2 < 0 or f2 > 32767:
            print(f"*** drone freq OOB: {f1}, {f2}")
            return

        self._drone1.frequency = f1
        self._drone2.frequency = f2

    def stopDrone(self):
        self._synth.release_all()
        self._drone1 = None
        self._drone2 = None

    def stop(self):
        self._synth.release_all()

    '''
        Can/should we do this automatically?
        see https://docs.circuitpython.org/en/latest/docs/design_guide.html#lifetime-and-contextmanagers
    '''
    def deinit(self):
        self._audio.deinit()

    def setNumOscs(self, numOscs):
        self._numOscs = numOscs


# ---------------- class test methods


    def test_drone(self, n):
        print("FeatherSynth6.test() with GC fix...")

        # test drone mode
        v = 0.1
        for i in range(n, 0, -1):
            print(f"Testing drone mode #{i}....")
            f1 = 300
            self.setVolume(v)
            v = v + 0.1
            self.startDrone(f1, f1)
            for delta in range(-100, 100):
                self.drone(f1, f1+delta)
                time.sleep(0.02)
            for delta in range(100, -100, -1):
                self.drone(f1, f1+delta)
                time.sleep(0.02)
            self.stopDrone()
        print("DONE Testing drone mode....")
        self.deinit()
        return
    

    # create a sawtooth sort of 'song', like a siren, with non-integer midi notes
    def test_sawtooth(self):

        start_note = 65
        song_notes = numpy.arange(0, 20, 0.1)
        song_notes = numpy.concatenate((song_notes, numpy.arange(20, 0, -0.1)), axis=0)
        delay = 0.02

        while True:
            for n in song_notes:
                self.play(start_note + n)
                time.sleep(delay)
            time.sleep(1) # hold last note for one more beat
            self.stop()
            time.sleep(1)
    

    # integer version
    def test_sawtooth_int(self):

        start_note = 65
        song_notes = numpy.arange(0, 20, 1)
        song_notes = numpy.concatenate((song_notes, numpy.arange(20, 0, -1)), axis=0)
        delay = 0.2

        # after 'tiny lfo song' by @todbot
        start_note = 65
        song_notes = (+3, 0, -2, -3, -2, 0, -2, -3)
        delay = 1

        while True:
            for n in song_notes:
                self.play(start_note + n)
                time.sleep(delay)
            time.sleep(1) # hold last note for one more beat
            self.stop()
            time.sleep(1)
    

    # test tremolo and vibrato
    def test_trem_and_vib(self):

        # after 'tiny lfo song' by @todbot
        start_note = 65
        song_notes = (+3, 0, -2, -3, -2, 0, -2, -3)
        delay = 1

        i = 1
        while True:
            print(f"Playing #{i}...")

            if i%4 == 1:
                self.clearTremolo()
                self.clearVibrato()
            elif i%4 == 2:
                self.setTremolo(15)
                self.clearVibrato()
            elif i%4 == 3:
                self.clearTremolo()
                self.setVibrato(8)
            elif i%4 == 0:
                self.setTremolo(25)
                self.setVibrato(4)

            for n in song_notes:
                self.play(start_note + n)
                time.sleep(delay)
            time.sleep(1) # hold last note for one more beat
            self.stop()
            time.sleep(1)

            i += 1


    def test_phat_2(self):

        start_note = 65
        song_notes = (+3, 0, -2, -3, -2, 0, -2, -3)
        delay = 1

        while True:

            print("fatness 1....")
            self.setNumOscs(1)
            for n in song_notes:
                self.play(start_note + n)
                time.sleep(delay)
            
            print("fatness 2....")
            self.setNumOscs(2)
            for n in song_notes:
                self.play(start_note + n)
                time.sleep(delay)
            
            print("fatness 3....")
            self.setNumOscs(3)
            for n in song_notes:
                self.play(start_note + n)
                time.sleep(delay)
            
            print("fatness 4....")
            self.setNumOscs(4)
            for n in song_notes:
                self.play(start_note + n)
                time.sleep(delay)


    """
        from https://github.com/todbot/circuitpython-synthio-tricks/tree/main#detuning-oscillators-for-fatter-sound
    """
    def test_phat(self):

        # import board, time, audiopwmio, synthio
        # audio = audiopwmio.PWMAudioOut(board.TX)
        # synth = synthio.Synthesizer(sample_rate=22050)
        # audio.play(synth)

        detune = 0.005  # how much to detune, 0.7% here
        num_oscs = 1
        midi_note = 45

        HOLD_TIME = 2.0
        INTER_TIME = 0.1

        while True:

            print(f"num_oscs: {num_oscs}")
            notes = []  # holds note objs being pressed
            # simple detune, always detunes up
            for i in range(num_oscs):
                f = synthio.midi_to_hz(midi_note) * (1 + i*detune)
                notes.append(synthio.Note(frequency=f))

            self._synth.press(notes)
            time.sleep(HOLD_TIME)

            self._synth.release(notes)
            time.sleep(INTER_TIME)

            # increment number of detuned oscillators
            num_oscs = num_oscs+1 if num_oscs < 5 else 1

