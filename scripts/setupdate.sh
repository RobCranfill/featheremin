# 'source' this to create a function that will update FROM the RP2040 to here, to be committed.
# to see it it's set, do 'type update'
function update() {
	CPATH=/mnt/CIRCUITPY
	sudo mount -t drvfs F: $CPATH
	cp -uv $CPATH/feathereminMain.py $CPATH/feathereminDisplay9341.py $CPATH/featherSynth5.py $CPATH/README.md .
}
