from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt
import datetime
from hashlib import md5
from base64 import b64encode

import polars as pl
from os.path import basename
import subprocess
import random, string, re


from PIL import Image


class Exporter:
    def __init__(self, tmpFolder=None):
        self.pages = []

        self.filename = None

        if tmpFolder is None:
            self.tmpFolder = "/tmp/" + ''.join(random.choice(string.ascii_letters) for _ in range(15))
        else: 
            self.tmpFolder = tmpFolder


    def add_blank_page(self):
        return -1
    
    def finish_page(self):
        pass

    # Image info is a list [imgPath, imgSize]
    def add_image(self, imgInfo, page_idx=0):
        pass

    def add_title(self, title, page_idx=0):
        pass

    def add_text(self, textFile, page_idx=0, text_size=11):
        pass

    def save(self, filename):
        pass 
    def as_dataframe(self ):
        return None

