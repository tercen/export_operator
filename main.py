import os, sys
# os.environ['OPENBLAS_NUM_THREADS'] = '1'
# os.environ["OMP_NUM_THREADS"] = "1"
# os.environ["MKL_NUM_THREADS"] = "1"
# os.environ["NUMEXPR_NUM_THREADS"] = "1"

from tercen.client import context as context
from tercen.model.impl import SimpleRelation, CompositeRelation, RenameRelation

from tercen.util.helper_objects import ObjectTraverser
from tercen.util.helper_functions import get_temp_dir
import string, random, os, shutil

from exporter.ppt_exporter import PPTXExporter
from exporter.docx_exporter import DOCXExporter
from exporter.util import table_to_file




import numpy as np

def get_plot_schemas(ctx, steps ):
    schemas = {}
    for stp in steps:

        if hasattr(stp, "computedRelation"):
            traverser = ObjectTraverser()
            
            relationIds = np.unique( [rel.id for rel in traverser.traverse(stp.computedRelation, target=SimpleRelation)] )

            for i in range(0, len(relationIds)):
                schema = ctx.client.tableSchemaService.get(relationIds[i])

                if any([c.name == ".content" for c in schema.columns]):
                    stpName = stp.name
                    sk = 1
                    while stpName in schemas:
                        stpName = stp.name + "_" + str(sk)
                        sk += 1
                        
                    schemas[stpName] = schema
                    
    
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


#http://127.0.0.1:5400/test/w/05667561962b97ec1e693784fc0029f9/ds/9182c8f4-b047-446c-89da-dd9c13d8aaf9
tercenCtx = context.TercenContext()


outputFormat = tercenCtx.operator_property('OutputFormat', typeFn=str, default="MS-PowerPoint (*.pptx)")
svgOptimize = tercenCtx.operator_property('SVGOptimization', typeFn=str, default="Bitmap Auto")
labelPos = tercenCtx.operator_property('LabelPosition', typeFn=str, default="Right")

project = tercenCtx.client.projectService.get(tercenCtx.schema.projectId)


workflow = tercenCtx.client.workflowService.get( tercenCtx.get_workflow_id() )


tmpFolder = get_temp_dir(workflow.id)


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

expo.save(  workflow.name + "_Report")

# Only PPT needs this fix for editable SVGs
if isinstance(expo, PPTXExporter):
    expo.fix_svg_images(fixImgInfos)

imgDf = expo.as_dataframe( )
imgDf = tercenCtx.add_namespace(imgDf)


expo.clean_temp_files()

tercenCtx.save(imgDf)
