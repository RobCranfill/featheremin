import board
import featherSynth5

AUDIO_OUT_I2S_BIT  = board.D9
AUDIO_OUT_I2S_WORD = board.D10
AUDIO_OUT_I2S_DATA = board.D11

synth = featherSynth5.FeatherSynth(
    i2s_bit_clock=AUDIO_OUT_I2S_BIT, i2s_word_select=AUDIO_OUT_I2S_WORD, i2s_data=AUDIO_OUT_I2S_DATA)
synth.setVolume(0.1)
print("OK with sound?")
synth.test(5)

while True:
    pass
