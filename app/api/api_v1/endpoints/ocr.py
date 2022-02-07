from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import Any, Optional

from schemas.ocr import OcrBase, Ocr
from core.config import settings

router = APIRouter()

import os
#import cv2
import pytesseract
#import numpy as np
import tempfile
import shutil
#from PIL import Image
import pytesseract
import mimetypes
from nextcloud import NextCloud
import logging
import sys

logger = logging.getLogger()
streamHandler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)
logger.error("This is the first error")

NEXTCLOUD_URL = settings.NEXTCLOUD_URL
NEXTCLOUD_USERNAME = settings.NEXTCLOUD_USERNAME
NEXTCLOUD_PASSWORD = settings.NEXTCLOUD_PASSWORD
NEXTCLOUD_OCR_INPUT_DIR = settings.NEXTCLOUD_OCR_INPUT_DIR
NEXTCLOUD_OCR_OUTPUT_DIR = settings.NEXTCLOUD_OCR_OUTPUT_DIR
NEXTCLOUD_OCR_TAG = settings.NEXTCLOUD_OCR_TAG
VERIFY_INPUTPATH = settings.VERIFY_INPUTPATH
level = logging.getLevelName(settings.OCR_LOGLEVEL)
logger.setLevel(level)


logging.debug('NEXTCLOUD_URL: ' + NEXTCLOUD_URL)
logging.debug('NEXTCLOUD_USERNAME: ' + NEXTCLOUD_USERNAME)
logging.debug('NEXTCLOUD_PASSWORD: ' + NEXTCLOUD_PASSWORD)
logging.debug('NEXTCLOUD_OCR_INPUT_DIR: ' + NEXTCLOUD_OCR_INPUT_DIR)
logging.debug('NEXTCLOUD_OCR_OUTPUT_DIR: ' + NEXTCLOUD_OCR_OUTPUT_DIR)
logging.debug('VERIFY_INPUTPATH: ' + str(VERIFY_INPUTPATH))
logging.debug('NEXTCLOUD_OCR_TAG: ' + NEXTCLOUD_OCR_TAG)

def ocr_batch(images: list):
    for image_path in images:
        print(image_path)
        post_images(image_path=image_path)

@router.post("/batch", status_code=200, response_model=Ocr)
async def post_batch(*, runbatch: bool, background_tasks: BackgroundTasks) -> dict:
    """
    Convert all images in the backup folder to PDF
    """

    if(not runbatch):
        return {"image_path": runbatch,"message": "Nothing to do", "status": "Ignored"}

    image_list = []
    try:
        with NextCloud(
                    NEXTCLOUD_URL,
                    user=NEXTCLOUD_USERNAME,
                    password=NEXTCLOUD_PASSWORD,
                    ) as nxc:
            nc_file_list = nxc.list_folders(NEXTCLOUD_OCR_INPUT_DIR, all_properties=True).data
            for nc_file in nc_file_list:
                tag_scanned = False
                nc_file_tags = nc_file.get_tags()
                if(len(nc_file_tags) > 0):
                    for tag in nc_file_tags:
                        if tag.display_name == NEXTCLOUD_OCR_TAG:
                            logging.debug('tag: ' + NEXTCLOUD_OCR_TAG)
                            tag_scanned = True
                image_path = nc_file.href
                mime = mimetypes.guess_type(nc_file.href)[0]

                if mime != None:
                    mime = mime.split('/')[0]
                    print(mime)
                    logging.debug('image_path: ' + image_path)
                if(not tag_scanned and not image_path.endswith('/') and mime != None and mime == 'image'):
                    if(image_path.startswith('/remote.php/dav/files/' + NEXTCLOUD_USERNAME)):
                        image_path = image_path[len('/remote.php/dav/files/' + NEXTCLOUD_USERNAME):]
                        logging.debug('image_path: ' + image_path)
                    image_list.append(image_path)
        if len(image_list) > 0:
            background_tasks.add_task(ocr_batch, image_list)
        return {"image_path": runbatch,"message": str(len(image_list)) + " messages will be processed", "status": "OK"}
    except Exception as e:
        return {"image_path": runbatch,"message": str(e), "status": "Failure"}

@router.post("/images", status_code=200, response_model=Ocr)
def post_images(*, image_path: str,) -> dict:
    """
    Convert Image to PDF
    """
    logging.debug('image_path: ' + image_path)
    try:
        if(image_path.startswith(NEXTCLOUD_USERNAME+"/files")):
            image_path = image_path[len(NEXTCLOUD_USERNAME+"/files"):]
            logging.debug('image_path: ' + image_path)
        if(VERIFY_INPUTPATH and not image_path.startswith(NEXTCLOUD_OCR_INPUT_DIR)):
            return {"image_path": image_path,"message": "ignored because folder not " + NEXTCLOUD_OCR_INPUT_DIR , "status": "IGNORED"}
    except Exception as e:
                print("parse error: " + str(e))
    try:
        
        workdir = tempfile.mkdtemp(prefix="ocr_")
        with NextCloud(
                NEXTCLOUD_URL,
                user=NEXTCLOUD_USERNAME,
                password=NEXTCLOUD_PASSWORD,
                ) as nxc:
            try:    
                nc_file_list = nxc.list_folders(NEXTCLOUD_OCR_INPUT_DIR).data
                logging.debug('nc_file_list: ' + str(nc_file_list))
                nc_file_remote_name = image_path
                logging.debug('nc_file_remote_name: ' + str(nc_file_remote_name))
                nc_file_remote = nxc.get_file(nc_file_remote_name)
                logging.debug('nc_file_remote: ' + str(nc_file_remote))
                nc_file_name, nc_file_ext = os.path.splitext(os.path.basename(nc_file_remote_name))
                logging.debug('nc_file_name: ' + str(nc_file_name))
                logging.debug('nc_file_ext: ' + str(nc_file_ext))
                nc_file_remote.download(target=workdir)
            except Exception as e:
                print("download error: " + str(e))
            try:
                pdf = pytesseract.image_to_pdf_or_hocr(os.path.join(workdir, nc_file_name + nc_file_ext), extension='pdf', lang="deu")
                file_ocr_name = os.path.join(workdir, nc_file_name + "-" + str(nc_file_remote.file_id) + ".pdf")
                with open(file_ocr_name, 'w+b') as file_ocr:
                    file_ocr.write(pdf)
            except Exception as e:
                print("ocr error: " + str(e))
            try:
                file_ocr_remote = NEXTCLOUD_OCR_OUTPUT_DIR + "/" + nc_file_name + "-" + str(nc_file_remote.file_id) + ".pdf"
                nxc.upload_file(file_ocr_name, file_ocr_remote).data
                nc_file_remote.add_tag(tag_name=NEXTCLOUD_OCR_TAG)
            except Exception as e:
                print("upload error: " + str(e))
        shutil.rmtree(workdir)
        return {"image_path": image_path,"message": "successfully converted " + nc_file_remote_name + " to " + file_ocr_remote, "status": "OK"}
    except Exception as e:
        return {"image_path": image_path,"message": str(e), "status": "Failure"}