# 'source' this to create a function that will update FROM the RP2040 to here, to be committed.
# to see it it's set, do 'type cpupdate'
# this is for WSL2 only!
function cpupdate() {
	CPATH=/mnt/CIRCUITPY
	sudo mount -t drvfs E: $CPATH 
	cp -uv $CPATH/feathereminMain.py $CPATH/feathereminDisplay1.py /$CPATH/feathereminDisplay2.py $CPATH/featherSynth5.py $CPATH/README.md .
	cp -uv $CPATH/test/* ./test
}
