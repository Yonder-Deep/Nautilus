from goprocam import GoProCamera, constants
import shutil
import time


# def __init__(self):
# Need to be connected to the gopros wifi for running any function
go_pro = GoProCamera.GoPro()


def take_photo():
    go_pro.take_photo()


def timelapse(interval):
    while True:
        go_pro.downloadLastMedia(go_pro.take_photo(timer=interval))


def start_video():
    go_pro.shoot_video(True)


def stop_video():
    go_pro.shoot_video(False)

# WORKS


def delete_all_media():
    go_pro.delete("all")

# WORKS


def delete_latest_media():
    go_pro.delete("last")

# WORKS


def gopro_info():
    go_pro.overview()
