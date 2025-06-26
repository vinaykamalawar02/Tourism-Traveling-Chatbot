# TripGenius - AI-Powered Travel Itinerary Planner

![TripGenius Banner](https://via.placeholder.com/1200x400?text=TripGenius+Banner)

TripGenius is an intelligent tourism planning web application that generates personalized travel itineraries using Google's Gemini AI. Users interact via voice or text to receive detailed daily plans with attractions, activities, and budget-aware recommendations.

## Key Features

✨ **Multi-Modal Interaction**
- Voice interface with speech recognition/synthesis
- Text-based chatbot interface
- Visual destination browser

📝 **AI-Generated Itineraries**
- Daily schedules with time slots
- Entry fees & transportation details
- Local cuisine recommendations
- Evening activities and hidden gems

💰 **Budget-Centric Features**
- INR support (lakhs/crores parsing)
- Cost validation and warnings
- Accommodation suggestions with TripAdvisor links

🌐 **Integrated Knowledge**
- Wikipedia destination summaries
- Context-aware conversation flow
- Responsive for all devices

## Tech Stack

### Backend
- Python 3.x
- Flask (Web Framework)
- Google Generative AI (Gemini 1.5 Flash)
- Wikipedia-API (Python wrapper)
- SpeechRecognition (v3.10+)
- gTTS (Google Text-to-Speech) + pyttsx3 fallback

### Frontend
- HTML5, CSS3, JavaScript
- Swiper.js (v11.0.5+)
- Web Speech API
- Responsive design (mobile-first)

## Installation & Setup

1. **Clone repository**
 
   git clone https://github.com/yourusername/TripGenius.git
   cd TripGenius

2. Set up virtual environment

    python -m venv venv
    # Linux/MacOS:
    source venv/bin/activate
    # Windows:
    venv\Scripts\activate

3. Install dependencies

    pip install -r requirements.txt

3. Configure environment

    echo "GEMINI_API_KEY=your_api_key_here" > .env

4. Run application

    python app.py
    Access at: http://localhost:5000

5. Project Structure

    TripGenius/
    ├── static/                # Static assets
    │   ├── css/               # Custom styles
    │   ├── img/               # All images
    │   └── js/                # JavaScript files
    ├── templates/             # Jinja2 templates
    │   ├── core/              # Base templates
    │   ├── features/          # Feature pages
    │   └── partials/          # UI components
    ├── app.py                 # Flask application
    ├── config.py              # Configuration
    ├── requirements.txt       # Dependencies
    └── README.md              # Documentation