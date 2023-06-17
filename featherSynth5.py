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

class FeatherSynth:
    '''
        Our new synthio-based synth!

        Can change waveform, envelope, add amplitude or frequecy LFO (tremelo or vibrato).
        (^^^ some of that is TBD)
    '''
    def __init__(self, boardPinPWM: microcontroller.Pin) -> None:

        # must prevent the PWMAudioOut object from being garbage collected:
        self._audio = audiopwmio.PWMAudioOut(boardPinPWM)

        self._wave_sine = np.array(np.sin(np.linspace(0, 2*np.pi, SAMPLE_SIZE, endpoint=False)) * SAMPLE_VOLUME, dtype=np.int16)
        self._wave_saw = np.linspace(SAMPLE_VOLUME, -SAMPLE_VOLUME, num=SAMPLE_SIZE, dtype=np.int16)
        print(f"wave_sine: {self._wave_sine}")
        print(f"wave_saw: {self._wave_saw}")

        env = synthio.Envelope(attack_time=0.1, decay_time=0.05, release_time=0.2,
                                attack_level=1.0, sustain_level=0.8)
        
        # TODO: if envelope not given, "the default envelope, instantly turns notes on and off"
        # which may be what we want!
        self._synth = synthio.Synthesizer(sample_rate=SYNTH_RATE, envelope=env)

        # This will cause the Note to use a 50% duty cycle square wave
        # TODO: this probably shouldn't be the default - sine?
        #
        self._waveform = None

        self._audio.play(self._synth)

    def setWaveformSine(self) -> None:
        self._waveform = self._wave_sine

    def setWaveformSaw(self) -> None:
        self._waveform = self._wave_saw

    def setWaveformSquare(self) -> None:
        self._waveform = None
    
    '''
        Play a note.
        "If waveform or envelope are None the synthesizer object's default waveform or envelope are used."
    '''
    def play(self, midi_note_value):
        # print(f"FeatherSynth5: play midiNote ({midi_note_value})")
        note = synthio.Note(synthio.midi_to_hz(midi_note_value), waveform=self._waveform)
        self._synth.release_all_then_press((note))

    def stop(self):
        self._synth.release_all()

    def test(self):
        print("FeatherSynth5.test() with GC fix...")

        # create a sawtooth sort of 'song', like a siren, with non-integer midi notes
        start_note = 65
        song_notes = np.arange(0, 20, 0.1)
        song_notes = np.concatenate((song_notes, np.arange(20, 0, -0.1)), axis=0)

        while True:
            print("Playing...")
            for n in song_notes:
                self.play(start_note + n)
                time.sleep(.01)

