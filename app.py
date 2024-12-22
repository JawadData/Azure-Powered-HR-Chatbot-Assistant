from flask import  Flask, render_template ,request, jsonify , session
import os
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from azure.storage.blob import BlobServiceClient
from googleapiclient.discovery import build
import base64
from loguru import logger
import uuid

from modules.azure_data_lake_gen2 import Azure_Data_Lake_Gen2
from modules.job_candidate_matcher import result_with_llama
from modules.document_OCR import extract_information , resume_ocr

load_dotenv(override=True)

LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")

ACCOUNT_NAME = os.getenv("ACCOUNT_NAME")
ACCOUNT_KEY = os.getenv("ACCOUNT_KEY")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")

SCOPES = os.getenv("SCOPES")
print(f"the SCOPES:{SCOPES}")
print(f"the LLAMA_API_KEY:{LLAMA_API_KEY}")
print(f"the ACCOUNT_NAME:{ACCOUNT_NAME}")
print(f"the ACCOUNT_KEY:{ACCOUNT_KEY}")
print(f"the CONTAINER_NAME:{CONTAINER_NAME}")
input_file_path = "resumes.json"
output_file_path = "best_candidates.csv"

app = Flask(__name__)


def get_resume_from_email(SCOPES, subject):
    
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=8080)  
    
    service = build('gmail', 'v1', credentials=creds)

    query = f'subject:{subject}'
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    print(f"the message is:{messages}")
    if not messages:
        logger.info(f"No emails found with {subject} in the subject.")
        return
    
    logger.info(f"{len(messages)} emails found with {subject} in the subject.")
                        
    return service, messages



def best_condidate(candidates, offer):

    candidates_row = []
    for con in candidates:
        candidate = {
            "name": con.get('name', "Unknown"),
            "email": con.get('email', "Unknown"),
            "skills": con.get('skills', []),
            "experience": con.get('experience', "Unknown"),
            "certifications": con.get('certifications', []),
            "localisation": con.get('address', None), 
            "langues": con.get('langues', [])
        }

        score = result_with_llama(LLAMA_API_KEY, offer, candidate)
  
        candidate_row = {
            "Name": candidate["name"] or 'Unknown',
            "Email": candidate["email"] or 'Unknown' ,
            "Skills": ', '.join(str(item) for item in candidate["skills"] if isinstance(item, (str,))) if isinstance(candidate["skills"], list) else str(candidate["skills"]) or 'Unknown',
            "Experience": candidate["experience"] or 'Unknown',
            "Certifications": ', '.join(str(item) for item in candidate["certifications"] if isinstance(item, (str,))) if isinstance(candidate["certifications"], list) else str(candidate["certifications"]) or 'Unknown',
            "Localisation": candidate["localisation"] or 'Unknown',
            "Langues": ', '.join(str(item) for item in candidate["langues"] if isinstance(item, (str,))) if isinstance(candidate["langues"], list) else str(candidate["langues"]) or 'Unknown',
            "Score": score 
        }

        print(f"NOM : {candidate['name']} | EMAIL : {candidate['email']}| SKILLS : {candidate['skills']} | EXPERIENCE : {candidate['experience']} | CERTIFICATIONS : {candidate['certifications']} | LOCALISATION : {candidate['localisation']} | LANGUES : {candidate['langues']} | Score de compatibilité : {score}")

        candidates_row.append(candidate_row)

    return candidates_row


def highest_score(candidates, top_n = 5): return sorted(candidates, key=lambda x: x['Score'], reverse=True)[:top_n]


@app.route("/")
def index(): return render_template("index.html")


@app.route("/fetch-resumes", methods=["POST"])
def fetch_resumes():
    try:
        subject = request.json["subject"]
        print(f"The subject is: {subject}")

        azure_gen2 = Azure_Data_Lake_Gen2(ACCOUNT_NAME, ACCOUNT_KEY, CONTAINER_NAME)

        service, messages = get_resume_from_email(SCOPES, subject)
        logger.debug(f"Service returned: {service}")
        logger.debug(f"Service messages: {messages}")
        
        if not messages:
            print(f"No emails found with {subject} in the subject.")
            return {"message": f"Aucun email trouvé avec le sujet '{subject}'."}, 404

        print(f"{len(messages)} email(s) found with {subject} in the subject.")

        for msg in messages:
            msg_id = msg['id']
            message = service.users().messages().get(userId='me', id=msg_id).execute()

            payload = message.get('payload', {})
            parts = payload.get('parts', [])
    
            for part in parts:
                if part.get('filename'):  
                    attachment_id = part.get('body', {}).get('attachmentId')
                    if attachment_id:
                        attachment = service.users().messages().attachments().get(
                            userId='me', messageId=msg_id, id=attachment_id).execute()

                        file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
                        

                        if part['filename'].endswith('.pdf'):
                            unique_id = uuid.uuid4().hex[:8]
                            file_name_with_id = f"{unique_id}_{part['filename']}"
                            blob_name = os.path.join(subject, file_name_with_id).replace("\\", "/")

           
                            logger.info(f"Téléversement de {part['filename']} vers {blob_name}...")
                            azure_gen2.upload_to_container(file_data, blob_name)
                            logger.info(f"Fichier {part['filename']} téléversé avec succès.")

                            try:
                                file_data_in_memory = azure_gen2.read_from_container(blob_name)
                                print(file_data)
     
                                ocr_text = resume_ocr(file_path=file_data_in_memory, endpoint=os.getenv("ENDPOINT"), key=os.getenv("KEY"))

                                if not ocr_text:
                                    raise ValueError(f"L'OCR a échoué pour le fichier {blob_name}.")
                                    
                            except Exception as ocr_error:
                                logger.error(f"Erreur lors de l'OCR du fichier {blob_name}: {ocr_error}")
                                continue

                            json_data = extract_information(API_KEY=LLAMA_API_KEY, text=ocr_text)
                            azure_gen2.write_into_container(file_path="resumes_data.json", data=json_data)
                            logger.info(f"CV uploaded and saved in Azure Blob: {blob_name}")
                        else:
                            logger.info(f"File ignored (not a PDF): {part['filename']}")
        return {"message": "Téléversement terminé avec succès."}, 200
    except Exception as e:
        logger.error(f"Une erreur s'est produite : {e}")
        return {"message": f"Erreur interne : {str(e)}"}, 500









@app.route('/process-offer', methods=['POST'])
def process_offer():
    try:

        offer = request.json
        subject = session.get('subject')

        azure_gen2 = Azure_Data_Lake_Gen2(ACCOUNT_NAME, ACCOUNT_KEY, CONTAINER_NAME)

        input_file_path = os.path.join(subject, "resumes_data.json")

        candidates = azure_gen2.read_from_container(input_file_path)
        candidates = candidates[0:10]

        candidates_with_scores = best_condidate(candidates, offer)
        top_n_candidates = highest_score(candidates_with_scores)

        return jsonify({"top_candidates": top_n_candidates})
    
    except Exception as e:
        print(f"Error processing the offer: {str(e)}")
        return render_template('index.html', top_candidates="An error occurred while processing the offer")



if __name__ == "__main__":
    app.run(debug=True)