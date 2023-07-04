# based on:
# synthio_two_knob_drone_synth.py -- Got a Pico and two pots? Now you got a drone synth
# 5 Jun 2023 - @todbot / Tod Kurt
# video demo: https://www.youtube.com/watch?v=KsSRaKjhmHg
import time, random, board, analogio, audiopwmio, synthio

# knob1 = analogio.AnalogIn(board.GP26)
# knob2 = analogio.AnalogIn(board.GP27)

audio = audiopwmio.PWMAudioOut(board.D5)
synth = synthio.Synthesizer(sample_rate=22050)
audio.play(synth)

f1 = 300

note1 = synthio.Note(frequency=f1, amplitude=1, bend=1)
note2 = synthio.Note(frequency=f1, amplitude=1, bend=1)
synth.press((note1,note2))

while True:
    for delta in range(100):
        note1.frequency = f1
        note2.frequency = f1+delta
        time.sleep(0.02)

    for delta in range(100):
        note1.frequency = f1
        note2.frequency = f1-delta
        time.sleep(0.02)
