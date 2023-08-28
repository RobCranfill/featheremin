# 'source' this to create a function that will update FROM the RP2040 to here, to be committed.
# to see it it's set, do 'type cpupdate'
# this is for WSL2 only!
function cpupdate() {
	CPATH=/mnt/CIRCUITPY
	sudo mount -t drvfs E: $CPATH 
	cp -uv $CPATH/feathereminMain.py $CPATH/feathereminDisplay?.py $CPATH/featherSynth?.py $CPATH/README.md gestureMenu.py .
	cp -uv $CPATH/test/* ./test
}
