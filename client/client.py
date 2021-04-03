import socket
import tqdm
import os
import time
import threading

SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 4096 # send 4096 bytes each time step

host = "192.168.2.35"
port = 5001

dropfile = "dropfiles/"
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
        time.sleep(1)

thread = threading.Thread(target=drop_files_handel, daemon=True)
thread.start()
thread.join()