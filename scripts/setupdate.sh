# 'source' this to create a function that will update FROM the RP2040 to here, to be committed.
# to see it it's set, do 'type cpupdate'
# This is for native Ubuntu (not WSL)
function cpupdate() {
	CPATH=/media/rob/CIRCUITPY
	cp -uv $CPATH/feathereminMain.py $CPATH/feathereminDisplay?.py $CPATH/featherSynth?.py $CPATH/README.md gestureMenu.py .
	cp -uv $CPATH/test/* ./test
}
