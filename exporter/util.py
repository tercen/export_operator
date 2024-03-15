import base64, tempfile, string, random, shutil, os, subprocess
from pathlib import Path
from tercen.http.HttpClientService import decodeTSON
from experimental import optimize_svg

from exporter.config import INKSCAPE


def random_string(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

# Save image/text file so the python-pptx can read it later
def table_to_file(ctx, schema, tmpFolder=None, force_png=False, svgOptimize="Bitmap Auto", labelPos="Ignore"):
    for c in schema.columns:
        if "mimetype" in c.name:
            mimeColName = c.name

    nameColName = None
    for c in schema.columns:
        if "filename" in c.name:
            nameColName = c.name
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # TODO Update API call to select file content [Replace block below]
    #fileContent = ctx.context.client.tableSchemaService.selectFileContentStream(schema.id, filenames[0])
    mimetypeTbl = decodeTSON(ctx.context.client.tableSchemaService.selectStream(schema.id, [mimeColName], 0, -1))
    ctt = ctx.context.client.tableSchemaService.selectStream(schema.id, [".content"], 0, -1)

    if not nameColName is None:
        filenameTbl = decodeTSON(ctx.context.client.tableSchemaService.selectStream(schema.id, [nameColName], 0, -1))
        filenames = filenameTbl["columns"][0]["values"]

    if tmpFolder is None:
        tmpFolder = tempfile.gettempdir() + "/"  + random_string()
        shutil.rmtree(tmpFolder)
        os.makedirs(tmpFolder)
    
    bytesTbls = decodeTSON(ctt)
    mimetypes = mimetypeTbl["columns"][0]["values"]
    # ENDOF TODO +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    fileInfos = []

    nRows = schema.nRows
    multifile = False
    if schema.nRows > 1:
        # Merge all with same name
        byteObjs = []
        fnames = [[filenames[0]]]

        currentFname = filenames[0]
        b =  base64.b64decode(bytesTbls["columns"][0]["values"][0])
        k = 1
        while k < len(filenames):
            if filenames[k] == currentFname:
                b = b + base64.b64decode(bytesTbls["columns"][0]["values"][k])
            else:
                currentFname = filenames[k]
                fnames.append([currentFname])
                byteObjs.append([b])
                b = base64.b64decode(bytesTbls["columns"][0]["values"][k])
            k = k + 1

        byteObjs.append([b])
        nRows = len(fnames)
        multifile = True

        


    for i in range(0, nRows):
        mimetype = mimetypes[i]
        if multifile == True:
            filename = Path(fnames[i][0]).stem
        else:
            filename = Path(filenames[i]).stem

        
        baseImgPath = tmpFolder + "/" + filename


        if mimetype == "image/svg+xml":
            saveImgPath = baseImgPath + ".svg"

            
            if multifile == True:
                with open(saveImgPath, "wb") as file:
                    file.write( byteObjs[i][0] )
            else:
                with open(saveImgPath, "wb") as file:
                    file.write( base64.b64decode(bytesTbls["columns"][0]["values"][i] ) )

            
            if force_png == False:
                # Optimizations to reduce SVG file size, otherwise large scatter plots may be untractable
                saveImgPath = optimize_svg(saveImgPath, mode=svgOptimize, labelPos=labelPos, context=ctx)

                # NOTE
                # python-pptx cannot add svg directly, thus a temporary WMF file is added
                # This file will be later replaced in the final PPT file
                outImgPath =  saveImgPath.replace(".svg", ".wmf") 

                subprocess.call([INKSCAPE, \
                                 saveImgPath, "-o", outImgPath])
            else:
                outImgPath = tmpFolder + "/" + filename + ".png"
                
                subprocess.call([INKSCAPE, \
                                 saveImgPath, "-d", "150", "-o", outImgPath])

            fileInfos.append([outImgPath, mimetype, filename])
       
        if mimetype == "image/png":
            saveImgPath = baseImgPath + ".png"

            if multifile == True:
                with open(saveImgPath, "wb") as file:
                    file.write( byteObjs[i][0] )
            else:
                with open(saveImgPath, "wb") as file:
                    file.write( base64.b64decode(bytesTbls["columns"][0]["values"][i] ) )

            fileInfos.append([saveImgPath, mimetype, filename])

        if mimetype == "image/jpg" or mimetype == "image/jpeg":
            saveImgPath = baseImgPath + ".jpg"

            if multifile == True:
                with open(saveImgPath, "wb") as file:
                    file.write( byteObjs[i][0] )
            else:
                with open(saveImgPath, "wb") as file:
                    file.write( base64.b64decode(bytesTbls["columns"][0]["values"][i] ) )

            fileInfos.append([saveImgPath, mimetype, filename])

        if mimetype == "text/markdown":
            saveFilePath = baseImgPath + ".txt"
            with open(saveFilePath, "wb") as file:
                file.write(base64.b64decode(bytesTbls["columns"][0]["values"][i]))

            fileInfos.append([saveFilePath, mimetype, filename])
    return fileInfos