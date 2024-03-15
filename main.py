import os, sys
# os.environ['OPENBLAS_NUM_THREADS'] = '1'
# os.environ["OMP_NUM_THREADS"] = "1"
# os.environ["MKL_NUM_THREADS"] = "1"
# os.environ["NUMEXPR_NUM_THREADS"] = "1"

from tercen.client import context as context
from tercen.model.impl import SimpleRelation, CompositeRelation, RenameRelation


import string, random, os, shutil

from exporter.ppt_exporter import PPTXExporter
from exporter.docx_exporter import DOCXExporter
from exporter.util import table_to_file

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


def parse_args() -> dict:
        workflowId = None
        stepId = None


        args = sys.argv
        nArgs = len(args)
        
        for i in range(1, nArgs):
            arg = args[i]
            
            if str.startswith(arg, '--'):
                #argParts = str.split(arg, ' ')
                argName = str.removeprefix(arg, '--')

                if argName == 'workflowId':
                    workflowId = args[i+1]
                
                if argName == 'stepId':
                    stepId = args[i+1]
                

        return {'workflowId':workflowId, 
                'stepId':stepId}


#http://127.0.0.1:5400/test/w/fea5edf39e43bb91ac6121c5a7030364/ds/61358eb4-178d-49c0-b98c-26485b99c125
tercenCtx = context.TercenContext()


outputFormat = tercenCtx.operator_property('OutputFormat', typeFn=str, default="MS-PowerPoint (*.pptx)")
svgOptimize = tercenCtx.operator_property('SVGOptimization', typeFn=str, default="Bitmap Auto")
labelPos = tercenCtx.operator_property('LabelPosition', typeFn=str, default="Right")

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

is_docx = False
if outputFormat == "MS-PowerPoint (*.pptx)":
    expo = PPTXExporter(output="pptx", tmpFolder=tmpFolder)
elif outputFormat == "PDF - Slides (*.pdf)":
    expo = PPTXExporter(output="pdf", tmpFolder=tmpFolder)
elif outputFormat == "MS-Word (*.docx)":
    expo = DOCXExporter(output="docx", tmpFolder=tmpFolder)
    is_docx = True
elif outputFormat == "PDF - A4 (*.pdf)":
    expo = DOCXExporter(output="pdf", tmpFolder=tmpFolder)
    is_docx = True
else:
    raise ValueError("unsupported format")


fixImgInfos = []
for stpName,schema in schemas.items():
    # Save tables as temporary image files
    fileInfo = table_to_file(tercenCtx, schema,  tmpFolder=tmpFolder, force_png=is_docx, svgOptimize=svgOptimize, labelPos=labelPos)
    
    for fi in fileInfo:

        if fi[1] == "image/svg+xml":
            fixImgInfos.append(fi)

        if fi[1].startswith("image"):
            expo.add_blank_page()

            if fi[2] != "Tercen_Plot":
                expo.add_title(stpName + " - " + fi[2])
            else:
                expo.add_title(stpName)

            expo.add_image(fi)
            expo.add_footer()

            expo.finish_page()

        if fi[1].startswith("text"):
            expo.add_blank_page()

            if fi[2] != "Tercen_Plot":
                expo.add_title(stpName + " - " + fi[2])
            else:
                expo.add_title(stpName)
            
            expo.add_text(fi[0])

            expo.add_footer()
            expo.finish_page()

expo.save( tempfile.gettempdir() + "/" + workflow.id + "/" + workflow.name + "_Report")

# Only PPT needs this fix for editable SVGs
if isinstance(expo, PPTXExporter):
    expo.fix_svg_images(fixImgInfos)

imgDf = expo.as_dataframe( )
imgDf = tercenCtx.add_namespace(imgDf)
tercenCtx.save(imgDf)
