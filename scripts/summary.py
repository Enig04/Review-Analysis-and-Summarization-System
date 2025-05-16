import requests
import fitz  # PyMuPDF
import json

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text("text") for page in doc)
    return text

def run_summary(pdf_file="data/real_reviews.pdf"):
    file_content = extract_text_from_pdf(pdf_file)

    ollama_url =  "http://ADD-YOUR-LOCALHOST-IP-HERE/api/generate"
    ollama_model = "deepseek-llm:7b"
    
    try:
        response = requests.post(
            ollama_url,
            json={
                "model": ollama_model,
                "prompt": (
                    "Summarize these reviews into a single paragraph, "
                    "highlighting the pros and cons of the product:\n\n" + file_content
                )
            },
            stream=True
        )
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return "Summary generation failed due to request error."

    full_response = ""
    for line in response.iter_lines():
        if line:
            try:
                json_line = json.loads(line)
                full_response += json_line.get("response", "")
            except json.JSONDecodeError:
                continue

    return full_response.strip()
