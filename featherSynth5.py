# A synthio-based implementation of FeatherSynth
# For the Featheremin project - https://github.com/RobCranfill/featheremin
#
import audiopwmio
import microcontroller
import random
import synthio
import time
import ulab.numpy as np

SYNTH_RATE    = 22050
SAMPLE_RATE   = 28000
SAMPLE_SIZE   =   512
SAMPLE_VOLUME = 32000

# A do-nothing 'BlockInput' for the LFOs
LFO_NONE = 1.0

class FeatherSynth:
    '''
        Our new synthio-based synth.

        Can change waveform, TODO: envelope, and add tremolo or vibrato).

        TODO: Triangle wave? Saw up vs saw down? (it is a rising sawtooth now.)

    '''
    def __init__(self, boardPinPWM: microcontroller.Pin) -> None:

        # keeping a reference here prevents the PWMAudioOut object from being garbage collected.
        self._audio = audiopwmio.PWMAudioOut(boardPinPWM)

        self._WAVE_SINE = np.array(np.sin(np.linspace(0, 2*np.pi, SAMPLE_SIZE, endpoint=False)) * SAMPLE_VOLUME, dtype=np.int16)
        
        # this is a rising sawtooth, going from -SAMPLE_VOLUME down to +SAMPLE_VOLUME
        # TODO: does a falling sawtooth sound different?
        self._wave_saw = np.linspace(SAMPLE_VOLUME, -SAMPLE_VOLUME, num=SAMPLE_SIZE, dtype=np.int16)

        # print(f"wave_sine: {self._WAVE_SINE}")
        # print(f"wave_saw: {self._wave_saw}")

        env = synthio.Envelope(attack_time=0.1, decay_time=0.05, release_time=0.2, attack_level=1.0, sustain_level=0.8)
        
        # TODO: if envelope not given, "the default envelope, instantly turns notes on and off"
        # which may be what we want!
        self._synth = synthio.Synthesizer(sample_rate=SYNTH_RATE, envelope=env)

        # TODO: Set the default waveform. Sine?
        #
        # self._waveform = None # 'None' gets you a square wave.
        self._waveform = self._WAVE_SINE
        
        # These two LFOs persist, but can be modified on the fly.
        #
        # TODO: should/can we use a smaller wave for the LFO envelopes?
        self._tremLFO = synthio.LFO(rate=10, waveform=self._WAVE_SINE)
        self._tremCurrent = LFO_NONE

        self._vibLFO = synthio.LFO(rate=5, waveform=self._WAVE_SINE)
        self._vibCurrent = LFO_NONE

        self._audio.play(self._synth)


    # setters for waveform
    def setWaveformSine(self) -> None:
        self._waveform = self._WAVE_SINE

    def setWaveformSaw(self) -> None:
        self._waveform = self._wave_saw

    def setWaveformSquare(self) -> None:
        self._waveform = None
    

    # setters for tremolo and vibrato
    def setTremolo(self, tremFreq) -> None:
        self._tremLFO.rate = tremFreq
        self._tremCurrent = self._tremLFO

    def clearTremolo(self) -> None:
        self._tremCurrent = LFO_NONE

    def setVibrato(self, vibFreq) -> None:
        self._vibLFO.rate = vibFreq
        self._vibCurrent = self._vibLFO

    def clearVibrato(self) -> None:
        self._vibCurrent = LFO_NONE


    '''
        Play a note.
        Uses the current values set for vibrato and tremolo.
    '''
    def play(self, midi_note_value):

        # print(f"note {midi_note_value}")

        note = synthio.Note(synthio.midi_to_hz(midi_note_value), waveform=self._waveform, 
                            amplitude = self._tremCurrent, bend=self._vibCurrent)

        self._synth.release_all_then_press((note))

    # we'd rather create the notes once, then change their frequency. or does it matter?
    # probably does!
    #
    # takes frequencies (in Hz) not MIDI notes.
    #
    def startDrone(self, f1, f2):

        self._n1 = synthio.Note(f1, waveform=self._waveform, 
                    amplitude = 1, bend=1)

        self._n2 = synthio.Note(f2, waveform=self._waveform, 
                    amplitude = 1, bend=1)

        self._synth.release_all_then_press((self._n1, self._n2))

    def drone(self, f1, f2):
        self._n1.frequency = f1
        self._n2.frequency = f2

    def stopDrone(self):
        self._synth.release_all()
        self._n1 = None
        self._n2 = None

    def stop(self):
        self._synth.release_all()

    def test(self):
        print("FeatherSynth5.test() with GC fix...")

        # test drone mode
        print("Testing drone mode....")
        self.startDrone(2000, 5000)
        for f1 in range(2000, 10000, 10):
            self.drone(f1, 10000-f1)
            # print(f"f={f1}")
            time.sleep(0.01)
        self.stopDrone()

        # # create a sawtooth sort of 'song', like a siren, with non-integer midi notes
        # start_note = 65
        # song_notes = np.arange(0, 20, 0.1)
        # song_notes = np.concatenate((song_notes, np.arange(20, 0, -0.1)), axis=0)
        # delay = 0.02

        # # integer version
        # start_note = 65
        # song_notes = np.arange(0, 20, 1)
        # song_notes = np.concatenate((song_notes, np.arange(20, 0, -1)), axis=0)
        # delay = 0.2
        
        # after 'tiny lfo song' by @todbot
        start_note = 65
        song_notes = (+3, 0, -2, -3, -2, 0, -2, -3)
        delay = 1

        i = 1
        while True:
            print(f"Playing #{i}...")

            # test tremolo and vibrato
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
