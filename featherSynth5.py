# cran - Implement a class called FeatherSynth
# 

import audiopwmio
import synthio
import microcontroller
import time
import ulab.numpy
import random

SYNTH_RATE = 22050

class FeatherSynth:
    def __init__(self, boardPinPWM: microcontroller.Pin) -> None:

        # must prevent the PWMAudioOut object from being garbage collected:
        self._audio = audiopwmio.PWMAudioOut(boardPinPWM)

        env = synthio.Envelope(attack_time = 0.1, decay_time = 0.05, release_time = 0.2,
                                attack_level = 1.0, sustain_level = 0.8)
        self._synth = synthio.Synthesizer(sample_rate = SYNTH_RATE, envelope=env)
        self._audio.play(self._synth)

    def play(self, midi_note_value):
        # print(f"FeatherSynth5: play midiNote ({midi_note_value})")
        note = synthio.Note(synthio.midi_to_hz(midi_note_value))
        self._synth.release_all_then_press((note))

    def stop(self):
        self._synth.release_all()

    def test(self):
        print("FeatherSynth5.test() with GC fix...")

        # create a sawtooth sort of 'song', like a siren, with non-integer midi notes
        start_note = 65
        song_notes = ulab.numpy.arange(0, 20, 0.1)
        song_notes = ulab.numpy.concatenate((song_notes, ulab.numpy.arange(20, 0, -0.1)), axis=0)

        while True:
            print("Playing...")
            for n in song_notes:
                self.play(start_note + n)
                time.sleep(.01)

