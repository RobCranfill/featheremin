# eighties_arp_synthio.py -- playing with arpeggios, testing my Arpy class
# 20 Jun 2023 - @todbot / Tod Kurt
#
#  - arp arp arp
#  - two pots, two buttons, no keys!
#  - no musical knowledge needed, just plug it, start twisting knobs
#  - video demo: https://www.youtube.com/watch?v=noj92Ae0IQI
#
# UI is:

#  VL563L0X #1 (was knobA) - adjusts root note      (QTPy A0)
#  VL563L0X #2 (was knobB) - adjusts BPM            (QTPY A1)

#  APDS "up" (was buttonA) - changes arp pattern  (QTPy SDA)
#  APDS "right" (was buttonB) - changes num iters up for pattern (QTPy SCL)

#
# Circuit:
# - See: "eighties_arp_bb.png" wiring
# - QT Py RP2040 or similar

# (was) - QTPy RX pin is audio out, going through RC filter (1k + 100nF) to TRS jack
# (is) I2S audio out

import time, random
import board, analogio, keypad
import audiopwmio, audiomixer, synthio
import ulab.numpy as np
import neopixel, rainbowio  # circup install neopixel
from arpy import Arpy

# cran
import audiobusio
import adafruit_vl53l0x as vl53l0x
import cran_vlx


RANGE_THRESH = 500

# map a ToF range (0-8000) to a "knob" (0-64K?)
def rangeAsKnobVal(str, vl53l0x):
    # time.sleep(0.1) # don't read too fast?
    r = vl53l0x.range
    if r > RANGE_THRESH:
        return -1
    val = r * 64000 / RANGE_THRESH
    print(f" {str} {r} -> {val}")
    return val


num_voices = 3       # how many voices for each note
lpf_basef = 2500     # filter lowest frequency
lpf_resonance = 1.5  # filter q

# cranfill - instead of analog knobs, we have time-of-flight sensors!
# knobA = analogio.AnalogIn(board.A0)
# knobB = analogio.AnalogIn(board.A1)
cvlx = cran_vlx.CranVLX()

# keys = keypad.Keys( (board.SDA, board.SCL), value_when_pressed=False )

led = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.1)

# audio = audiopwmio.PWMAudioOut(board.RX)  # RX pin on QTPY RP2040
audio = audiobusio.I2SOut(bit_clock=board.D9, word_select=board.D10, data=board.D11)

mixer = audiomixer.Mixer(channel_count=1, sample_rate=28000, buffer_size=2048)
synth = synthio.Synthesizer(channel_count=1, sample_rate=28000)
audio.play(mixer)
mixer.voice[0].play(synth)
mixer.voice[0].level = 0.8

# our oscillator waveform, a 512 sample downward saw wave going from +/-30k
wave_saw = np.linspace(30000, -30000, num=512, dtype=np.int16)  # max is +/-32k but gives us headroom
amp_env = synthio.Envelope(attack_level=1, sustain_level=1, release_time=0.5)

voices=[]  # holds our currently sounding voices ('Notes' in synthio speak)

# called by arpy to turn on a note
def note_on(n):
    # print("  note on ", n )
    led.fill(rainbowio.colorwheel( n % 12 * 20  ))
    fo = synthio.midi_to_hz(n)
    voices.clear()  # delete any old voices
    for i in range(num_voices):
        f = fo * (1 + i*0.007)
        lpf_f = fo * 8  # a kind of key tracking
        lpf = synth.low_pass_filter( lpf_f, lpf_resonance )
        voices.append( synthio.Note( frequency=f, filter=lpf, envelope=amp_env, waveform=wave_saw) )
    synth.press(voices)

# called by arpy to turn off a note
def note_off(n):
    # print(f"  note off {n}")
    led.fill(0)
    synth.release(voices)

# simple range mapper, like Arduino map()
def map_range(s, a1, a2, b1, b2): return  b1 + ((s - a1) * (b2 - b1) / (a2 - a1))

arpy = Arpy()
arpy.note_on_handler = note_on
arpy.note_off_handler = note_off
arpy.on()

arpy.root_note = 37
arpy.set_arp('suspended4th')

arpy.set_bpm( bpm=110, steps_per_beat=4 ) # 110 bpm 16th notes
arpy.set_transpose(distance=12, steps=0)

knobfilter = 0.75

knobAval = rangeAsKnobVal("A", cvlx._sensor_A) # was knobA.value
lastKA = knobAval

knobBval = rangeAsKnobVal("B", cvlx._sensor_B) # was knobB.value
lastKB = knobBval

# print(f" knobAval {knobAval}, knobBval {knobBval}")

while True:

    doKeys = False
    if doKeys:
        key = keys.events.get()
        if key and key.pressed:
            if key.key_number==0:  # left button changes arp played
                arpy.next_arp()
                print(arpy.arp_name())
            if key.key_number==1:  # right button changes arp up iterations
                steps = (arpy.trans_steps + 1) % 3;
                print(f"steps {steps}")
                arpy.set_transpose(steps=steps)

    # filter noisy adc
    # knobAval = knobAval * knobfilter + (1-knobfilter) * ra
    # knobBval = knobBval * knobfilter + (1-knobfilter) * rb
    
    # ka is new knobA.value
    ka = rangeAsKnobVal("A", cvlx._sensor_A)
    if ka == -1:
        ka = lastKA
    else:
        lastKA = ka
    knobAval = knobAval * knobfilter + (1-knobfilter) * ka

    # kb is new knobB.value
    kb = rangeAsKnobVal("B", cvlx._sensor_B) # was knobB.value
    if kb == -1:
        kb = lastKB
    else:
        lastKB = kb
    knobBval = knobBval * knobfilter + (1-knobfilter) * kb 


    # map knobA to root note
    arpy.root_note = int(map_range( knobAval, 0,65535, 24, 72) )

    # map knobB to bpm
    arpy.set_bpm( map_range(knobBval, 0, 65535, 40, 180 ) )

    arpy.update()
