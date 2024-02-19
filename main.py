from tercen.client import context as context
from tercen.model.impl import SimpleRelation, CompositeRelation, RenameRelation, Workflow, CubeQueryTask
from tercen.http.HttpClientService import decodeTSON

from pathlib import Path
from pptx import Presentation

import  base64, subprocess, string, random, os, shutil


from exporter import PPTXExporter


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

def table_to_file(ctx, schema, tmpFolder=None):
    for c in schema.columns:
        if "mimetype" in c.name:
            mimeColName = c.name

    nameColName = None
    for c in schema.columns:
        if "filename" in c.name:
            nameColName = c.name

    
    mimetypeTbl = decodeTSON(ctx.context.client.tableSchemaService.selectStream(schema.id, [mimeColName], 0, -1))
    ctt =ctx.context.client.tableSchemaService.selectStream(schema.id, [".content"], 0, -1)

    if not nameColName is None:
        filenameTbl = decodeTSON(ctx.context.client.tableSchemaService.selectStream(schema.id, [nameColName], 0, -1))
        filenames = filenameTbl["columns"][0]["values"]

    if tmpFolder is None:
        tmpFolder = "/tmp/"  + random_string()
        os.makedirs(tmpFolder)
    
    schema.nRows
    
    bytesTbls = decodeTSON(ctt)
    mimetypes = mimetypeTbl["columns"][0]["values"]
    
    fileInfos = []

    for i in range(0, schema.nRows):
        mimetype = mimetypes[i]
        filename = Path(filenames[i]).stem

        
        baseImgPath = tmpFolder + "/" + filename
        
        

        # print(mimetype)

        if mimetype == "image/svg+xml":
            saveImgPath = baseImgPath + ".svg"

            with open(saveImgPath, "wb") as file:
                file.write( base64.b64decode(bytesTbls["columns"][0]["values"][i])  )
            
            outImgPath = filename + ".png"
            subprocess.call(["inkscape", "-z" ,saveImgPath, "-e", outImgPath])

            # im = Image.open(outImgPath)
            fileInfos.append([outImgPath, mimetype, filename])
            # return [outImgPath, im.size, mimetype]
        
        if mimetype == "image/png":
            saveImgPath = baseImgPath + ".png"

            with open(saveImgPath, "wb") as file:
                file.write( base64.b64decode(bytesTbls["columns"][0]["values"][i])  )

            fileInfos.append([saveImgPath, mimetype, filename])
            # im = Image.open(saveImgPath)
            # return [saveImgPath, im.size, mimetype]
        if mimetype == "text/markdown":
            saveFilePath = baseImgPath + ".txt"
            with open(saveFilePath, "wb") as file:
                file.write(base64.b64decode(bytesTbls["columns"][0]["values"][i]))

            fileInfos.append([saveFilePath, mimetype, filename])
            # return [saveFilePath,  mimetype]
    return fileInfos
    # return None




#310ae60ad93ec799406fcc2404141831/ds/785e21c9-acd7-4967-a37a-2dff81ce3cf3
# tercenCtx = context.TercenContext(workflowId="310ae60ad93ec799406fcc2404141831",\
                            # stepId="785e21c9-acd7-4967-a37a-2dff81ce3cf3")
tercenCtx = context.TercenContext()

outputFormat = tercenCtx.operator_property('OutputFormat', typeFn=str, default="PowerPoint (*.pptx)")

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



tmpFolder = "/tmp/"  + workflow.id
if os.path.exists(tmpFolder):
    shutil.rmtree(tmpFolder)
os.makedirs(tmpFolder )

schemas = get_plot_schemas(tercenCtx, workflow.steps)

if outputFormat == "PowerPoint (*.pptx)":
    expo = PPTXExporter(output="pptx", tmpFolder=tmpFolder)
elif outputFormat == "PDF - Slides (*.pdf)":
    expo = PPTXExporter(output="pdf", tmpFolder=tmpFolder)
else:
    raise ValueError("unsupported format")

for stpName,schema in schemas.items():
    fileInfo = table_to_file(tercenCtx, schema,  tmpFolder=tmpFolder)
    
    for fi in fileInfo:
        if fi[1].startswith("image"):
        # aspectRatio = imInfo[1][1]/imInfo[1][0]
            expo.add_blank_page(stpName=stpName)
            expo.add_image(fi)
            if fi[2] != "Tercen_Plot":
                expo.add_title(stpName + " - " + fi[2])
            else:
                expo.add_title(stpName)
            expo.add_footer()

        if fi[1].startswith("text"):
            expo.add_blank_page(stpName=stpName)
            

            expo.add_text(fi[0])
            if fi[2] != "Tercen_Plot":
                expo.add_title(stpName + " - " + fi[2])
            else:
                expo.add_title(stpName)
            expo.add_footer()



imgDf = expo.as_dataframe( "/tmp/"  + workflow.id + "/" + workflow.name + "_Report")


imgDf = tercenCtx.add_namespace(imgDf)
tercenCtx.save(imgDf)
