# from flask import Flask, request, jsonify
# from PIL import Image
# import io

# app = Flask(__name__)

# @app.route('/analyze-report/', methods=['POST'])
# def analyze_report():
#     image = request.files.get('image')
#     report_type = request.form.get('type')

#     if not image or not report_type:
#         return jsonify({'error': 'Image and report type are required'}), 400

#     try:
#         # Load image
#         img = Image.open(image.stream)
#         width, height = img.size

#         # Simulated ML response (Replace with real ML later)
#         mock_diagnosis = {
#             "X-ray": "Possible signs of mild pneumonia.",
#             "MRI": "No abnormalities detected in the brain scan.",
#             "Blood Report": "Slightly elevated white blood cell count.",
#             "CT Scan": "Minor lesion observed in left lung.",
#         }

#         result = mock_diagnosis.get(report_type, "No known issue detected.")
#         return jsonify({'result': f"{report_type} analyzed. Finding: {result}"}), 200

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# if __name__ == '__main__':
#     app.run(debug=True)

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import io
import os
from dotenv import load_dotenv
import google.generativeai as genai
import uvicorn
import json
# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

model = genai.GenerativeModel("gemini-1.5-flash")

def get_data(question: str, image: Image.Image):
    try:
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        image_bytes = buffered.getvalue()
        # Using generative AI to analyze the image + question
        response = model.generate_content([question, image])
        return response.text
    except Exception as e:
        return f"Error in get_data: {str(e)}"

@app.post("/analyze-report/")
async def analyze_report(
    report_type: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))

        # Customize prompt for medical analysis
        prompt = (
            f"Analyze the following medical report image of type '{report_type}'. "
            "Provide detailed diagnosis and suggested next steps for the patient."
            "Provide your response strictly in JSON format like this:\n"
            "{\n"
            '  "diagnosis": "...",\n'
            '  "next_steps": "...",\n'
            '  "recommendations": "..." \n'
            "}\n"
            "Do NOT include markdown symbols, bullets, or any extra text."
        )

        response = get_data(prompt, image)

        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            # fallback if AI fails to return proper JSON
            structured_result = {
                "diagnosis": response,
                "next_steps": "Not available",
                "recommendations": "Not available"
            }

        return JSONResponse(content={"result": result})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

