# from fastapi import FastAPI, File, UploadFile, Form
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# from PIL import Image
# import io
# import os
# from dotenv import load_dotenv
# import google.generativeai as genai
# import uvicorn

# # Load environment variables
# load_dotenv()
# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Adjust as needed
#     allow_credentials=True,
#     allow_methods=["GET", "POST"],
#     allow_headers=["Content-Type", "Authorization"],
# )

# model = genai.GenerativeModel("gemini-1.5-flash-8b")

# def get_data(question: str, image: Image.Image):
#     try:
#         buffered = io.BytesIO()
#         image.save(buffered, format="PNG")
#         image_bytes = buffered.getvalue()
#         # Using generative AI to analyze the image + question
#         response = model.generate_content([question, image])
#         return response.text
#     except Exception as e:
#         return f"Error in get_data: {str(e)}"

# @app.post("/analyze-report/")
# async def analyze_report(
#     report_type: str = Form(...),
#     file: UploadFile = File(...)
# ):
#     try:
#         image_data = await file.read()
#         image = Image.open(io.BytesIO(image_data))

#         # Customize prompt for medical analysis
#         prompt = (
#             f"Analyze the following medical report image of type '{report_type}'. "
#             "Provide detailed diagnosis and suggested next steps for the patient."
#         )

#         response = get_data(prompt, image)

#         return JSONResponse(content={"result": response})

#     except Exception as e:
#         return JSONResponse(content={"error": str(e)}, status_code=500)

# if __name__ == "__main__":
#     port = int(os.getenv("PORT", 8000))
#     uvicorn.run(app, host="0.0.0.0", port=port)

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import io
import os
from dotenv import load_dotenv
import google.generativeai as genai
import uvicorn

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# ✅ Auto-select the first working Gemini model supporting generateContent
def get_gemini_model():
    try:
        models = genai.list_models()
        for m in models:
            if "generateContent" in m.supported_generation_methods:
                print(f"✅ Using model: {m.name}")
                return genai.GenerativeModel(m.name)
        raise Exception("No supported Gemini model found.")
    except Exception as e:
        print(f"❌ Model fetch error: {str(e)}")
        # Fallback to known working model (if available)
        return genai.GenerativeModel("gemini-2.0-flash")

# Load model dynamically
model = get_gemini_model()


def get_data(question: str, image: Image.Image):
    try:
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        image_bytes = buffered.getvalue()

        # Use Gemini to analyze the image + question
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

        # Construct medical prompt
        prompt = (
            f"Analyze the following medical report image of type '{report_type}'. "
            "Provide a possible diagnosis, findings, and suggested next steps for the patient."
        )

        response = get_data(prompt, image)
        return JSONResponse(content={"result": response})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)


