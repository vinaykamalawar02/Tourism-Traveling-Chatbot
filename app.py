from flask import Flask, render_template, request, jsonify, send_file, make_response
import google.generativeai as genai
import speech_recognition as sr
from dotenv import load_dotenv
import os
import re
import wikipediaapi
from gtts import gTTS
import tempfile
import sys
import traceback
import pyttsx3

# Load environment variables
load_dotenv()

# Retrieve API key securely from environment variable
api_key = os.getenv("GEMINI_API_KEY")

# Initialize Flask app
app = Flask(__name__)

# Configure API key for Generative AI
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# Initialize speech recognition
recognizer = sr.Recognizer()

# Try to initialize pyttsx3 with error handling
try:
    engine = pyttsx3.init()
    # Set properties if needed
    engine.setProperty('rate', 150)  # Speed of speech
    engine.setProperty('volume', 0.9)  # Volume level
except Exception as e:
    print(f"Error initializing TTS engine: {str(e)}")
    engine = None

# Initialize Wikipedia API
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    user_agent='TourismChatbot/1.0 (bindubhavani113@gmail.com)'
)

def extract_trip_details(user_input):
    # Regular expressions to extract budget, city, and days
    budget_pattern = r"\b(\d+)\s*(lakh|lac|crore|INR|rs|rupees)?\b"
    city_pattern = r"\b(?:to|in|visit|go to|travel to)\s+([A-Za-z]+)\b"
    days_pattern = r"\b(\d+)\s*(?:days?|nights?)\b"

    # Extract budget
    budget_match = re.search(budget_pattern, user_input, re.IGNORECASE)
    if budget_match:
        budget = int(budget_match.group(1))
        unit = budget_match.group(2).lower() if budget_match.group(2) else None

        # Convert lakh/crore to INR
        if unit in ["lakh", "lac"]:
            budget *= 100000
        elif unit == "crore":
            budget *= 10000000
    else:
        budget = None

    # Extract city
    city_match = re.search(city_pattern, user_input, re.IGNORECASE)
    city = city_match.group(1).strip() if city_match else None

    # Extract days
    days_match = re.search(days_pattern, user_input, re.IGNORECASE)
    days = int(days_match.group(1)) if days_match else None

    return {
        "budget": budget,
        "city": city,
        "days": days
    }

def fetch_wikipedia_data(place_name):
    page = wiki_wiki.page(place_name)
    if page.exists():
        return page.summary
    return "No information found."

def generate_tripadvisor_link(destination):
    query = f"{destination} hotels".replace(" ", "+")
    return f"https://www.tripadvisor.com/Search?q={query}"

def generate_trip_plan(destination, days, budget):
    wiki_summary = fetch_wikipedia_data(destination)
    tripadvisor_url = generate_tripadvisor_link(destination)

    final_prompt = f"""
    Plan a {days}-day trip to {destination} (a city in India) with a budget of {budget} INR.

    Wikipedia Summary:
    {wiki_summary}

    Requirements:
    1. Highly Rated and Famous Places:
       • Include only the most famous, highly rated, and most visited tourist places in {destination}.
       • Avoid less-known or low-rated places.
    2. Complete Daily Schedule:
       • Provide a detailed schedule for each day, including timings, entry fees, food, shopping, transportation, and traffic tips.
       • Ensure no place is revisited, and each day has unique places.
    3. Evening Activities:
       • Include unique and fun evening activities (e.g., sunset spots, night markets, cultural shows).
    4. Meal Plans:
       • Include specific recommendations for breakfast, lunch, and dinner for each day.
       • Suggest local dishes and restaurants that fit within the budget.
       • Allocate extra money for food since the user's eating habits are unknown.
    5. Additional Recommendations:
       • After scheduling all days, provide additional recommendations for parks, gardens, temples, caves, beaches, malls, forts, palaces, museums, etc.
    6. Last Day:
       • Do not allocate the last day for departure or relaxation. Include new tourist places even on the last day.
    7. Accommodation:
       • Suggest hotels/lodges under the allotted budget with approximate prices.
       • Include this EXACT line at the end of the accommodation section:
         "🔍 <a href='{tripadvisor_url}' target='_blank' style='text-decoration: none; color: #0066cc; font-weight: 600;'>Find hotels in {destination} on Tripadvisor</a>"
       • If the next day's places are far, suggest changing accommodations accordingly.
    8. Budget Warnings:
       • If the budget is too low for the number of days, politely inform the user and suggest adjustments.
    9. Add a "Travel Tips" section at the end with 3-5 practical tips for the trip.

    Format (use • for all bullets, NOT *):
    Day 1:
    • Places to Visit:
      1. Place 1 (Timings: 9 AM - 12 PM)
         • Famous for: [Description]
         • Entry Fee: [Exact price or "Don't know"]
         • Food: [Famous dishes/snacks]
         • Shopping: [Nearby shopping areas]
         • Nearby Attractions: [Suggestions]
         • Transportation: [Options]
         • Traffic Tips: [Suggestions to avoid traffic]
      2. Place 2 (Timings: 1 PM - 5 PM)
         • Famous for: [Description]
         • Entry Fee: [Exact price or "Don't know"]
         • Food: [Famous dishes/snacks]
         • Shopping: [Nearby shopping areas]
         • Nearby Attractions: [Suggestions]
         • Transportation: [Options]
         • Traffic Tips: [Suggestions to avoid traffic]
    • Evening Activity:
      • [Description of evening activity, e.g., sunset spot, night market, cultural show]
    • Meal Plans:
      • Breakfast: [Recommendation]
      • Lunch: [Recommendation]
      • Dinner: [Recommendation]
    • Unique Experience:
      • [Description of a unique or offbeat experience]
    • Local Festival or Event:
      • [Description of a local festival or event, if applicable]
    • Hidden Gem:
      • [Description of a hidden gem]
    • Cultural Insight:
      • [Cultural insight related to the destination]
    • Interactive Element:
      • [Interactive question or poll to tailor the itinerary]
    Travel Tips:
    • Tip 1: [Practical advice, e.g., "Carry cash for beach shacks"]
    • Tip 2: [Safety/cultural tip, e.g., "Dress modestly in temples"]
    • Tip 3: [Transport tip, e.g., "Rent a scooter for flexibility"]

    Repeat this structure for all {days} days, ensuring no place is revisited and each day has unique activities.
    """

    response = model.generate_content(final_prompt)
    plan_text = response.text.strip()
    return plan_text

@app.route('/')
def index():
    return render_template('interface.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/voicebot')
def voicebot():
    return render_template('speech.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json.get("message", "").strip()
        is_speech = request.json.get("is_speech", False)
        step = request.json.get("step", "ask_destination")
        destination = request.json.get("destination", "")
        days = request.json.get("days", 0)
        budget = request.json.get("budget", 0)

        print(f"Current step: {step}, Destination: {destination}, Days: {days}, Budget: {budget}")
        print(f"User input: {user_input}")

        if step == "ask_destination":
            return jsonify({
                "message": f"How many days do you plan to spend in {user_input}?",
                "step": "ask_days",
                "destination": user_input
            })

        if step == "ask_days":
            try:
                days = int(user_input)
                if days <= 0 or days > 30:
                    return jsonify({
                        "message": "Please provide a valid number of days between 1 and 30.",
                        "step": "ask_days",
                        "destination": destination,
                        "days": 0,
                        "budget": 0
                    })
            except ValueError:
                return jsonify({
                    "message": "Please enter a valid number of days (e.g., '3 days' or 'three days').",
                    "step": "ask_days",
                    "destination": destination,
                    "days": 0,
                    "budget": 0
                })

            return jsonify({
                "message": "What is your budget? (Enter a number in INR)",
                "step": "ask_budget",
                "destination": destination,
                "days": days
            })

        if step == "ask_budget":
            try:
                budget = int(user_input)
                if budget <= 0:
                    return jsonify({
                        "message": "Please provide a valid budget amount greater than zero.",
                        "step": "ask_budget",
                        "destination": destination,
                        "days": days,
                        "budget": 0
                    })

                if budget < days * 2000:
                    return jsonify({
                        "message": f"Your budget of {budget} INR for {days} days is quite low. It may be difficult to cover all expenses (accommodation, food, transportation, and entry fees). Would you like to adjust your budget or reduce the number of days?",
                        "step": "ask_budget"
                    })

                trip_plan = generate_trip_plan(destination, days, budget)
                return jsonify({
                    "message": trip_plan,
                    "step": "trip_complete",
                    "destination": destination,
                    "days": days,
                    "budget": budget
                })
            except ValueError:
                return jsonify({
                    "message": "Please enter a valid budget amount (e.g., '5000 INR' or 'five thousand rupees').",
                    "step": "ask_budget",
                    "destination": destination,
                    "days": days,
                    "budget": 0
                })

        if step == "trip_complete" and user_input.lower() in ["ok", "thank you", "thanks"]:
            return jsonify({
                "message": "You're welcome! Would you like to plan another trip? (Yes/No)",
                "step": "ask_another_trip"
            })

        if step == "ask_another_trip":
            if user_input.lower() in ["yes", "y"]:
                return jsonify({
                    "message": "Great! Which city are you planning to visit?",
                    "step": "ask_destination",
                    "destination": "",
                    "days": 0,
                    "budget": 0
                })
            elif user_input.lower() in ["no", "n"]:
                return jsonify({
                    "message": "Thank you for using the tourism chatbot. Have a great day!",
                    "step": "end_conversation"
                })
            else:
                return jsonify({
                    "message": "Please respond with 'Yes' or 'No'.",
                    "step": "ask_another_trip"
                })

        return jsonify({"message": "I couldn't understand. Please try again."})
    
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({
            "message": "Sorry, I encountered an error processing your request. Please try again.",
            "step": "ask_destination",
            "destination": "",
            "days": 0,
            "budget": 0
        }), 500

@app.route('/voice', methods=['POST'])
def voice():
    try:
        data = request.json
        user_input = data.get("message", "").strip()
        is_speech = data.get("is_speech", False)
        step = data.get("step", "ask_destination")
        destination = data.get("destination", "")
        days = data.get("days", 0)
        budget = data.get("budget", 0)

        print(f"Current step: {step}, Destination: {destination}, Days: {days}, Budget: {budget}")
        print(f"User input: {user_input}")

        if step == "ask_destination" and not user_input:
            return jsonify({
                "message": "Which city in India are you planning to visit?",
                "step": "ask_destination",
                "destination": "",
                "days": 0,
                "budget": 0
            })

        if step == "ask_destination":
            if not user_input:
                return jsonify({
                    "message": "Please tell me which city you want to visit.",
                    "step": "ask_destination",
                    "destination": "",
                    "days": 0,
                    "budget": 0
                })
            
            destination = ' '.join([word.capitalize() for word in user_input.split()])
            if len(destination) < 2:
                return jsonify({
                    "message": "Please provide a valid city name.",
                    "step": "ask_destination",
                    "destination": "",
                    "days": 0,
                    "budget": 0
                })
            
            return jsonify({
                "message": f"How many days do you plan to spend in {destination}? (e.g., 'three days' or '3 days')",
                "step": "ask_days",
                "destination": destination,
                "days": 0,
                "budget": 0
            })

        if step == "ask_days":
            try:
                days_match = re.search(r'(\d+)', user_input.replace(',', ''))
                if days_match:
                    days = int(days_match.group(1))
                else:
                    # Try to match English number words
                    number_words = {
                        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
                        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14,
                        'fifteen': 15, 'twenty': 20, 'thirty': 30, 'forty': 40,
                        'fifty': 50, 'hundred': 100
                    }
                    lower_input = user_input.lower()
                    for word, num in number_words.items():
                        if word in lower_input:
                            days = num
                            break
                    else:
                        raise ValueError("No valid number found")
                
                if days <= 0 or days > 30:
                    return jsonify({
                        "message": "Please provide a valid number of days between 1 and 30.",
                        "step": "ask_days",
                        "destination": destination,
                        "days": 0,
                        "budget": 0
                    })
                
                return jsonify({
                    "message": f"What's your total budget for this {days}-day trip to {destination}? (Please say the amount in INR)",
                    "step": "ask_budget",
                    "destination": destination,
                    "days": days,
                    "budget": 0
                })
            except (ValueError, AttributeError):
                return jsonify({
                    "message": "Please tell me a valid number of days for your trip (e.g., 'three days' or '3 days').",
                    "step": "ask_days",
                    "destination": destination,
                    "days": 0,
                    "budget": 0
                })

        if step == "ask_budget":
            try:
                budget_text = user_input.lower()
                budget = 0
                
                if 'thousand' in budget_text:
                    num_match = re.search(r'(\d+\.?\d*)', budget_text.replace(',', ''))
                    if num_match:
                        budget = float(num_match.group(1)) * 1000
                elif 'lakh' in budget_text or 'lac' in budget_text:
                    num_match = re.search(r'(\d+\.?\d*)', budget_text.replace(',', ''))
                    if num_match:
                        budget = float(num_match.group(1)) * 100000
                elif 'crore' in budget_text:
                    num_match = re.search(r'(\d+\.?\d*)', budget_text.replace(',', ''))
                    if num_match:
                        budget = float(num_match.group(1)) * 10000000
                else:
                    num_match = re.search(r'(\d+\.?\d*)', budget_text.replace(',', ''))
                    if num_match:
                        budget = float(num_match.group(1))
                
                budget = int(budget)
                
                if budget <= 0:
                    return jsonify({
                        "message": "Please provide a valid budget amount greater than zero.",
                        "step": "ask_budget",
                        "destination": destination,
                        "days": days,
                        "budget": 0
                    })
                
                min_budget = days * 1000
                if budget < min_budget:
                    return jsonify({
                        "message": f"Your budget of {budget} INR for {days} days might be too low for a comfortable trip. We recommend at least {min_budget} INR. Would you like to increase your budget? (Yes/No)",
                        "step": "confirm_low_budget",
                        "destination": destination,
                        "days": days,
                        "budget": budget
                    })
                
                trip_plan = generate_trip_plan(destination, days, budget)
                return jsonify({
                    "message": trip_plan,
                    "step": "trip_complete",
                    "destination": destination,
                    "days": days,
                    "budget": budget
                })
            except (ValueError, AttributeError):
                return jsonify({
                    "message": "Please tell me a valid budget amount for your trip (e.g., '5000 INR' or 'five thousand rupees').",
                    "step": "ask_budget",
                    "destination": destination,
                    "days": days,
                    "budget": 0
                })

        if step == "confirm_low_budget":
            if user_input.lower() in ["yes", "y"]:
                return jsonify({
                    "message": "Please provide your new budget amount:",
                    "step": "ask_budget",
                    "destination": destination,
                    "days": days,
                    "budget": 0
                })
            else:
                # Proceed with the original low budget
                trip_plan = generate_trip_plan(destination, days, budget)
                return jsonify({
                    "message": trip_plan,
                    "step": "trip_complete",
                    "destination": destination,
                    "days": days,
                    "budget": budget
                })

        if step == "trip_complete":
            return jsonify({
                "message": "Would you like to plan another trip? (Yes/No)",
                "step": "ask_another_trip",
                "destination": destination,
                "days": days,
                "budget": budget
            })

        if step == "ask_another_trip":
            if user_input.lower() in ["yes", "y"]:
                return jsonify({
                    "message": "Great! Which city are you planning to visit?",
                    "step": "ask_destination",
                    "destination": "",
                    "days": 0,
                    "budget": 0
                })
            else:
                return jsonify({
                    "message": "Thank you for using the tourism chatbot. Have a great day!",
                    "step": "end_conversation",
                    "destination": "",
                    "days": 0,
                    "budget": 0
                })

        return jsonify({
            "message": "I didn't understand that. Could you please repeat?",
            "step": step,
            "destination": destination,
            "days": days,
            "budget": budget
        })

    except Exception as e:
        print(f"Error in voice endpoint: {str(e)}")
        return jsonify({
            "message": "Sorry, I encountered an error. Please try again.",
            "step": "ask_destination",
            "destination": "",
            "days": 0,
            "budget": 0
        }), 500

def speech_to_text(max_retries=3):
    """Improved speech recognition with retries and better error handling"""
    for attempt in range(max_retries):
        try:
            with sr.Microphone() as source:
                print(f"Attempt {attempt + 1}: Speak now...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                text = recognizer.recognize_google(audio, language="en-US")
                if text:
                    print(f"Recognized: {text}")
                    return text
        except sr.WaitTimeoutError:
            print("Listening timed out while waiting for speech")
            if attempt == max_retries - 1:
                return "I didn't hear anything. Please try again."
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
            if attempt == max_retries - 1:
                return "Sorry, I couldn't understand your speech."
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            if attempt == max_retries - 1:
                return "Speech service is unavailable. Please try typing instead."
        except Exception as e:
            print(f"Unexpected error in speech recognition: {str(e)}")
            if attempt == max_retries - 1:
                return "Sorry, there was an error processing your speech."

    return "Sorry, I couldn't understand your speech after several attempts. Please try typing your response."

@app.route('/play_audio', methods=['GET'])
def play_audio():
    try:
        text = request.args.get('text', '')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Clean the text
        clean_text = re.sub(r'<[^>]*>', '', text)
        clean_text = re.sub(r'•', '-', clean_text)
        
        # Split long text into chunks
        max_chunk_length = 200
        text_chunks = [clean_text[i:i+max_chunk_length] 
                      for i in range(0, len(clean_text), max_chunk_length)]
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            try:
                # Generate speech for each chunk and combine
                for chunk in text_chunks:
                    tts = gTTS(text=chunk, lang='en', slow=False)
                    tts.write_to_fp(tmp_file)
                
                tmp_file.close()
                
                # Read the file and send as response
                with open(tmp_file.name, 'rb') as f:
                    audio_data = f.read()
                
                # Clean up
                os.unlink(tmp_file.name)
                
                response = make_response(audio_data)
                response.headers['Content-Type'] = 'audio/mpeg'
                response.headers['Content-Disposition'] = 'inline; filename=itinerary.mp3'
                return response
                
            except Exception as e:
                print(f"gTTS error: {str(e)}")
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)
                return jsonify({"error": "Failed to generate speech"}), 500
            
    except Exception as e:
        print(f"Error in play_audio: {str(e)}")
        return jsonify({"error": f"Error generating audio: {str(e)}"}), 500

@app.route('/play_audio_pyttsx3', methods=['POST'])
def play_audio_pyttsx3():
    try:
        data = request.json
        text = data.get("text", "")
        
        temp_engine = pyttsx3.init()
        temp_engine.say(text)
        temp_engine.runAndWait()
        
        return jsonify({
            "message": "Audio played successfully."
        })
    except Exception as e:
        print(f"Error in play_audio_pyttsx3: {str(e)}")
        return jsonify({
            "message": f"Error playing audio: {str(e)}"
        }), 500

@app.route('/slides')
def slides():
    return render_template('slides.html')

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

@app.route('/contactus')
def contactus():
    return render_template('contactus.html')

if __name__ == '__main__':
    app.run(debug=True)