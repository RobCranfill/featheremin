# based on synthio_rude_noises1.py, mods by cran

import board, time, random
import audiobusio, audiomixer, synthio
import ulab.numpy as np
import audiopwmio

SAMPLE_RATE = 28000
SAMPLE_SIZE = 512
SAMPLE_VOLUME = 32000

class FeatherSynth1:

    def __init__(self, boardPinPWM) -> None:

        # cran - was
        # lck_pin, bck_pin, dat_pin = board.MISO, board.MOSI, board.SCK
        # audio = audiobusio.I2SOut(bit_clock=bck_pin, word_select=lck_pin, data=dat_pin)

        audio = audiopwmio.PWMAudioOut(board.D5)

        mixer = audiomixer.Mixer(voice_count=1, sample_rate=SAMPLE_RATE, channel_count=1,
                                bits_per_sample=16, samples_signed=True, buffer_size=2048 )
        audio.play(mixer)

        self.synth_ = synthio.Synthesizer(sample_rate=SAMPLE_RATE)
        mixer.voice[0].level = 0.25 # turn down the volume a bit since this can get loud
        mixer.voice[0].play(self.synth_)

        self.wave_sine_ = np.array(np.sin(np.linspace(0, 2*np.pi, SAMPLE_SIZE, endpoint=False)) * SAMPLE_VOLUME, dtype=np.int16)
        print(f"wave_sine: {self.wave_sine_}")

        self.wave_saw_ = np.linspace(SAMPLE_VOLUME, -SAMPLE_VOLUME, num=SAMPLE_SIZE, dtype=np.int16)

        self.lfo1_ = synthio.LFO(rate=35, waveform=self.wave_sine_)
        self.lfo2_ = synthio.LFO(rate=1, waveform=self.wave_sine_)

        print("FeatherSynth1 init OK?")


    # FIXME: TODO: can we just create 1 note and then muck with it? maybe not
    def play(self, midiNote):
        print(f"FeatherSynth1: play midiNote {midiNote}")

        note = synthio.Note(frequency=synthio.midi_to_hz(midiNote), 
                             waveform=self.wave_sine_,
                            ring_frequency=synthio.midi_to_hz(midiNote)*1.05, 
                            ring_bend=0, 
                            #lfo1,
                            ring_waveform=self.wave_sine_)
        note.bend = self.lfo1_
        self.synth_.press(note)


    def stop(self):
        print("'stop' is NOP")


    def test():
        print("synthio_rude_noises1...")
        while True:

            print("no ring_bend", n)
            note1.ring_bend = 0
            time.sleep(1)

            #print("lfo bend")
            #note1.bend = lfo2
            print("ring_bend lfo1")
            note1.ring_bend = lfo1
            time.sleep(1)

            n = n + 4
            if n > 100: n = 45
            note1.frequency = synthio.midi_to_hz(n)
            note1.ring_frequency = synthio.midi_to_hz(n) * 1.05

            #f = f*1.5
            #fd = f*1.047
            #note1.frequency = f
            #note1.ring_frequency = fd

