# !/bin/bash
# Simply compiles radio.m to executable
clang -framework Foundation -framework IOKit radio.m -o radio.exe
# And tests
RADIO_PATH=$(./radio.exe)
# pppd on mac requires sudo even if using options files
if [ "$RADIO_PATH" == "Radio device not found" ]; then
    echo $RADIO_PATH
else
    sudo pppd $RADIO_PATH 57600 nodetach lock local 192.168.100.10:192.168.100.11
fi
