from tercen.client import context as context
from tercen.model.impl import SimpleRelation, CompositeRelation, RenameRelation, Workflow, ImportWorkflowTask
from tercen.http.HttpClientService import decodeTSON


from pptx import Presentation


from PIL import Image

import  base64, subprocess, string, random, os, shutil
# import time

from exporter import PPTXExporter
#http://127.0.0.1:5400/test/w/310ae60ad93ec799406fcc2404141831/ds/785e21c9-acd7-4967-a37a-2dff81ce3cf3

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
                if any([c.name == ".content" for c in schema.columns]) and any([c.name == "mimetype" for c in schema.columns]):
                    schemas[stp.name] = schema
    
    return schemas
def random_string(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def table_to_file(ctx, schema, tmpFolder=None):
    mimetypeTbl = decodeTSON(ctx.context.client.tableSchemaService.selectStream(schema.id, ["mimetype"], 0, -1))
    ctt =ctx.context.client.tableSchemaService.selectStream(schema.id, [".content"], 0, -1)

    
    bytesTbl = decodeTSON(ctt)
    mimetype = mimetypeTbl["columns"][0]["values"][0]

    if tmpFolder is None:
        tmpFolder = "/tmp/"  + random_string()
        os.makedirs(tmpFolder)
    
    baseImgPath = tmpFolder + "/" + random_string()
    
    outImgPath = baseImgPath + ".png"

    print(mimetype)

    if mimetype == "image/svg+xml":
        saveImgPath = baseImgPath + ".svg"

        with open(saveImgPath, "wb") as file:
            file.write( base64.b64decode(bytesTbl["columns"][0]["values"][0])  )
        

        subprocess.call(["inkscape", "-z" ,saveImgPath, "-e", outImgPath])

        im = Image.open(outImgPath)
        return [outImgPath, im.size, mimetype]
    
    if mimetype == "image/png":
        saveImgPath = baseImgPath + ".png"

        with open(saveImgPath, "wb") as file:
            file.write( base64.b64decode(bytesTbl["columns"][0]["values"][0])  )

        im = Image.open(saveImgPath)
        return [saveImgPath, im.size, mimetype]
    if mimetype == "text/markdown":
        saveFilePath = baseImgPath + ".txt"
        with open(saveFilePath, "wb") as file:
            file.write(base64.b64decode(bytesTbl["columns"][0]["values"][0]))

        return [saveFilePath, None, mimetype]

    return None




#310ae60ad93ec799406fcc2404141831/ds/785e21c9-acd7-4967-a37a-2dff81ce3cf3
# tercenCtx = context.TercenContext(workflowId="310ae60ad93ec799406fcc2404141831",\
                            # stepId="785e21c9-acd7-4967-a37a-2dff81ce3cf3")
tercenCtx = context.TercenContext()
outputFormat = tercenCtx.operator_property('OutputFormat', typeFn=str, default="PowerPoint (*.pptx)")

#tercenCtx.schema.projectId
project = tercenCtx.context.client.projectService.get(tercenCtx.schema.projectId)
objs = tercenCtx.context.client.persistentService.getDependentObjects(project.id)


workflows = []
for o in objs:
    if isinstance(o, Workflow):
        workflows.append(o)

workflow = tercenCtx.context.client.workflowService.get(workflows[0].id)




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
    
    if fileInfo[2].startswith("image"):
    # aspectRatio = imInfo[1][1]/imInfo[1][0]
        expo.add_blank_page(stpName=stpName)
        expo.add_image(fileInfo)
        expo.add_title(stpName)
        expo.add_footer()

    if fileInfo[2].startswith("text"):
        expo.add_blank_page(stpName=stpName)
        expo.add_text(fileInfo[0])
        expo.add_title(stpName)
        expo.add_footer()



imgDf = expo.as_dataframe( "/tmp/"  + workflow.id + "/" + workflow.name + "_Report")


imgDf = tercenCtx.add_namespace(imgDf)
tercenCtx.save(imgDf)
