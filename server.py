from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import json
from utils import flatten_file, convert_pdf_to_image, extract_data_with_bedrock
import base64

# intializing app
app = Flask(__name__)
CORS(app)

# intializing logging
logging.basicConfig(
    filename="logs/app.log",        
    level=logging.INFO,             
    format="%(asctime)s - %(levelname)s - %(message)s", 
)

#load the json templete 


# helper
def error_response(message, code=400):
    return jsonify({"message": message}), code


# api's
@app.route("/file-upload", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            return jsonify({"message": "No file part"}), 400
        
        file = request.files['file']

        if file.filename == "":
            logging.error("No file present in the request body.")
            return error_response("No selected file")
        
        if file and file.filename.lower().endswith(".pdf"):
        
            #1: Flatten File
            flattened_pdf_base64 = flatten_file(file)
            if flattened_pdf_base64 is None:
                logging.error("Failed to flatten file.")
                return error_response("Couldn't process your PDF. Please try again.")
            
            #2: Convert Pdf to images
            image_pdf_bytes_list = convert_pdf_to_image(flattened_pdf_base64)
            if image_pdf_bytes_list is None:
                logging.error("Failed to convert pdf to images.")
                return error_response("Couldn't process your PDF. Please try again.")
            
            #3: Call Bedrock for Mapping
            print("bedrock started")
            response = extract_data_with_bedrock(image_pdf_bytes_list)
            print("bedrock ended")
            if response is None:
                logging.error("Failed to extract data.")
                return error_response("Couldn't process your PDF. Please try again.")
            
            return jsonify(response, 200)
        else:
            return error_response("Invalid file type. Only pdf allowed.")
    except Exception as e:
        print(str(e))
        return error_response("Unexpected error occurred while uploading and analysing. Please try again.")
    

if __name__ == "__main__":
    app.run(debug=True)