import board
# import featherSynth5 as fsynth
import featherSynth6 as fsynth

AUDIO_OUT_I2S_BIT  = board.D9
AUDIO_OUT_I2S_WORD = board.D10
AUDIO_OUT_I2S_DATA = board.D11

# synth = fsynth.FeatherSynth(
#     i2s_bit_clock=AUDIO_OUT_I2S_BIT, i2s_word_select=AUDIO_OUT_I2S_WORD, i2s_data=AUDIO_OUT_I2S_DATA)
# synth.setVolume(0.1)
# print("OK with sound?")
# synth.test(5)


synth = fsynth.FeatherSynth(
    True, i2s_bit_clock=AUDIO_OUT_I2S_BIT, i2s_word_select=AUDIO_OUT_I2S_WORD, i2s_data=AUDIO_OUT_I2S_DATA)

# synth.setVolume(0.5)

# synth.test_drone()
synth.test_sawtooth()
synth.test_sawtooth_int()
synth.test_trem_and_vib()
synth.test_phat()
synth.test_phat_2()


print("test_feathereminSynth done!")
while True:
    pass
