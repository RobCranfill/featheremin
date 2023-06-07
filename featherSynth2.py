# cran - synth2
# based on
# synthio_tiny_lfo_song_2.py -- tiny "song" made with just LFOs in synthio
# 29 May 2023 - @todbot / Tod Kurt
# video demo: https://www.youtube.com/watch?v=m_ALNCWXor0
# requires CircuitPython 8.2.0-beta0 or later

import audiopwmio
import synthio


class FeatherSynth2:

    def __init__(self, boardPinPWM) -> None:

        audio = audiopwmio.PWMAudioOut(boardPinPWM)

        # class synthio.Envelope(*, attack_time: float | None = 0.1, 
        #                       decay_time: float | None = 0.05, 
        #                       release_time: float | None = 0.2, 
        #                       attack_level: float | None = 1.0, 
        #                       sustain_level: float | None = 0.8)

        env = synthio.Envelope(attack_time = 0.1, decay_time = 0.05, release_time = 0.2,
                                attack_level = 1.0, sustain_level = 0.8)

        self._synth = synthio.Synthesizer(sample_rate=22050, envelope = env)
        audio.play(self._synth)

        self._lfo_tremo1 = synthio.LFO(rate=3)  # 3 Hz for fastest note (cran: modulation?)
        self._lfo_tremo2 = synthio.LFO(rate=2)  # 2 Hz for middle note
        self._lfo_tremo3 = synthio.LFO(rate=1)  # 1 Hz for lower note
        self._lfo_tremo4 = synthio.LFO(rate=0.75) # 0.75 Hz for lowest bass note

    def play(self, midi_note):
        print(f"FeatherSynth2: play midiNote ({midi_note})")

        wiggle = True
        if wiggle:
            note1 = synthio.Note(synthio.midi_to_hz(midi_note),     amplitude=self._lfo_tremo1)
            note2 = synthio.Note(synthio.midi_to_hz(midi_note-7),   amplitude=self._lfo_tremo2)
            note3 = synthio.Note(synthio.midi_to_hz(midi_note-12),  amplitude=self._lfo_tremo3)
            note4 = synthio.Note(synthio.midi_to_hz(midi_note-24),  amplitude=self._lfo_tremo4)
        else:
            note1 = synthio.Note(synthio.midi_to_hz(midi_note), bend=self._lfo_tremo4)
            note2 = synthio.Note(synthio.midi_to_hz(midi_note-7))
            note3 = synthio.Note(synthio.midi_to_hz(midi_note-12))
            note4 = synthio.Note(synthio.midi_to_hz(midi_note-24))

        self._synth.release_all_then_press((note1, note2, note3, note4))

    def stop(self):
        # print("'stop' is NOP")
        pass

    def test():
        print("synthio_rude_noises1...")
    
