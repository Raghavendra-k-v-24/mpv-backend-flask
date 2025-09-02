import os
import boto3
from dotenv import load_dotenv
import requests
import io
import json
import re
import base64
from pdf2image import convert_from_bytes
from io import BytesIO
from botocore.config import Config

# load .env file 
load_dotenv()

config = Config(
    read_timeout=300,  # 5 minutes
    connect_timeout=60,  # 1 minute
    retries={
        'max_attempts': 3,
        'mode': 'adaptive'
    }
)

client = boto3.client("bedrock-runtime", config=config)

with open("template.json", "r") as f:
  template =  json.load(f)

def flatten_file(file: object) -> str:
    try:
        file_bytes = file.read()
        file_base64 = base64.b64encode(file_bytes).decode("utf-8")
        response = requests.post( "http://localhost:3000/flatten-file",
                    json={"file_base64": file_base64}
                    )
        if response.status_code == 200:
            data = response.json()
            flattened_pdf_base64 = data['flattened_pdfbytes_base64']
            return flattened_pdf_base64
        return None
    except Exception as e:
        print(f"[ERROR] Failed to flatten file: {str(e)}")
        return None
 
def convert_pdf_to_image(pdf_base64: str) -> list:
    try:
        flattened_pdf_bytes = base64.b64decode(pdf_base64)
        images = convert_from_bytes(
                    flattened_pdf_bytes,
                    # first_page=1,
                    # last_page=1,
                    poppler_path=r"C:\Users\ragha\Downloads\Release-25.07.0-0\poppler-25.07.0\Library\bin",
                    use_pdftocairo = True
                )
        buffers =[]
        for i, img in enumerate(images, start=1):
            buf = BytesIO()
            img.save(buf, format="PNG")
            buffers.append(buf)
        all_pages_bytes= [b.getvalue() for b in buffers]
        return all_pages_bytes
    except Exception as e:
        print(f"[ERROR] Failed to convert pdf to image: {str(e)}")
        return None

def remove_duplicates(obj):
    if isinstance(obj, dict):
        clean = {}
        for k, v in obj.items():
            clean[k] = remove_duplicates(v)  # overwrite if duplicate key
        return clean
    elif isinstance(obj, list):
        return [remove_duplicates(i) for i in obj]
    else:
        return obj
    
def extract_data_with_bedrock(image_pdf_bytes_list: list) -> json:
    try:
        messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                            'image':{
                                'format':'png',
                                'source':{
                                'bytes':image_pdf_bytes_list[0]
                                }
                            }
                            },
                            {
                            'image':{
                                'format':'png',
                                'source':{
                                'bytes':image_pdf_bytes_list[1]
                                }
                            }
                            },
                            {
                            'image':{
                                'format':'png',
                                'source':{
                                'bytes':image_pdf_bytes_list[2]
                                }
                            }
                            },
                            {
                            'image':{
                                'format':'png',
                                'source':{
                                'bytes':image_pdf_bytes_list[3]
                                }
                            }
                            },
                            {
                            'image':{
                                'format':'png',
                                'source':{
                                'bytes':image_pdf_bytes_list[4]
                                }
                            }
                            },
                            {
                            'image':{
                                'format':'png',
                                'source':{
                                'bytes':image_pdf_bytes_list[5]
                                }
                            }
                            },
                            {
                            'image':{
                                'format':'png',
                                'source':{
                                'bytes':image_pdf_bytes_list[6]
                                }
                            }
                            },
                            {
                            'image':{
                                'format':'png',
                                'source':{
                                'bytes':image_pdf_bytes_list[7]
                                }
                            }
                            },
                            {
                            'image':{
                                'format':'png',
                                'source':{
                                'bytes':image_pdf_bytes_list[8]
                                }
                            }
                            },
                            {
                                "text": f"""
                Here is a 1003 loan form (image above).

                Map it into this JSON template.

                STRICT RULES:
                - Fill values only from the image.
                - If a field is missing, keep it as an empty string "".
                - Instruction for Checkbox Handling:
                    a. For every checkbox labeled "Does not apply", do not interpret its meaning and determine whether it is checked or not.
                    b. If the checkbox is checked, set the corresponding field in the output template to true.
                    c. If the checkbox is not checked, set the corresponding field in the output template to false.
                - Instruction for Radio Buttons and Checkboxes
                    a. Determine the selected option only by looking at which circle is filled (●) or which box is checked (☑).
                    b. Do not infer the answer from text fields or filled numbers if the circle/box is not marked.
                    Example:
                        1. If “No primary housing expense” has a filled circle (●), then that is the selected option, regardless of any numbers written in the “Rent” field.
                        2. If “Rent” has a filled circle, then “Rent” is the selected option, and the monthly rent value should be extracted from the text box.
                        3. If “Own” has a filled circle, then “Own” is the selected option.
                - Return ONLY valid JSON, no explanations.

                TEMPLATE:
                {json.dumps(template, indent=2)}
                                """
                            }
                        ]
                    }
                ]
        response = client.converse(
                modelId="us.anthropic.claude-sonnet-4-20250514-v1:0",
                messages=messages,
            )
        output = response['output']['message']['content'][0]['text']
        cleaned = output.replace('```json','').replace('```','')
        try:
            parsed = json.loads(cleaned)
            deduped = remove_duplicates(parsed)
        except json.JSONDecodeError as e:
            print("JSON parse failed:", e)
            deduped = json.loads(cleaned)
        return deduped
    except Exception as e:
        print(f"[ERROR] Failed to extract data using bedrock: {str(e)}")
        return None