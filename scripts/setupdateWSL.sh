# 'source' this to create a function that will update FROM the RP2040 to here, to be committed.
# to see it it's set, do 'type cpupdate'
# this is for WSL2 only!
# note: takes 1 arg, the drive letter (F on Flex15, E on ScreamerIII)
#
function cpupdate() {
	CPATH=/mnt/CIRCUITPY
	sudo mount -t drvfs $1: $CPATH 
	cp -uv $CPATH/*.py .
	cp -uv $CPATH/test/*.py ./test
}
