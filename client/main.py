from __future__ import print_function
import logging
import six
import sys
import gphoto2 as gp
import threading
import os
import io
import multiprocessing
import time
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
import re
import socket
import time
import shutil
from subprocess import *
import tqdm

SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 4096 # send 4096 bytes each time step

host = "192.168.1.100"
port = 4466

dropfile = "/root/camera_sender/files_sender/"
files_sender = "/root/camera_sender/files_sender"
tmp_dir = "/root/camera_sender/tmp/"
processes = []
count_process = 0
camera_list = []
camera_list_new = []

addr_camera = []
addr_camera_new = []

def rename_find(path_file):
    Copyright = None
    arr = os.listdir(path_file)
    if(len(arr) == 2):
        for image_file in arr:
            arr = os.listdir(path_file)
            for image_file in arr:
                if image_file.endswith('.jpg') or image_file.endswith('.JPG'):
                    image = Image.open(path_file + "/" + image_file)
                    exifdata = image.getexif()
                    list = {}
                    for tag_id in exifdata:
                        tag = TAGS.get(tag_id, tag_id)
                        data = exifdata.get(tag_id)
                        try:
                            # decode bytes 
                            if isinstance(data, bytes):
                                data = data.decode()
                            list[tag] = data
                        except:
                            pass
                    Copyright = list['Copyright']
                if Copyright is not None:
                    file_data_str = image_file.split('.')
                    os.rename(path_file + "/" + image_file, path_file + "/" + Copyright + "." + file_data_str[1])
        
        arr = os.listdir(path_file)
        for image_file in arr:
            file_data_str = image_file.split('.')
            shutil.move(path_file + "/" + image_file, files_sender + "/" + image_file)
        flag_reame=True


def check_dir(process_dir):
    Path(process_dir).mkdir(parents=True, exist_ok=True)

def list_camera_files(camera, path='/'):
    result = []
    gp_list = gp.check_result(
        gp.gp_camera_folder_list_folders(camera, path))
    for name, value in gp_list:
        result.append(name)
    return result

def camera_wait_for_event(addr, count_process):
    try:
        camera = gp.Camera()
        port_info_list = gp.PortInfoList()
        port_info_list.load()
        idx = port_info_list.lookup_path(addr)
        camera.set_port_info(port_info_list[idx])
        camera.init()
        timeout = 3000  # milliseconds
        camera_files = list_camera_files(camera)
        if camera_files:
            # adjust camera configuratiuon
            cfg = camera.get_config()
            capturetarget_cfg = cfg.get_child_by_name('capturetarget')
            capturetarget = capturetarget_cfg.get_value()
            capturetarget_cfg.set_value('Memory card')
            camera.set_config(cfg)
        else:
            cfg = camera.get_config()
            capturetarget_cfg = cfg.get_child_by_name('capturetarget')
            capturetarget = capturetarget_cfg.get_value()
            capturetarget_cfg.set_value('Internal RAM')
            camera.set_config(cfg)

        while True:
            event_type, event_data = camera.wait_for_event(timeout)
            if event_type == gp.GP_EVENT_FILE_ADDED:
                check_dir(tmp_dir + count_process)
                cam_file = camera.file_get(
                    event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL)
                target_path = os.path.join(os.getcwd(), tmp_dir + count_process + "/" + event_data.name)
                print("Image is being saved to {}".format(target_path))
                cam_file.save(target_path)
                rename_find(tmp_dir + count_process)
    finally:
        camera.exit()

def intiCamera_list():
    global count_process
    camera_list = list(gp.Camera.autodetect())
    if not camera_list:
        print('No camera detected')
        return 1
    camera_list.sort(key=lambda x: x[1])
    for name, addr in camera_list:
        addr_camera.append(addr)
        processes.append(multiprocessing.Process(target=camera_wait_for_event, args=(addr, str(count_process).zfill(2))))
        time.sleep(1)
        count_process += 1
    [process.start() for process in processes]
    [process.join() for process in processes]

def main():
    while True:
        logging.basicConfig(format='%(levelname)s: %(name)s: %(message)s', level=logging.WARNING)
        callback_obj = gp.check_result(gp.use_python_logging())
        intiCamera_list()
        time.sleep(1)

def send_files(filename):
        # filename = "data.csv"
        # get the file size
        filesize = os.path.getsize(filename)
        # create the client socket
        s = socket.socket()

        print(f"[+] Connecting to {host}:{port}")
        s.connect((host, port))
        print("[+] Connected.")

        # send the filename and filesize
        s.send(f"{filename}{SEPARATOR}{filesize}".encode())

        # start sending the file
        progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "rb") as f:
            while True:
                # read the bytes from the file
                bytes_read = f.read(BUFFER_SIZE)
                if not bytes_read:
                    # file transmitting is done
                    break
                # we use sendall to assure transimission in 
                # busy networks
                s.sendall(bytes_read)
                # update the progress bar
                progress.update(len(bytes_read))
        # close the socket
        s.close()
        if os.path.exists(filename):
            os.remove(filename)

def drop_files_handel():
    while True:
        try:
            files_name = os.listdir(dropfile)
            if len(files_name) != 0:
                send_files(dropfile + files_name[0])
        except:
            pass
        time.sleep(2)

if __name__ == "__main__":
    thread = threading.Thread(target=drop_files_handel, daemon=True)
    thread.start()  
    time.sleep(1)
    sys.exit(main())