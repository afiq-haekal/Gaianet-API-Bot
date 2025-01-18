import requests
import time
import random
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API URL, model, and Discord webhook from environment variables
API_URL = os.getenv("API_URL")
MODEL = os.getenv("MODEL")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_to_discord(title, content, color=None, footer=None):
    """
    Mengirim pesan ke Discord menggunakan embed
    
    Parameters:
    - title: Judul embed
    - content: Isi pesan
    - color: Warna embed (dalam format decimal)
    - footer: Teks footer (opsional)
    """
    try:
        embed = {
            "title": title,
            "description": content,
            "color": color or 3447003,  # Default blue color
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if footer:
            embed["footer"] = {"text": footer}
            
        payload = {
            "embeds": [embed]
        }
        
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("Pesan berhasil dikirim ke Discord")
    except Exception as e:
        print(f"Gagal mengirim pesan ke Discord: {e}")

def ask_question(question):
    url = API_URL
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful, respectful, and honest assistant. Always answer accurately, while being safe."},
            {"role": "user", "content": question}
        ],
        "model": MODEL
    }
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {response.content}")
    except Exception as err:
        print(f"Other error occurred: {err}")
    
    return None

def save_response_to_file(response, folder, index):
    try:
        # Extract the assistant's answer from the response
        answer = response['choices'][0]['message']['content']
        filename = os.path.join(folder, f"response_{index}.txt")
        with open(filename, 'w') as file:
            file.write(answer)
        print(f"Response saved to {filename}")
        
        # Kirim ke Discord dengan embed
        send_to_discord(
            title=f"Jawaban #{index}",
            content=answer,
            color=3066993,  # Green color
            footer=f"Saved to: {filename}"
        )
        
    except Exception as e:
        print(f"Failed to save response to file: {e}")

def read_initial_question(filename):
    try:
        with open(filename, 'r') as file:
            question = file.readline().strip()
        return question
    except Exception as e:
        print(f"Failed to read initial question from file: {e}")
        return None

def extract_question_from_response(response):
    try:
        answer = response['choices'][0]['message']['content']
        sentences = answer.split('.')
        if len(sentences) > 1:
            new_question = sentences[-2].strip() + '?'
        else:
            new_question = sentences[0].strip() + '?'
        return new_question
    except Exception as e:
        print(f"Failed to extract question from response: {e}")
        return None

def save_individual_question_to_file(question, folder, index):
    try:
        filename = os.path.join(folder, f"generated_question_{index}.txt")
        with open(filename, 'w') as file:
            file.write(question)
        print(f"Individual question saved to {filename}")
        
        # Kirim ke Discord dengan embed
        send_to_discord(
            title=f"Pertanyaan #{index}",
            content=question,
            color=15105570,  # Yellow color
            footer=f"Saved to: {filename}"
        )
        
    except Exception as e:
        print(f"Failed to save individual question to file: {e}")

if __name__ == "__main__":
    question = read_initial_question("questions.txt")
    if question:
        # Kirim pertanyaan awal ke Discord dengan embed
        send_to_discord(
            title="Pertanyaan Awal",
            content=question,
            color=15844367,  # Light blue color
            footer="Starting conversation..."
        )
        
        # Create a directory based on the current timestamp inside 'logs'
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        log_folder = "logs"
        os.makedirs(os.path.join(log_folder, timestamp), exist_ok=True)
        timestamp_folder = os.path.join(log_folder, timestamp)
        
        i = 0
        while True:
            response = ask_question(question)
            if response:
                save_response_to_file(response, timestamp_folder, i + 1)
                question = extract_question_from_response(response)
                if not question:
                    print("Failed to extract a new question from the response. Exiting loop.")
                    send_to_discord(
                        title="Proses Selesai",
                        content="Tidak dapat mengekstrak pertanyaan baru.",
                        color=15158332,  # Red color
                        footer="Process ended"
                    )
                    break
                i += 1
                save_individual_question_to_file(question, timestamp_folder, i)
            else:
                print(f"Failed to get a response for iteration {i}.")
                send_to_discord(
                    title="Proses Error",
                    content=f"Gagal mendapatkan respons pada iterasi {i}",
                    color=15158332,  # Red color
                    footer="Process failed"
                )
                break
            delay = random.randint(30, 60)
            print(f"Sleeping for {delay} seconds.")
            time.sleep(delay)
    else:
        print("No initial question to process.")
        send_to_discord(
            title="Error",
            content="Tidak ada pertanyaan awal untuk diproses.",
            color=15158332,  # Red color
            footer="Process failed to start"
        )