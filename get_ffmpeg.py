import requests
import os

from zipfile import ZipFile


url = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2021-10-02-12-23/ffmpeg-n4.4-154-g79c114e1b2-win64-gpl-shared-4.4.zip'
reply = requests.get(url)
open('ffmpeg.zip', 'wb').write(reply.content)

os.makedirs('ffmpeg', exist_ok=True)

with ZipFile('ffmpeg.zip', 'r') as zip_obj:
   for filepathname in zip_obj.namelist():
        if not ('/bin/' in filepathname):
            continue

        filename = filepathname.split('/')[-1]
        if len(filename) == 0:
            continue

        print(f'ffmpeg/{filename}')
        with open(f'ffmpeg/{filename}', 'wb') as f:
            f.write(zip_obj.read(filepathname))

os.remove('ffmpeg.zip')