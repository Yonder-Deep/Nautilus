# !/bin/bash
# Simply compiles radio.m to executable
clang -framework Foundation -framework IOKit radio.m -o radio.exe
# And tests
sudo ./radio.exe
# pppd on mac requires sudo even if using options files