Gstreamer commands:

For Linux laptop:
```
gst-launch-1.0 -v udpsrc port=5000 ! capsfilter caps="application/x-rtp, media=video, clock-rate=90000, encoding-name=H264, payload=96" ! rtph264depay ! avdec_h264 ! videoconvert ! autovideosink
```

For Rpi:
```
gst-launch-1.0 -v v4l2src device=/dev/video4 ! 'video/x-raw,framerate=30/1,width=320,height=240' ! videoconvert ! x264enc tune=zerolatency ! rtph264pay ! udpsink host=10.42.0.1 port=5000
```