import base64, tempfile, string, random, shutil, os, subprocess
from pathlib import Path
from tercen.http.HttpClientService import decodeTSON
from experimental import optimize_svg

from exporter.config import INKSCAPE
import numpy as np

def random_string(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def read_in_chunks(file_object, chunk_size=128 * 1024):
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data


# Save image/text file so the python-pptx can read it later
def table_to_file(ctx, schema, tmpFolder=None, force_png=False, svgOptimize="Bitmap Auto", labelPos="Ignore"):
    if tmpFolder is None:
        tmpFolder = tempfile.gettempdir() + "/"  + random_string()
        shutil.rmtree(tmpFolder)
        os.makedirs(tmpFolder)
    
    for c in schema.columns:
        if "mimetype" in c.name:
            mimeColName = c.name

    nameColName = None
    for c in schema.columns:
        if "filename" in c.name:
            nameColName = c.name
            
    mimetypes = decodeTSON(ctx.context.client.tableSchemaService.selectStream(schema.id, [mimeColName], 0, -1))['columns'][0]['values']
    filenames = np.unique(decodeTSON(ctx.context.client.tableSchemaService.selectStream(schema.id, [nameColName], 0, -1))['columns'][0]['values'])
    fileInfos = []
    
    for filename, mimetype in zip(filenames, mimetypes):
        baseImgPath = tmpFolder + "/" + Path(filename).stem
        
        
        fileContent = ctx.context.client.tableSchemaService.selectFileContentStream(schema.id, filename)
    
        if mimetype == "image/svg+xml":
            saveImgPath = baseImgPath + ".svg"
            with open(saveImgPath, "ab") as f:
                for chunk in read_in_chunks(fileContent):
                    f.write(chunk)
            
            if force_png == True:
                outImgPath = tmpFolder + "/" + filename + ".png"
                
                subprocess.call([INKSCAPE, \
                                 saveImgPath, "-d", "150", "-o", outImgPath])
            else:
                # Optimizations to reduce SVG file size, otherwise large scatter plots may be untractable
                saveImgPath = optimize_svg(saveImgPath, mode=svgOptimize, labelPos=labelPos, context=ctx)

                # NOTE
                # python-pptx cannot add svg directly, thus a temporary WMF file is added
                # This file will be later replaced in the final PPT file
                outImgPath =  saveImgPath.replace(".svg", ".wmf") 

                subprocess.call([INKSCAPE, \
                                 saveImgPath, "-o", outImgPath])
            
            saveFilePath = outImgPath
        else:
            if mimetype.startswith("image"):
                saveFilePath = baseImgPath + "." + mimetype.split("/")[1]  

            if mimetype == "text/markdown":
                saveFilePath = baseImgPath + ".txt"
                
            with open(saveFilePath, "ab") as f:
                for chunk in read_in_chunks(fileContent):
                    f.write(chunk)

            
        fileInfos.append([saveFilePath, mimetype, filename])
   
    return fileInfos


