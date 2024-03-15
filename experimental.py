import math, subprocess
import numpy as np
import xml.etree.ElementTree as ET

import subprocess
from exporter.config import INKSCAPE

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

def print_log(msg, context=None):
    if not context is None:
        context.log(msg)

def optimize_svg(filepath, mode="bitmap auto", labelPos="ignore", context=None):
    if mode is None:
        mode = "bitmap auto"

    mode = mode.lower()
    labelPos = labelPos.lower()


    print_log("Optimizing {} with mode {}".format(  filepath.split("/")[-1], mode ), context)

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
    subprocess.check_output([INKSCAPE, filepath,\
                    "--actions=select-by-element:circle;delete-selection;export-area-drawing;export-filename:{};export-do".format(intermediateFile1)])

    # Get the structure of the scatter plot without the dots
    tree = ET.parse(intermediateFile1)
    docRoot = tree.getroot()

    keysBaseDict = {}

    # Rectangles without fill will be exported as black, so we fix that
    rects = flatten(get_children(docRoot, type="rect"))

    # TODO Check if need to clean up
    for rect in rects:
        if "style" in rect.attrib.keys():
            style = rect.attrib["style"]

            if not "fill" in style:
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
    
    # Try to remove circles in the labels
    dictToAdd = {}
    for key, circleGroup in keysBaseDict.items():
        xVec = [float(c.attrib["x"]) for c in circleGroup]
        # REMOVE from group and create a new one jsut with this one circle
        remIdx = -1
        if labelPos == "right":
            remIdx = np.argmax(xVec) 
        elif labelPos == "left":
            remIdx = np.argmin(xVec) 

        if remIdx >= 0:
            el = circleGroup.pop(remIdx)
            dictToAdd[key + "_label"] = [el]
            
    for key, labelGroup in dictToAdd.items():
        keysBaseDict[key] = labelGroup


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
    print("Mode is {}, label position is {}".format(mode, labelPos))

    if mode=="bitmap":
        for key, val in keysBaseDict.items():
            # Select circles in group -: Make a bitmap copy -> select circles again -> delete them
            selection += "select-by-id:{};selection-make-bitmap-copy;select-clear;select-by-id:{};delete-selection;".format(key,key)
        

        actionCmd = "--actions={};export-filename:{};export-area-drawing;export-do;file-close".format(selection, outFile)
        subprocess.call([INKSCAPE, intermediateFile2,  \
                                    "--batch-process", actionCmd ])
    if mode=="simplify":
        for key, val in keysBaseDict.items():
            # Select circles in group -: Make a bitmap copy -> select circles again -> delete them
            selection += "select-by-id:{};path-simplify;".format(key)


        actionCmd = "--actions={}export-filename:{};export-plain-svg;export-area-drawing;export-do;file-close".format(selection, outFile)
        subprocess.call([INKSCAPE, intermediateFile2,  \
                                    "--batch-process", actionCmd ])

    if mode=="none":
        outFile = intermediateFile2

    
    
    
    return outFile

