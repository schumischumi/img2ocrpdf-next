from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any, Optional

from schemas.ocr import OcrBase, Ocr
from core.config import settings

router = APIRouter()

import os
import cv2
import pytesseract
import numpy as np
import tempfile
import shutil
from PIL import Image
import pytesseract


from nextcloud import NextCloud

NEXTCLOUD_URL = settings.NEXTCLOUD_URL
NEXTCLOUD_USERNAME = settings.NEXTCLOUD_USERNAME
NEXTCLOUD_PASSWORD = settings.NEXTCLOUD_PASSWORD
NEXTCLOUD_OCR_INPUT_DIR = settings.NEXTCLOUD_OCR_INPUT_DIR
NEXTCLOUD_OCR_OUTPUT_DIR = settings.NEXTCLOUD_OCR_OUTPUT_DIR
NEXTCLOUD_OCR_TAG = settings.NEXTCLOUD_OCR_TAG


def apply_threshold(img, argument):    
    switcher = {        
        cv2.threshold(cv2.GaussianBlur(img, (9, 9), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1], 
        cv2.threshold(cv2.GaussianBlur(img, (7, 7), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],  
        cv2.threshold(cv2.GaussianBlur(img, (5, 5), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],    
        cv2.adaptiveThreshold(cv2.medianBlur(img, 7), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2),
        cv2.adaptiveThreshold(cv2.medianBlur(img, 5), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2),
        cv2.adaptiveThreshold(cv2.medianBlur(img, 3), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)    
    }    
    return switcher.get(argument, "Invalid method")


def get_string(img_path, method):    
    # Read image using opencv    
    img = cv2.imread(img_path)    
    # Extract the file name without the file extension    
    file_name = os.path.basename(img_path).split('.')[0]    
    file_name = file_name.split()[0]    
    # Create a directory for outputs    
    temp_path = tempfile.mkdtemp()
    output_path = os.path.join(temp_path, file_name)    
    if not os.path.exists(output_path):        
        os.makedirs(output_path)

    # Rescale the image, if needed.    
    #img = cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)


    # Convert to gray    
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)    
    # Apply dilation and erosion to remove some noise    
    kernel = np.ones((1, 1), np.uint8)    
    img = cv2.dilate(img, kernel, iterations=1)    
    img = cv2.erode(img, kernel, iterations=1)

    # Apply threshold to get image with only black and white    
    #img = apply_threshold(img, method)
    #img = cv2.threshold(cv2.GaussianBlur(img, (3, 3), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


    # Save the filtered image in the output directory    
    save_path = os.path.join(output_path, file_name + "_filter_" + str(method) + ".jpg")    
    print(save_path)
    cv2.imwrite(save_path, img)    
    
    # Recognize text with tesseract for python    
    result = pytesseract.image_to_string(img, lang="deu")
    pdf = pytesseract.image_to_pdf_or_hocr(img, extension='pdf', lang="deu")
    with open(os.path.join(output_path, file_name + "_filter_" + str(method) + ".pdf") , 'w+b') as f:
        f.write(pdf) # pdf type is bytes by default
    pdf = pytesseract.image_to_pdf_or_hocr(img_path, extension='pdf', lang="deu")
    with open(os.path.join(output_path, file_name + "_filter_2.pdf") , 'w+b') as f:
        f.write(pdf) # pdf type is bytes by default


    return result


@router.post("/image2pdf", status_code=200, response_model=Ocr)
def image2pdf(*, image_id: int,) -> dict:
    """
    Convert Image to PDF
    """
    try:
        workdir = tempfile.mkdtemp(prefix="ocr_")
        with NextCloud(
                NEXTCLOUD_URL,
                user=NEXTCLOUD_USERNAME,
                password=NEXTCLOUD_PASSWORD,
                ) as nxc:
            nc_file_list = nxc.list_folders(NEXTCLOUD_OCR_INPUT_DIR).data
            my_filter_iter = filter(lambda x: x.file_id == image_id, nc_file_list)

            nc_file = next(my_filter_iter).href

            nc_file_remote_name = nc_file.replace(nc_file.split(NEXTCLOUD_OCR_INPUT_DIR)[0],"")
            nc_file_remote = nxc.get_file(nc_file_remote_name)

            nc_file_name, nc_file_ext = os.path.splitext(os.path.basename(nc_file))
            nc_file_remote.download(target=workdir)
            pdf = pytesseract.image_to_pdf_or_hocr(os.path.join(workdir, nc_file_name + nc_file_ext), extension='pdf', lang="deu")
            file_ocr_name = os.path.join(workdir, nc_file_name + "-" + str(image_id) + ".pdf")
            with open(file_ocr_name, 'w+b') as file_ocr:
                file_ocr.write(pdf)

            file_ocr_remote = NEXTCLOUD_OCR_OUTPUT_DIR + "/" + nc_file_name + "-" + str(image_id) + ".pdf"
            nxc.upload_file(file_ocr_name, file_ocr_remote).data

            nc_file_remote.add_tag(tag_name='ORC_DONE')
        shutil.rmtree(workdir)

        return {"image_id": image_id,"message": "successfully converted " + nc_file_remote_name + " to " + file_ocr_remote, "status": "OK"}
    except Exception as e:
        return {"image_id": image_id,"message": str(e), "status": "Failure"}