from goprocam import GoProCamera, constants
import shutil
import time

go_pro = GoProCamera.GoPro()

# shows everything on the camera: go_pro.listMedia(True)

# to delete all: go_pro.delete("all")
# # to delete last: go_pro.delete("last")


def take_photo_transfer_delete():
    go_pro.take_photo(timer=5)
    # go_pro.downloadLastMedia(custom_filename="yonderpic.JPG")
    # go_pro.delete("last")


def timelapse(interval):
    while True:
        go_pro.downloadLastMedia(go_pro.take_photo(timer=interval))


def media_download_and_transfer_and_delete():
    media = go_pro.downloadAll()
    for i in media:
        shutil.move('./100GOPRO-{}'.format(i), './gopro_images/100GOPRO-{}'.format(i))
    # go_pro.delete("all")

# The parameter time must be in seconds


def take_video(record_time):
    # go_pro.getWebcamPreview()
    go_pro.shoot_video(record_time)


take_video(5)
# take_photo_transfer_delete()

# go_pro.overview()
