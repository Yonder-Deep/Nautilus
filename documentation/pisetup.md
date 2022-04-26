1. Set up an SD card with newest version of Raspbian (currently 11)
2. Create directory ~~dev~~ from the root. Clone the Yonder Deep repository. Navigate to the auv folder.
3. Run
   ~~~
   sudo pigpiod
   ~~~

   More details here: https://www.codetd.com/en/article/12959579
   
4. Run
   ~~~
   sudo raspi-config
   ~~~
   a. Select Interace Options
   b. Select I2C
   c. Select yes
   d. Select Interface Options
   e. Select Serial Port
   f. Select yes
   g. Select finish

   More details here: https://github.com/bluerobotics/ms5837-python
5. Navigate to the Adafruit_GPIO folder under api. Then navigate to Adafruit_Python... Run
   ~~~
   sudo python setup.py install
   ~~~

   More details here: https://github.com/adafruit/Adafruit_Python_GPIO

Note: These instructions don't work on a raspberry pi 4.
