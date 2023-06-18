# --------------- SHARED -------------------------------------------
print(f"RUNNING: {__name__} ")
import sys
sys.path.append('.')  # Add the current directory to the sys path
sys.path.append('utils')  # Add the current directory to the sys path
from utils.omni_utils_misc import omni_get_env
from utils.omni_utils_http import CdnHandler, CdnResponse, ImageMeta, route_commands
routes_info = {}
# ------------------------------------------------------------------
from langchain.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import NLTKTextSplitter
from tqdm import tqdm
from fastapi import HTTPException
from utils.omni_chroma_memory import OmniChromaMemory

log = True
verbose = True
vectorstore_memories = {}

# ---------------------------------------------------
# --------------- VECTORSTORE INGEST ----------------
# ---------------------------------------------------
from Plugins.vectorstore_plugin.vectorstore_plugin import VectorstoreIngest_Input, VectorestoreIngest_Response, ENDPOINT_VECTORSTORE_INGEST

def init_chroma_memory(repo_name, create_if_empty):
    print(f"init_chroma_memory with Repo Name = {repo_name}")

    memory = OmniChromaMemory(
        chroma_db_impl="duckdb+parquet",
        repo_name=repo_name, 
        loader=UnstructuredFileLoader, 
        text_splitter=NLTKTextSplitter(chunk_size=2500), 
        create_if_empty=create_if_empty,
        max_words=2048)

    return memory        
    #

async def vectorstore_ingest(input_filename: str, repo_name: str):
    print(f"-------- vectorestore_ingest_Action : f={input_filename}")

    memory = init_chroma_memory(repo_name, True)        
    memory.ingest(input_filename)

async def integration_VectorstoreIngest_Post(input: VectorstoreIngest_Input):
    cdn= CdnHandler()
    if True: #try:
        cdn.announcement()
        print("------------- /vectorstore/ingest ------------------")
        print(f"input = {input}")


        input_cdns = input.documents
        repo_name = input.repo_name

        print(f"documents = {input_cdns}")
        print(f"repo_name = {repo_name}")
    
        if input_cdns is not None and len(input_cdns) > 0:
            suffix = ".txt"
            input_filenames = await cdn.download_files_from_cdn(input_cdns, suffix)
            print(f"input_filenames = {input_filenames}")
      
            for input_filename in input_filenames:
                await vectorstore_ingest(input_filename, repo_name)
            #
        #
      
        # DEBUG, now that we are done
        print("\n--------- now that we are done --------------\n")
        memory2 = init_chroma_memory(repo_name, False)        
        print(f"count = {memory2.chroma_collection.count()}")
        print("\n--------- was that what you expected? --------------\n")

        response = VectorestoreIngest_Response(success=True) 
        #print(f"response = {response}")
        #print("\n-----------------------\n")
        return response
    
    else: #except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
routes_info[ENDPOINT_VECTORSTORE_INGEST] = (VectorstoreIngest_Input, integration_VectorstoreIngest_Post)

# ---------------------------------------------------
# --------------- VECTORSTORE QUERY -----------------
# ---------------------------------------------------
async def vectorstore_query(query: str, repo_name: str, nb_of_answers:int):
    memory = init_chroma_memory(repo_name, False)  

    if verbose: print(f"Remembering about:\n{query}")

    #nb_of_answers = 5
    system_prompt = "You are a helpful assistant talented at finding relevant information among various source of information."
    system_prompt += "You work by reviewing raw information"
    system_prompt += "and then writing a quality summary of that raw information as is pertain to a specific query."
    system_prompt += "Do not use prior knowledge. Only what you see in the raw information"
    system_prompt += "If you found something relevant, it is important that your answer be a summary of the relevant information."
    system_prompt += "If you did not find something relevant, it is important that your answer just be '[no pertinent info]'"

    collection_answers = memory.get_matching_memories(query, nb_of_answers)
    answer = f"<no information in repo: {repo_name}>"
    total_cost = 0
    if collection_answers is not None and len(collection_answers) > 0:
        answer, total_cost = review_memories(collection_answers, query, system_prompt)

    return answer, total_cost

def review_memories(remembered_info_list, query, system_prompt):
    i = 0
    total_cost = 0
    combined_memories = ""

    print(type(remembered_info_list))
    print(f"testimony count: {len(remembered_info_list)}")
    answer = ""
    for remembered_info in tqdm(remembered_info_list, desc="Processing", ncols=80):
        i += 1
        summary = ""
        token_cost = 0
        # -------------------
        summary, token_cost = summarize(info = remembered_info, question=query, system_prompt=system_prompt)
        total_cost += token_cost
        memory_result = f"Testimony #{i}: {summary} \n"
        cprint(memory_result, "green")
        combined_memories += memory_result
        # -------------------
        print("-------------------------------------")
        print(memory_result)
    #
    if True:
        print(f"Results = {combined_memories}")
        model_name ="gpt-3.5-turbo"
        max_tokens =4096

        system_prompt = "You are an investigator trying to answer a question. You have access to a number of testimonies from different people."
        system_prompt += "Start by entirely discarding testimonies that have no information relevant ot the query or from people that did not to know the answer"
        system_prompt += "Once you have discarded the useless testimonies, consider all relevant information from the various testimonies, changing their wording only so that the final answer flows better."
        system_prompt += "Now think step by step to combine the various useful testimonies into your answer."
        system_prompt += "Do not mention the testimonies themselves. Do not say 'in testimony 1, it is said that ...', do not say 'discarding irrelevant testimonies, we are left with ...'"
        system_prompt += "Reply with a single answer that is highly relevant to the question and fuse as much details from the various testimonies as possible into a single answer."

        user_prompt = "The question is: "+ query + "\nThe following are the testimonies to review:\n"
        user_prompt += combined_memories

        print(f"system_prompt = {system_prompt}")
        print(f"user_prompt = {user_prompt}")

        answer, local_token_cost = query_llm(system_prompt, user_prompt, model_name, max_tokens, log, verbose)
        total_cost+= local_token_cost
        print("-------------------------------------")
        print(f"final_result =")
        cprint(answer)
        print(f"total_cost = {total_cost}")
        print("-------------------------------------")


    return answer, total_cost

from vectorstore_definitions import VectorstoreQuery_Input, VectorstoreQuery_Response, ENDPOINT_VECTORSTORE_QUERY
async def integration_VectorstoreQuery_Post(input: VectorstoreQuery_Input):
    cdn= CdnHandler()
    if True: #try:
        cdn.announcement()
        print("------------- /vectorstore/query ------------------")
        print(f"input = {input}")

        query = input.query
        repo_name = input.repo_name
        nb_of_answers = 5 #input.nb_of_answers

        print(f"query = {query}")
        print(f"repo_name = {repo_name}")

        answer, cost = await vectorstore_query(query, repo_name, nb_of_answers)
        print(f"\n---------\nQuery = {query}\nAnswer = {answer}\n--------")
        

        response = VectorstoreQuery_Response(answer=answer) 
        return response

    else: #except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
routes_info[ENDPOINT_VECTORSTORE_QUERY] = (VectorstoreQuery_Input, integration_VectorstoreQuery_Post)
# --------------- SHARED -------------------------------------------
if __name__ == '__main__':
    route_commands(routes_info, sys.argv)
# ------------------------------------------------------------------