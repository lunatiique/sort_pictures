import os
import sys
import shutil
import json
import subprocess
import shlex
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
from tqdm import tqdm
import re
import piexif
import pillow_heif
pillow_heif.register_heif_opener()

# fetch date from image
def handle_image(file):
    try:
        image = Image.open(file)
    except:
        print("Unexpected error for file: " + file.split('\\')[-1] + ":", sys.exc_info()[0])
        return None
    exif_data = None
        # 📌 1️⃣ Extraction des métadonnées EXIF des images HEIC
    if file.lower().endswith('.heic') or file.lower().endswith('.heif'):
        heif_image = pillow_heif.open_heif(file)
        metadata = heif_image.info.get("exif")

        if metadata:
            try:
                exif_dict = piexif.load(metadata)
                if "Exif" in exif_dict and 36867 in exif_dict["Exif"]:  # Tag 'DateTimeOriginal'
                    creation_date = exif_dict["Exif"][36867].decode("utf-8")
                    return creation_date
            except Exception as e:
                print(f"Error extracting HEIC metadata for {file}: {e}")

    # 📌 2️⃣ Extraction EXIF pour JPEG/PNG
    else:
        exif_data = image.getexif()
    if exif_data is not None:
        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag, tag)
            if tag_name == 'DateTimeOriginal':  # or 'DateTimeDigitized'
                creation_date = value
                return creation_date
    #check if 'Screen Shot' in file name
    if 'Screenshot' in file:
        #extract date from file name
        creation_date = file.split('Screenshot')[1].split('.')[0]
        creation_date = creation_date.replace('-', ':').replace('_', '')
        #replace third ':' with ' ' to match image naming structure
        creation_date = creation_date[:10] + ' ' + creation_date[11:]
        return creation_date
    if 'IMG_' in file:
        #extract date from file name
        creation_date = file.split('IMG_')[1].split('.')[0]
        #if 
        if len(creation_date) < 14:
            return None
        if creation_date[:2] != '20':
            return None
        #match image naming structure
        creation_date = creation_date[:4] + ':' + creation_date[4:6] + ':' + creation_date[6:8] + ' ' + creation_date[9:11] + ':' + creation_date[11:13] + ':' + creation_date[13:15]
        return creation_date
    if 'IMG-' in file:
        #extract date from file name
        creation_date = file.split('IMG-')[1].split('.')[0]
        if len(creation_date) < 14:
            return None
        if creation_date[:2] != '20':
            return None
        #match image naming structure
        creation_date = creation_date[:4] + ':' + creation_date[4:6] + ':' + creation_date[6:8] + ' ' + creation_date[9:11] + ':' + creation_date[11:13] + ':' + creation_date[13:15]
        return creation_date
    #regex pattern to match date in file name : 2019-12-31-20-28-30 (YYYY-MM-DD-HH-MM-SS) or 20191231_151830 (YYYYMMDD_HHMMSS)
    pattern = re.compile(r'(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})|(\d{8}_\d{6})')
    match = pattern.search(file)
    if match:
        creation_date = match.group()
        if len(creation_date) < 14:
            return None
        if creation_date[:2] != '20':
            return None
        #match image naming structure
        if creation_date[4] == '-':
            creation_date = creation_date[:4] + ':' + creation_date[5:7] + ':' + creation_date[8:10] + ' ' + creation_date[11:13] + ':' + creation_date[14:16] + ':' + creation_date[17:19]
        else:
            creation_date = creation_date[:4] + ':' + creation_date[4:6] + ':' + creation_date[6:8] + ' ' + creation_date[9:11] + ':' + creation_date[11:13] + ':' + creation_date[13:15]
        return creation_date
    return None

# fetch date from video
def handle_video(video_path):
    cmd = "ffprobe -v quiet -print_format json -show_format"
    args = shlex.split(cmd)
    args.append(video_path)
    # run the ffprobe process, decode stdout into utf-8 & convert to JSON
    try :
        ffprobe_output = subprocess.check_output(args).decode('utf-8')
        ffprobe_output = json.loads(ffprobe_output)
        # extract creation_time
        try:
            creation_time = ffprobe_output['format']['tags']['creation_time']
            # convert creation_time to datetime object=
            creation_time = datetime.strptime(creation_time, "%Y-%m-%dT%H:%M:%S.%fZ")
            # format datetime object to match image naming structure
            creation_time = creation_time.strftime("%Y:%m:%d %H:%M:%S")
        except:
            if 'VID_' in video_path:
                #extract date from file name
                creation_date = video_path.split('VID_')[1].split('.')[0] 
                if len(creation_date) < 14:
                    return None
                if creation_date[:2] != '20':
                    return None
                #match image naming structure
                creation_date = creation_date[:4] + ':' + creation_date[4:6] + ':' + creation_date[6:8] + ' ' + creation_date[9:11] + ':' + creation_date[11:13] + ':' + creation_date[13:15]
                return creation_date
            if 'VID-' in video_path:
                #extract date from file name
                creation_date = video_path.split('VID-')[1].split('.')[0]
                if len(creation_date) < 14:
                    return None
                if creation_date[:2] != '20':
                    return None
                #match image naming structure
                creation_date = creation_date[:4] + ':' + creation_date[4:6] + ':' + creation_date[6:8] + ' ' + creation_date[9:11] + ':' + creation_date[11:13] + ':' + creation_date[13:15]
                return creation_date
            else:
                creation_time = None
        return creation_time
    except:
        print("Unexpected error for file: " + video_path + ":", sys.exc_info()[0])
        return None

# rename and move files in directory
def rename_and_move_files(directory):
    try:
        files = os.listdir(directory)
    except FileNotFoundError:
        print("Directory not found: " + directory)
        return
    listTypePicture = ['.jpg', '.png', '.JPG', '.PNG', '.jpeg', '.JPEG', '.heic', '.HEIC', '.webp', '.WEBP']
    listTypeVideo = ['.mp4', '.mov', '.MP4', '.MOV', '.avi', '.AVI', '.3gp', '.3GP', '.wmv', '.WMV']
    for filename in tqdm(files, ncols=70, desc="Processing files"):
        format = '.' + filename.split('.')[-1]
        if format in listTypePicture: 
            date = handle_image(os.path.join(directory, filename))
            file = True
        elif format in listTypeVideo:
            date = handle_video(os.path.join(directory, filename))
            file = True
        else:
            date = None
            file = False
        if date is not None:
            new_name = date.replace(':', '').replace(' ', '_') + format
            year_month_folder = os.path.join(directory, date[:4], date[5:7])  # extract year and month from date
            os.makedirs(year_month_folder, exist_ok=True)  # create year and month folders
            try:
                shutil.move(os.path.join(directory, filename), os.path.join(year_month_folder, new_name))
            except FileExistsError:
                print("File already exists: " + new_name)
                new_name = date.replace(':', '').replace(' ', '_') + "_1" + format
                shutil.move(os.path.join(directory, filename), os.path.join(year_month_folder, new_name))
            except:
                print("Unexpected error:", sys.exc_info()[0])
                raise
        elif file:
            print("No date found for file: " + filename)
            unknown_folder = os.path.join(directory, "unknown")
            os.makedirs(unknown_folder, exist_ok=True) # create unknown folder
            shutil.move(os.path.join(directory, filename), os.path.join(directory, unknown_folder, filename))

# main
if __name__ == "__main__":
    if len(sys.argv) > 1:
        directory_path = sys.argv[1]
        print("Sorting pictures and videos in directory: " + directory_path)
        rename_and_move_files(directory_path)
    else:
        print("Please provide a directory path")