import google.generativeai as genai
import json

gem_api ='AIzaSyCwnXTOjCHT3rttgv7jI-UoYr2J5GCLcJg'

def get_gemini_response(data, prompt):
    data_str = json.dumps(data, indent=4)    
    full_prompt = f"{prompt[0]}\n\nData Siswa:\n{data_str}"    
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content([full_prompt])
    return response.text

def run_task(data, prompt):
    response=get_gemini_response(data, prompt)
    return response

client = genai.configure(api_key=gem_api)

prompt = [
    """
    Tugas:
    berikan analisis dari data yang diberikan tentang kefokusan dan emosi siswa pada saat pembelajaran daring. 
    cukup jawab secara dominan dia fokus atau tidak, lalu dalam fokus tersebut sebutkan emosi dominannnya.
    juga berikan rekomendasi evaluasi tentang bagian materi mana yang harus diperbaiki oleh pengajar berdasarkan tingkat kefokusan dan emosi siswa tersebut.
    cukup jelaskan masing-masing dalam 1 paragraf saja. Jawaban jangan mengandung format-format bold atau miring.
    """
]

def analisis_gemini(file_json):
    JSON_PATH = f"emo_data/{file_json}"
    with open(JSON_PATH, 'r') as file:
        data = json.load(file)
    x = run_task(data, prompt)
    return x