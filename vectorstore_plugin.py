# --------------- SHARED ---------------------------------------------------
import sys
from typing import List, Any
sys.path.append('.')  # Add the current directory to the sys path
sys.path.append('utils')  # Add the utils directory to the sys path

from utils.omni_utils_http import CdnResponse, ImageMeta, create_api_route, plugin_main, init_plugin
from pydantic import BaseModel
app, router = init_plugin()
# ---------------------------------------------------------------------------
plugin_module_name="Plugins.vectorstore_plugin.vectorstore"

# ---------------------------------------------------
# --------------- VECTORSTORE INGEST ----------------
# ---------------------------------------------------
ENDPOINT_VECTORSTORE_INGEST = "/vectorstore/ingest"

class VectorstoreIngest_Input(BaseModel):
    documents: List[CdnResponse]
    repo_name: str

    class Config:
        schema_extra = {
            "title": "Ingest document into a vectorstore"
        }

class VectorestoreIngest_Response(BaseModel):
    success: bool

    class Config:
        schema_extra = {
            "title": "Success flag"
        }

VectorstoreIngest_Post = create_api_route(
    app=app,
    router=router,
    context=__name__,
    endpoint=ENDPOINT_VECTORSTORE_INGEST,
    input_class=VectorstoreIngest_Input,
    response_class=VectorestoreIngest_Response,
    handle_post_function="integration_VectorstoreIngest_Post",
    plugin_module_name=plugin_module_name
)

# ---------------------------------------------------
# --------------- VECTORSTORE QUERY -----------------
# ---------------------------------------------------
ENDPOINT_VECTORSTORE_QUERY = "/vectorstore/query"

class VectorstoreQuery_Input(BaseModel):
    query: str
    repo_name: str
    
    class Config:
        schema_extra = {
            "title": "Query the vectorstore"
        }

class VectorstoreQuery_Response(BaseModel):
    answer: str

    class Config:
        schema_extra = {
            "title": "Answer to the query"
        }

VectorstoreQuery_Post = create_api_route(
    app=app,
    router=router,
    context=__name__,
    endpoint=ENDPOINT_VECTORSTORE_QUERY,
    input_class=VectorstoreQuery_Input,
    response_class=VectorstoreQuery_Response,
    handle_post_function="integration_VectorstoreQuery_Post",
    plugin_module_name=plugin_module_name
)

endpoints = [ENDPOINT_VECTORSTORE_INGEST, ENDPOINT_VECTORSTORE_QUERY]

# --------------- SHARED ---------------------------------------------------
plugin_main(app, __name__, __file__)
# --------------------------------------------------------------------------