# Raw test for generating 'drone' tones, for an attached I2S device.
# based on:
#   synthio_two_knob_drone_synth.py -- Got a Pico and two pots? Now you got a drone synth
#   5 Jun 2023 - @todbot / Tod Kurt
#   video demo: https://www.youtube.com/watch?v=KsSRaKjhmHg
#
import audiobusio
import audiomixer
import board
import microcontroller
import random
import synthio
import time

import ulab.numpy as np

# does auto-reload jank things up?
import supervisor
supervisor.runtime.autoreload = False  # CirPy 8 and above


# for I2S audio out
AUDIO_OUT_I2S_BIT  = board.D9
AUDIO_OUT_I2S_WORD = board.D10
AUDIO_OUT_I2S_DATA = board.D11

SYNTH_RATE    = 22050
SAMPLE_RATE   = 28000
SAMPLE_SIZE   =   512
SAMPLE_VOLUME = 32000
BUFFER_SIZE   =  4096 # up from 2K, does this help the SPI noise?


i2s_bit_clock = AUDIO_OUT_I2S_BIT
i2s_word_select = AUDIO_OUT_I2S_WORD
i2s_data = AUDIO_OUT_I2S_DATA

_audio = audiobusio.I2SOut(i2s_bit_clock, i2s_word_select, i2s_data)

# As per https://github.com/todbot/circuitpython-synthio-tricks use a mixer:
_mixer = audiomixer.Mixer(channel_count=1, sample_rate=SYNTH_RATE, buffer_size=BUFFER_SIZE)
_mixer.voice[0].level = 0.5  # 50% volume to start seems plenty

# TODO: if envelope not given, 
# "the default envelope, instantly turns notes on and off" 
#  - which may or may not be what we want!
#
env = synthio.Envelope(attack_time=0.1, decay_time=0.05, release_time=0.2, attack_level=1.0, sustain_level=0.8)
_synth = synthio.Synthesizer(sample_rate=SYNTH_RATE, envelope=env)

_audio.play(_mixer)
_mixer.voice[0].play(_synth)

f1 = 3000

note1 = synthio.Note(frequency=f1, amplitude=1, bend=1)
note2 = synthio.Note(frequency=f1, amplitude=1, bend=1)
_synth.press((note1,note2))

delay = 0.05

while True:
    print("up!")
    for delta in range(100):
        note1.frequency = f1/10
        note2.frequency = f1/10+delta
        time.sleep(delay)

    print("down!")
    for delta in range(100):
        note1.frequency = f1/10
        note2.frequency = f1/10-delta
        time.sleep(delay)

