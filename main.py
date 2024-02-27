import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

from tercen.client import context as context
from tercen.model.impl import SimpleRelation, CompositeRelation, RenameRelation
from tercen.http.HttpClientService import decodeTSON

from pathlib import Path
import  base64, subprocess, string, random, os, shutil

from ppt_exporter import PPTXExporter
from docx_exporter import DOCXExporter
import tempfile

def get_simple_relation_id_list(obj):
    idList = []

    if isinstance(obj, SimpleRelation):
        idList.extend([obj.id])
    elif isinstance(obj, CompositeRelation):
        idList.extend(get_simple_relation_id_list(obj.mainRelation))
        idList.extend(get_simple_relation_id_list(obj.joinOperators))

    elif isinstance(obj, RenameRelation):
        cRel = obj.relation
        idList.extend(get_simple_relation_id_list(cRel.mainRelation))
        idList.extend(get_simple_relation_id_list(cRel.joinOperators))
    elif isinstance(obj, list):
        # Assumed: List of JoinOperator!
        for o in obj:
            idList.extend(get_simple_relation_id_list(o.rightRelation))

    return idList

def get_plot_schemas(ctx, steps ):
    schemas = {}
    for stp in steps:

        if hasattr(stp, "computedRelation"):
            relationIds = get_simple_relation_id_list(stp.computedRelation)
            for i in range(0, len(relationIds)):
                
                schema = ctx.context.client.tableSchemaService.get(relationIds[i])

                if any([c.name == ".content" for c in schema.columns]):
                    schemas[stp.name] = schema
    
    return schemas
def random_string(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

#docker run --net=host export_op --taskId=
# Save image/text file so the python-pptx can read it later
def table_to_file(ctx, schema, tmpFolder=None, force_png=False):
    for c in schema.columns:
        if "mimetype" in c.name:
            mimeColName = c.name

    nameColName = None
    for c in schema.columns:
        if "filename" in c.name:
            nameColName = c.name

    
    mimetypeTbl = decodeTSON(ctx.context.client.tableSchemaService.selectStream(schema.id, [mimeColName], 0, -1))
    ctt = ctx.context.client.tableSchemaService.selectStream(schema.id, [".content"], 0, -1)

    if not nameColName is None:
        filenameTbl = decodeTSON(ctx.context.client.tableSchemaService.selectStream(schema.id, [nameColName], 0, -1))
        filenames = filenameTbl["columns"][0]["values"]

    if tmpFolder is None:
        tmpFolder = tempfile.gettempdir() + "/"  + random_string()
        

    shutil.rmtree(tmpFolder)
    os.makedirs(tmpFolder )
    
    
    
    bytesTbls = decodeTSON(ctt)
    mimetypes = mimetypeTbl["columns"][0]["values"]
    
    fileInfos = []

    for i in range(0, schema.nRows):
        mimetype = mimetypes[i]
        filename = Path(filenames[i]).stem

        
        baseImgPath = tmpFolder + "/" + filename
        

        if mimetype == "image/svg+xml":
            saveImgPath = baseImgPath + ".svg"

            with open(saveImgPath, "wb") as file:
                file.write( base64.b64decode(bytesTbls["columns"][0]["values"][i])  )
            
            if force_png == False:
                outImgPath = tmpFolder + "/" + filename + ".emf"
                # This is only for 1.1, not available in vscode...
                #subprocess.call(["inkscape", saveImgPath, "--export-extension=org.inkscape.output.emf", "-o", outImgPath])
                #ENTRYPOINT [ "/home/root/inkscape/inkscape-1.1.x/build/bin/inkscape"]
#CMD [ "-export-extension", "org.inkscape.output.emf"]
                subprocess.call(["/home/root/inkscape/inkscape-1.1.x/build/bin/inkscape", \
                                 saveImgPath, "--export-extension=org.inkscape.output.emf", "-o", outImgPath])
                # subprocess.call(["/home/root/inkscape/inkscape-1.1.x/build/bin/inkscape", \
                                #  "--export-extension""-z" ,saveImgPath,  "-M", outImgPath])
                #subprocess.call(["cp", saveImgPath,  "test.svg"])

                
            else:
                outImgPath = tmpFolder + "/" + filename + ".png"
                # This is only for 1.1, not available in vscode...
                #subprocess.call(["inkscape", saveImgPath, "-o", outImgPath])
                subprocess.call(["inkscape", "-z" ,saveImgPath, "-d", "150", "-e", outImgPath])

            fileInfos.append([outImgPath, mimetype, filename])
       
        if mimetype == "image/png":
            saveImgPath = baseImgPath + ".png"

            with open(saveImgPath, "wb") as file:
                file.write( base64.b64decode(bytesTbls["columns"][0]["values"][i])  )

            fileInfos.append([saveImgPath, mimetype, filename])
        if mimetype == "text/markdown":
            saveFilePath = baseImgPath + ".txt"
            with open(saveFilePath, "wb") as file:
                file.write(base64.b64decode(bytesTbls["columns"][0]["values"][i]))

            fileInfos.append([saveFilePath, mimetype, filename])
    return fileInfos



#http://127.0.0.1:5400/test/w/fb58e9a6f4fe82c64066df20650d0794/ds/61358eb4-178d-49c0-b98c-26485b99c125
# tercenCtx = context.TercenContext(workflowId="fb58e9a6f4fe82c64066df20650d0794", stepId="61358eb4-178d-49c0-b98c-26485b99c125")
tercenCtx = context.TercenContext()



outputFormat = tercenCtx.operator_property('OutputFormat', typeFn=str, default="PowerPoint (*.pptx)")
# outputFormat = tercenCtx.operator_property('OutputFormat', typeFn=str, default="MS-Word (*.docx)")
# outputFormat = "MS-Word (*.docx)"
project = tercenCtx.context.client.projectService.get(tercenCtx.schema.projectId)
objs = tercenCtx.context.client.persistentService.getDependentObjects(project.id)


if hasattr(tercenCtx.context, "workflowId"):
    workflow = tercenCtx.context.client.workflowService.get(tercenCtx.context.workflowId)
else:
    task = tercenCtx.context.client.taskService.get(tercenCtx.task.id)

    workflowId = None
    for envPair in task.environment:
        if envPair.key == "workflow.id":
            workflowId = envPair.value

    workflow = tercenCtx.context.client.workflowService.get(workflowId)



tmpFolder = tempfile.gettempdir() + "/"  + workflow.id
if os.path.exists(tmpFolder):
    shutil.rmtree(tmpFolder)
os.makedirs(tmpFolder )

schemas = get_plot_schemas(tercenCtx, workflow.steps)


#
is_docx = False
if outputFormat == "PowerPoint (*.pptx)":
    expo = PPTXExporter(output="pptx", tmpFolder=tmpFolder)
elif outputFormat == "PDF - Slides (*.pdf)":
    expo = PPTXExporter(output="pdf", tmpFolder=tmpFolder)
elif outputFormat == "MS-Word (*.docx)":
    expo = DOCXExporter(output="docx", tmpFolder=tmpFolder)
    is_docx = True
else:
    raise ValueError("unsupported format")

for stpName,schema in schemas.items():
    fileInfo = table_to_file(tercenCtx, schema,  tmpFolder=tmpFolder, force_png=is_docx)
    
    for fi in fileInfo:
        
        if fi[1].startswith("image"):
            expo.add_blank_page(stpName=stpName)
            if not is_docx:
                expo.add_image(fi)
            if fi[2] != "Tercen_Plot":
                expo.add_title(stpName + " - " + fi[2])
            else:
                expo.add_title(stpName)

            if is_docx:
                expo.add_image(fi)

            expo.add_footer()

            expo.finish_page()

        if fi[1].startswith("text"):
            expo.add_blank_page(stpName=stpName)
            

            if not is_docx:
                expo.add_text(fi[0])
            if fi[2] != "Tercen_Plot":
                expo.add_title(stpName + " - " + fi[2])
            else:
                expo.add_title(stpName)
            if is_docx:
                expo.add_text(fi[0])

            expo.add_footer()

            expo.finish_page()



imgDf = expo.as_dataframe( tempfile.gettempdir() + "/"   + workflow.id + "/" + workflow.name + "_Report")


imgDf = tercenCtx.add_namespace(imgDf)
tercenCtx.save(imgDf)
