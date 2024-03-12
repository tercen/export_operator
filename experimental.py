import random, string, math, subprocess
# import numpy as np
import xml.etree.ElementTree as ET

import subprocess

def get_circle_info(circleElement):
    circleStyle = circleElement.attrib["style"]
    styleEls = circleStyle.split(";")

    

    circleInfo = {}

    for stEl in styleEls:
        keyVal = stEl.strip().split(":")
        if keyVal[0] == "fill":
            circleInfo["color"] = keyVal[1]


    circleInfo["x"] = float(circleElement.attrib["cx"])
    circleInfo["y"] = float(circleElement.attrib["cy"])
    circleInfo["r"] = float(circleElement.attrib["r"])

    return circleInfo

def almost_equal(x,y, tol=0.001):
    return abs(x-y) <= tol

def flatten(vec):
    out = []

    for v in vec:
        if not isinstance(v, list):
            out.append(v)
        else:
            out.extend(flatten(v))

    
    return out

def get_children(node, type="circle"):
    children = []
    if type in node.tag:
        return node
    else:
        for i in range(0, len(node)):
            children.append(get_children(node[i], type=type))
        
    return children


def optimize_svg(filepath, mode="bitmap auto"):
    # if mode is None:
    #     mode = "none"

    # mode.lower()
    tree = ET.parse(filepath)
    docRoot = tree.getroot()

    # STEP 1. Convert individual shapes to single path
    # Get all circles ...
    circles = flatten(get_children(docRoot, type="circle"))

    if circles is None or len(circles) == 0:
        return filepath
    
    if mode == "bitmap auto" and len(circles) > 1000:
        mode = "bitmap"
    else:
        mode = "none"

    intermediateFile1 = filepath.replace(".svg", "_clean.svg")

    # ... and save an image without them
    subprocess.check_output(["/home/root/inkscape/inkscape-1.3.2/build/bin/inkscape", filepath,\
                                    "--actions=select-by-element:circle;delete-selection;export-area-drawing;export-filename:{};export-do".format(intermediateFile1)])

    tree = ET.parse(intermediateFile1)
    docRoot = tree.getroot()

    keysBaseDict = {}

    # Rectangles without fill will be exported as black, so we fix that
    rects = flatten(get_children(docRoot, type="rect"))

    for rect in rects:
        if "style" in rect.attrib.keys():
            style = rect.attrib["style"]

            
            if not "fill" in style:
                print("ADDING FILL STYLE")
                style += ";fill:none"
                rect.attrib["style"] = style

    # Group circles by color and diameter
    for cEl in circles:
        info = get_circle_info(cEl)
        keyBase = "path{}{}".format(info["color"].split("#")[-1], str(info["r"]).split(".")[0])
        cEl.attrib["class"] = keyBase
        

        if not keyBase in keysBaseDict:
            keysBaseDict[keyBase] = [cEl]
        else:
            keysBaseDict[keyBase].append( cEl)
    

    # Create the path element for the group of scatter points
    for key, circleGroup in keysBaseDict.items():
        if len(circleGroup) > 1:
            groupElement = ET.Element("g")
            groupElement.attrib["id"] = "g{}".format(key)

            circleGroupElement = ET.SubElement(docRoot, "ns0:path")
            dString = ""

            prevX = 0
            prevY = 0
            bbs = []
            for c in circleGroup:
                circleInfo = get_circle_info(c)

                radius = circleInfo["r"]*1

                mX = circleInfo["x"] - (prevX)
                mY = circleInfo["y"] - (prevY)
                

                add = True
                
                if len(bbs) < 2:
                    add = True
                    bbs.append([  circleInfo["x"], circleInfo["y"], circleInfo["r"] ])    
                else:
                    dists = [ math.sqrt((bb[0]-circleInfo["x"])**2 + (bb[1]-circleInfo["y"])**2) < 0.1 for bb in bbs  ]  
                    bbs.append([  circleInfo["x"], circleInfo["y"], circleInfo["r"] ])    
                    if any(dists):
                        # excluded +=  1
                        add = False

                if add == True:                    
                    prevX = circleInfo["x"]
                    prevY = circleInfo["y"]
                    if dString == "":
                        dString = dString + "M {:.04},{:.04} A {:.04},{:.04} 0 0 1 {:.04},{:.04} {:.04},{:.04} 0 0 1 {:.04},{:.04} {:.04},{:.04} 0 0 1 {:.04},{:.04} {:.04},{:.04} 0 0 1 {:.04},{:.04} Z ".format(
                            mX + radius,mY, radius, radius,\
                            mX, mY + radius, radius, radius,\
                            mX - radius, mY, radius, radius,\
                            mX, mY - radius, radius, radius,\
                            mX + radius,mY
                            
                        )
                    else:
                        dString = dString + "m {:.04},{:.04} a {:.04},{:.04} 0 0 1 {:.04},{:.04} {:.04},{:.04} 0 0 1 {:.04},{:.04} {:.04},{:.04} 0 0 1 {:.04},{:.04} {:.04},{:.04} 0 0 1 {:.04},{:.04} z ".format(
                            mX, mY, radius, radius,\
                            -radius, radius, radius, radius,\
                            -radius, -radius, radius, radius,\
                            radius, -radius, radius, radius,\
                            radius,radius
                        
                    )

            attribDict = {"id":key,\
                "class":"class_{}".format(key),\
                "style":circleGroup[0].attrib["style"], \
                "d":dString}
            circleGroupElement.attrib = attribDict

        
    
    intermediateFile2 = filepath.replace(".svg", "_path.svg")
    outFile = filepath.replace(".svg", "_path_optimized.svg")
    tree.write(intermediateFile2)
    

    selection = ""
    print("Mode is {}".format(mode))

    mode = "bitmap"
    if mode=="bitmap":
        for key, val in keysBaseDict.items():
            # Select circles in group -: Make a bitmap copy -> select circles again -> delete them
            selection += "select-by-id:{};selection-make-bitmap-copy;select-clear;select-by-id:{};delete-selection;".format(key,key)
        

        actionCmd = "--actions={};export-filename:{};export-area-drawing;export-do;file-close".format(selection, outFile)
        subprocess.call(["/home/root/inkscape/inkscape-1.3.2/build/bin/inkscape", intermediateFile2,  \
                                    "--batch-process", actionCmd ])
        print("Exported {}".format(outFile))
    if mode=="simplify":
        for key, val in keysBaseDict.items():
            # Select circles in group -: Make a bitmap copy -> select circles again -> delete them
            selection += "select-by-id:{};path-simplify;".format(key)


        actionCmd = "--actions={}export-filename:{};export-plain-svg;export-area-drawing;export-do;file-close".format(selection, outFile)
        subprocess.call(["/home/root/inkscape/inkscape-1.3.2/build/bin/inkscape", intermediateFile2,  \
                                    "--batch-process", actionCmd ])

    if mode=="none":
        outFile = intermediateFile2

    
    
    
    return outFile


# #TODO MAKE THIS INTO the function!
# subprocess.call(["cp", "/out/Tercen_Plot.svg", "/out/Tercen_Plot_2.svg"])
# optimize_svg("/out/Tercen_Plot_2.svg", mode="bitmap auto")
# subprocess.call(["rm", "-rf","/out/test/"])
# subprocess.call(["mkdir", "/out/test/"])
# subprocess.call(["cp", "/out/test.pptx", "/out/test/test.zip"])
# subprocess.call(["unzip", "/out/test/test.zip", "-d", "/out/test/"])
# subprocess.call(["rm", "/out/test/test.zip"])
# subprocess.call(["cp", "/out/Tercen_Plot_2_path_optimized.svg", "/out/test/ppt/media/image5.svg"])
# subprocess.call(["/home/root/inkscape/inkscape-1.3.2/build/bin/inkscape", "/out/Tercen_Plot_2_path_optimized.svg",  \
#                                     "-o", "/out/image5_2.wmf" ])
# # subprocess.call(["rm", "/out/test/ppt/media/image5.wmf"])
# # subprocess.call(["rm", "/out/test/ppt/slides/_rels/slide6.xml.rels"])

# with open("/out/test/ppt/slides/_rels/slide5.xml.rels", "r") as file:
#     lines = file.readlines()


# txt_out = ""
# for line in lines:
#     if "image5.png" in line:
#         print("CHANGING!")
#         txt_out += line.replace("image5.png", "image5.svg")
#     else:
#         txt_out += line


# with open("/out/test/ppt/slides/_rels/slide5.xml.rels", "w") as file:
#     file.write(txt_out)
#     print(txt_out)

# import os
# wd = os.getcwd()
# os.chdir("/out/test/")
# subprocess.call(["zip", "-D","-r","test_out.zip", "."])
# os.chdir(wd)
# subprocess.call(["mv", "/out/test/test_out.zip", "/out/test_out.pptx"])







# optimize_svg("/out/Tercen_Plot_2.svg", mode="bitmap")

# subprocess.call(["/home/root/inkscape/inkscape-1.3.2/build/bin/inkscape", \
#                                  "/out/Tercen_Plot_2_path_optimized.svg", "-o", "/out/Tercen_Plot_2.emf"])