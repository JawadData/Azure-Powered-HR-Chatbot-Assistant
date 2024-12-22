# Azure Libaries
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.storage.blob import BlobServiceClient

# LLM LLaMa Library 
from groq import Groq

# Other Libraries
from dotenv import load_dotenv
import json
import re
import os

# Load the .env file
load_dotenv()


def resume_ocr(file_path,endpoint,key):

    """ OCR function : using Document Intellignece API this function aims to extract text from resumes
    
    Parameters
    ----------
    text : str
            the text extracted from a pdf file using the ocr 

    Returns
    -------
    dict containing the features extracted
        
    """

    document_analysis_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )
    with open(file_path, "rb") as document:  
        poller = document_analysis_client.begin_analyze_document("prebuilt-document", document)
        result = poller.result()

    document_content = result.content
    return document_content


def extract_information(API_KEY,text:str):

    """ After applying the ocr on a pdf file extract_information aims to extract the main features : name, position, email, phone, address, linkedin, summary, skills, education, experience, projects, certifications, languages
    from the text using LlaMa

    Parameters
    ----------
    text : str
            the text extracted from the image using the ocr 

    Returns
    -------
    dict containing the features extracted
        
    """

    client = Groq(api_key=API_KEY)
    completion = client.chat.completions.create(
    model="llama3-70b-8192",
    messages=[
        {
            "role": "user",
            "content": f"""
                Extract the following information in a JSON format from this resume:
                {text}
                Information to extract: name, position, email, phone, address, linkedin, summary, skills, education, experience, projects, certifications, languages. 
                If any of these information are not found, replace them with None
                        """
       },
        {
            "role": "assistant",
            "content": ""
        }
    ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
    )
    
    full_output = ""
    for chunk in completion:
        output = chunk.choices[0].delta.content or ""
        full_output += output

    start_index = full_output.find("{")
    end_index = full_output.rfind("}") + 1
    json_string = full_output[start_index:end_index]

    # Convert the JSON string to a Python dictionary
    data = json.loads(json_string.replace("None", "null"))

    return data


