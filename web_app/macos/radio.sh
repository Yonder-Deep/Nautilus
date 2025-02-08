# !/bin/bash
# Simply compiles radio.m to executable
clang -framework Foundation -framework IOKit radio.m -o radio.exe
# And tests
./radio.exe