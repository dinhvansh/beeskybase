from django.http import Http404,HttpResponseRedirect

TOOL_VERSION='0.40.0'

def download_tool(request,tool):
    names={'scanner':'BeeSkySetup','agent':'BeeSkyAgentSetup'}
    if tool not in names:raise Http404()
    response=HttpResponseRedirect('https://github.com/dinhvansh/beeskybase/releases/download/v'+TOOL_VERSION+'/'+names[tool]+'-'+TOOL_VERSION+'.exe')
    response['Cache-Control']='no-store'
    return response
