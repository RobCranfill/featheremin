# cran - Implement a class called FeatherSynth
# 

import audiopwmio
import synthio
import microcontroller
import time
import ulab.numpy as np
import random

SYNTH_RATE = 22050
SAMPLE_RATE = 28000
SAMPLE_SIZE = 512
SAMPLE_VOLUME = 32000


LFO_NONE = 1.0

class FeatherSynth:
    '''
        Our new synthio-based synth.

        Can change waveform, envelope, add amplitude or frequecy LFO (tremolo or vibrato).
        (^^^ some of that is TBD)

        TODO: Triangle wave? Saw up vs saw down? (which one is it now?)

    '''
    def __init__(self, boardPinPWM: microcontroller.Pin) -> None:

        # must prevent the PWMAudioOut object from being garbage collected:
        self._audio = audiopwmio.PWMAudioOut(boardPinPWM)

        self._wave_sine = np.array(np.sin(np.linspace(0, 2*np.pi, SAMPLE_SIZE, endpoint=False)) * SAMPLE_VOLUME, dtype=np.int16)
        self._wave_saw = np.linspace(SAMPLE_VOLUME, -SAMPLE_VOLUME, num=SAMPLE_SIZE, dtype=np.int16)
        # print(f"wave_sine: {self._wave_sine}")
        # print(f"wave_saw: {self._wave_saw}")

        env = synthio.Envelope(attack_time=0.1, decay_time=0.05, release_time=0.2, attack_level=1.0, sustain_level=0.8)
        
        # TODO: if envelope not given, "the default envelope, instantly turns notes on and off"
        # which may be what we want!
        self._synth = synthio.Synthesizer(sample_rate=SYNTH_RATE, envelope=env)

        # This will cause the Note to use a 50% duty cycle square wave
        # TODO: this probably shouldn't be the default - sine?
        #
        self._waveform = None
        self._waveform = self._wave_sine
        
        # These two LFOs persist; we can change them as we like, 
        # and if we don't want to use them we just set the thing we currently are using to 'None'
        # FIXME: that didn't work.
        #
        self._tremLFO = synthio.LFO(rate=LFO_NONE, waveform=self._wave_sine) # ok to re-use sine wave here?
        self._tremCurrent = None

        self._vibLFO = synthio.LFO(rate=LFO_NONE, waveform=self._wave_sine) # ok to re-use sine wave here?
        self._vibCurrent = None

        self._audio.play(self._synth)

    def setWaveformSine(self) -> None:
        self._waveform = self._wave_sine

    def setWaveformSaw(self) -> None:
        self._waveform = self._wave_saw

    def setWaveformSquare(self) -> None:
        self._waveform = None
    
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
        "If waveform or envelope are None the synthesizer object's default waveform or envelope are used."
        but what about tremolo or vibrato?
    '''
    def play(self, midi_note_value):

        # print(f"note {midi_note_value}")

        note = synthio.Note(synthio.midi_to_hz(midi_note_value), waveform=self._waveform, 
                            amplitude = self._tremCurrent, bend=self._vibCurrent)
        
        # note = synthio.Note(synthio.midi_to_hz(midi_note_value), waveform=self._waveform)
        
        self._synth.release_all_then_press((note))

    def stop(self):
        self._synth.release_all()

    def test(self):
        print("FeatherSynth5.test() with GC fix...")

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
                self.setTremolo(15)
                self.setVibrato(8)

            for n in song_notes:
                self.play(start_note + n)
                time.sleep(delay)
            time.sleep(1) # hold last note for one more beat
            self.stop()
            time.sleep(1)

            i += 1