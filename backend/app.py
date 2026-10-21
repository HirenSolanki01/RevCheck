from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS 
import torch
import pandas as pd
from werkzeug.utils import secure_filename
import os
import torch.nn.functional as F
from transformers import RobertaTokenizer, RobertaForSequenceClassification, pipeline
from scraper import scrape_booking_reviews 
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend'))

app = Flask(__name__, static_folder=None)
CORS(app) 

# --- MODEL 1: Your fine-tuned Fake/Real Classifier ---
MODEL_PATH = os.path.join(BASE_DIR, 'final_model_distilroberta')
print("Loading the saved models and tokenizers...")
try:
    # Your existing model for fake vs. real prediction
    fake_review_tokenizer = RobertaTokenizer.from_pretrained(MODEL_PATH)
    fake_review_model = RobertaForSequenceClassification.from_pretrained(MODEL_PATH)
    fake_review_model.eval()
    print("All models loaded successfully!")
except Exception as e:
    print(f"Error loading models: {e}")
    exit()

zero_shot_classifier = None


def get_zero_shot_classifier():
    """Lazy-load the heavy zero-shot model so the API can boot quickly."""
    global zero_shot_classifier
    if zero_shot_classifier is None:
        print("Loading Zero-Shot classification pipeline...")
        zero_shot_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        print("Zero-Shot classification pipeline loaded.")
    return zero_shot_classifier

LABELS = ['fake', 'real']
API_ENDPOINTS = {
    'predict': {'method': 'POST', 'path': '/predict'},
    'scrape-and-predict': {'method': 'POST', 'path': '/scrape-and-predict'},
    'analyze-file': {'method': 'POST', 'path': '/analyze-file'},
    'cross-check-review': {'method': 'POST', 'path': '/cross-check-review'},
    'health': {'method': 'GET', 'path': '/health'},
}
API_DOCS = [
    {
        'name': 'Health Check',
        'method': 'GET',
        'path': '/health',
        'description': 'Simple health endpoint to verify server status.',
        'content_type': 'application/json',
        'sample_request': None
    },
    {
        'name': 'Predict Review',
        'method': 'POST',
        'path': '/predict',
        'description': 'Classifies a single review as REAL or FAKE.',
        'content_type': 'application/json',
        'sample_request': {'review': 'Great hotel and very clean rooms.'}
    },
    {
        'name': 'Scrape And Predict',
        'method': 'POST',
        'path': '/scrape-and-predict',
        'description': 'Scrapes reviews from a Booking URL and predicts each one.',
        'content_type': 'application/json',
        'sample_request': {'url': 'https://www.booking.com/hotel/in/example.en-gb.html'}
    },
    {
        'name': 'Analyze File',
        'method': 'POST',
        'path': '/analyze-file',
        'description': 'Analyzes CSV uploads containing a review column.',
        'content_type': 'multipart/form-data',
        'sample_request': {'file': '<csv file with review column>'}
    },
    {
        'name': 'Cross Check Review',
        'method': 'POST',
        'path': '/cross-check-review',
        'description': 'Compares review clauses with hotel consensus signals. Can use mock database or real Booking.com data.',
        'content_type': 'application/json',
        'sample_request': {
            'hotel_name': 'The Royal Pinnacle',
            'review_text': 'WiFi was amazing but room service was very slow.',
            'booking_url': 'https://www.booking.com/hotel/in/example.en-gb.html (optional - for real data)'
        }
    },
]
UI_PAGES = [
    {'name': 'Home', 'path': '/'},
    {'name': 'Text Analysis', 'path': '/text-analysis.html'},
    {'name': 'URL Analysis', 'path': '/url-analysis.html'},
    {'name': 'File Analysis', 'path': '/file-analysis.html'},
    {'name': 'Cross Check', 'path': '/cross-check.html'},
    {'name': 'API Docs', 'path': '/api-docs'},
]


@app.route('/', methods=['GET'])
def serve_home():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:path>', methods=['GET'])
def serve_static(path):
    if path == 'api-docs':
        return send_from_directory(FRONTEND_DIR, 'api-docs.html')
    if path in API_ENDPOINTS:
        endpoint = API_ENDPOINTS[path]
        return jsonify({
            'error': 'This is an API endpoint.',
            'message': f"Use {endpoint['method']} {endpoint['path']} instead of opening it directly in a browser.",
            'available_endpoints': list(API_ENDPOINTS.values())
        }), 405
    return send_from_directory(FRONTEND_DIR, path)


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})


@app.route('/api/endpoints', methods=['GET'])
def list_endpoints():
    return jsonify({
        'backend_endpoints': API_DOCS,
        'ui_pages': UI_PAGES
    })

# --- ## FINAL, REFINED DUMMY DATABASE ## ---
existing_reviews_db = {
    "The Royal Pinnacle": [
        # Consensus: WiFi is EXCELLENT
        {"user": "Rohan", "review": "Blazing fast internet, I could stream 4K content without a single buffer. Perfect for my business needs."},
        {"user": "Priya", "review": "The connectivity here is top-notch. The WiFi signal was strong and stable in every corner of the hotel."},
        {"user": "Arjun", "review": "Best WiFi I've ever experienced in any hotel. Never had a single moment of disconnection during my week-long stay."},
        {"user": "Meera", "review": "The internet speed here puts my home connection to shame. Perfect for working remotely."},
        {"user": "Sanjay", "review": "Outstanding WiFi coverage even on the 15th floor. No dead zones anywhere."},
        # Consensus: Room Service is TERRIBLE
        {"user": "Anjali", "review": "Called room service three times for a bottle of water and it took them over an hour to deliver. Very disappointing."},
        {"user": "Vikram", "review": "The room service staff were rude and my order arrived cold. A truly awful experience."},
        {"user": "Pooja", "review": "Ordered breakfast at 8 AM, it arrived at 10:30 AM. The toast was soggy and tea was lukewarm."},
        {"user": "Rajeev", "review": "Room service is a joke. They forgot half my order and delivered the wrong items."},
        {"user": "Sneha", "review": "Waited 90 minutes for room service. When it finally came, the food was mediocre and overpriced."},
        # Consensus: Food is EXCELLENT
        {"user": "Sunita", "review": "The breakfast buffet was the highlight of my stay. So many options and everything tasted delicious, especially the local dishes."},
        {"user": "Sameer", "review": "I had the best paneer tikka of my life at their restaurant. The chefs here are true artists."},
        {"user": "Ritika", "review": "The dinner menu had amazing variety. Every dish was beautifully presented and tasted exceptional."},
        {"user": "Nikhil", "review": "The restaurant's biryani is legendary. I went there three times during my stay."},
        {"user": "Kavya", "review": "World-class cuisine with authentic Indian flavors. The service at the restaurant was impeccable."},
        # Consensus: Rooms are TERRIBLE
        {"user": "Fatima", "review": "Booked a 'deluxe' room which turned out to be tiny and cramped. The photos online are very misleading."},
        {"user": "David", "review": "The room felt old and worn out. The furniture was chipped and the bathroom had a strange smell."},
        {"user": "Christine", "review": "Room was small and dingy. The wallpaper was peeling and the carpet was stained."},
        {"user": "Rohit", "review": "Not worth the price. The room looked nothing like the pictures on their website."},
        {"user": "Shalini", "review": "Cramped space, poor maintenance, and the AC was barely functional. Disappointing for a 5-star hotel."},
        # Consensus: Surroundings are EXCELLENT
        {"user": "Neha", "review": "Even though it's in a busy area, the hotel is surprisingly quiet and peaceful. The valet parking made everything so convenient."},
        {"user": "Kumar", "review": "The hotel is an oasis of calm. Secure and easy parking was a huge plus."},
        {"user": "Ashok", "review": "Perfect location with easy access to shops and restaurants. The neighborhood is very safe."},
        {"user": "Divya", "review": "Strategic location with minimal noise despite being in a commercial area. Great for business travelers."},
        {"user": "Vikrant", "review": "The surroundings are beautiful. Tree-lined streets and a peaceful atmosphere throughout."}
    ],
    "Goa Shoreline Resort": [
        # Consensus: WiFi is TERRIBLE
        {"user": "Isabelle", "review": "Forget about getting any work done, the internet barely works in the rooms. Only usable in the lobby."},
        {"user": "John", "review": "The WiFi is a joke. It's slower than my 2G phone connection. Don't come here if you need to be online."},
        {"user": "Thomas", "review": "Tried to video call my family and kept getting disconnected. Very frustrating."},
        {"user": "Patricia", "review": "WiFi doesn't work in most of the property. Had to sit in the lobby all day to get a connection."},
        {"user": "Richard", "review": "Advertised WiFi but it's practically non-existent. Complained to reception and they said nothing could be done."},
        # Consensus: Room Service is EXCELLENT
        {"user": "Maria", "review": "Room service staff were so friendly and the late-night snacks menu was excellent. They went above and beyond."},
        {"user": "Leo", "review": "Lightning-fast room service! I ordered a meal at 1 AM and it arrived, hot and correct, in under 20 minutes."},
        {"user": "Fernanda", "review": "The room service team is exceptional. Always professional and attentive to every detail."},
        {"user": "Antonio", "review": "Best room service experience I've had. They even anticipated what we needed without asking."},
        {"user": "Rosa", "review": "Ordered multiple times and every delivery was prompt and the food quality was excellent."},
        # Consensus: Food is TERRIBLE
        {"user": "Chloe", "review": "The food is catered to foreign tourists with no spice. Very underwhelming for a place like Goa."},
        {"user": "Daniel", "review": "My fish curry was watery and tasteless. A complete disgrace to Goan cuisine."},
        {"user": "Patricia", "review": "Bland and uninspired menu. The seafood was overcooked and dry."},
        {"user": "Carlos", "review": "Expensive and mediocre food. The restaurant has a reputation it doesn't deserve."},
        {"user": "Elena", "review": "Food quality is poor for the prices they charge. Very disappointed with the dining options."},
        # Consensus: Rooms are EXCELLENT
        {"user": "Sophie", "review": "Our sea-facing room was huge and spacious, with a beautiful balcony."},
        {"user": "Michael", "review": "The room was spotless, very large, and the bed was incredibly comfortable."},
        {"user": "Jennifer", "review": "Amazing room with sea views and luxurious furnishings. Perfect for a beach getaway."},
        {"user": "David", "review": "The rooms are immaculate and very well-appointed. Modern amenities throughout."},
        {"user": "Michelle", "review": "Spacious room with excellent ventilation and a beautiful ocean view from the balcony."},
        # Consensus: Surroundings are TERRIBLE
        {"user": "Olivia", "review": "It's located right next to a noisy shack that plays loud music until 2 AM. Not peaceful at all."},
        {"user": "Ben", "review": "The beach access is public and crowded, not private as advertised. The area feels a bit unsafe at night."},
        {"user": "Steven", "review": "Neighborhood is quite noisy and chaotic. Not the peaceful beach escape I was expecting."},
        {"user": "Jessica", "review": "The surroundings are dirty and poorly maintained. Many stray dogs in the area."},
        {"user": "Mark", "review": "Location is disappointing. Too close to commercial establishments with constant noise."}
    ],
    "Himalayan Serenity": [
        # Consensus: WiFi is EXCELLENT
        {"user": "Aarav", "review": "I was surprised to have such a stable and fast internet connection this high up in the mountains."},
        {"user": "Ishaan", "review": "The WiFi here is better than what I have at home in the city! Reliable and fast."},
        {"user": "Harsh", "review": "Excellent connectivity despite the remote location. Great for remote work."},
        {"user": "Priya", "review": "Fiber-like speeds in the mountains. Impressed with their infrastructure."},
        {"user": "Rahul", "review": "Strong WiFi signal throughout the property. Never experienced any disconnections."},
        # Consensus: Room Service is TERRIBLE
        {"user": "Myra", "review": "Room service closes at 9 PM, which is far too early for a hotel. Very inconvenient for travelers."},
        {"user": "Kabir", "review": "It's clear they are understaffed. It took forever to get anyone to answer the room service line."},
        {"user": "Simran", "review": "Limited room service hours and very slow response times. Not acceptable for a hotel."},
        {"user": "Ajay", "review": "Room service is inefficient and frequently unavailable during the evening."},
        {"user": "Nisha", "review": "Terrible room service experience. Staff was dismissive when I asked for service after 9 PM."},
        # Consensus: Food is EXCELLENT
        {"user": "Diya", "review": "The traditional Himachali food they served was authentic and incredibly flavorful. A must-try!"},
        {"user": "Arjun", "review": "The fresh mountain trout was cooked to perfection. Dining here was an absolute delight."},
        {"user": "Sneha", "review": "The organic local cuisine is phenomenal. Every meal felt like a culinary journey."},
        {"user": "Vikram", "review": "Farm-to-table dining at its finest. The flavors are incredible and authentic."},
        {"user": "Ananya", "review": "The restaurant serves the best Himachali cuisine I've tasted. Highly recommended."},
        # Consensus: Rooms are TERRIBLE
        {"user": "Zara", "review": "The room was rustic, but that just meant it was old and poorly maintained. The heating was inadequate for the cold."},
        {"user": "Reyansh", "review": "Found insects in the bathroom and the linens didn't seem fresh. I was very uncomfortable during my stay."},
        {"user": "Pooja", "review": "The room is outdated and uncomfortable. Poor insulation means it was freezing at night."},
        {"user": "Sanjay", "review": "Room maintenance is poor. Creaky beds and broken furniture detract from the experience."},
        {"user": "Meera", "review": "Very basic rooms with minimal amenities. The décor feels stuck in the 90s."},
        # Consensus: Surroundings are EXCELLENT
        {"user": "Anika", "review": "The location is absolutely breathtaking and silent. Perfect for a peaceful retreat. Parking was easy to find."},
        {"user": "Vihaan", "review": "Waking up to the view of the snow-capped peaks from my window was a core memory. Incredibly peaceful."},
        {"user": "Roshan", "review": "Stunning mountain views and perfect tranquility. The environment here is magical."},
        {"user": "Divya", "review": "The location is ideal for nature lovers. Quiet, serene, and surrounded by natural beauty."},
        {"user": "Rajesh", "review": "Beautiful surroundings with minimal pollution. Perfect getaway from the city hustle."}
    ],
    "Jaipur Heritage Palace": [
        # Consensus: WiFi is TERRIBLE
        {"user": "William", "review": "The WiFi is non-existent. They claim to have it, but it just doesn't work. Had to use my mobile data the whole time."},
        {"user": "Emma", "review": "The thick palace walls seem to block all signals. Don't expect to have any functional internet here."},
        {"user": "Anthony", "review": "WiFi is abysmal. Can't even load a webpage properly during peak hours."},
        {"user": "Victoria", "review": "Terrible internet service. The staff seemed indifferent to the complaints."},
        {"user": "Edward", "review": "WiFi is one of the worst I've experienced. Multiple disconnections throughout the day."},
        # Consensus: Room Service is EXCELLENT
        {"user": "James", "review": "Felt like royalty with their room service. The staff addressed me by name and were extremely attentive."},
        {"user": "Charlotte", "review": "Every request via room service was handled with grace and speed. Truly 5-star service."},
        {"user": "Alexander", "review": "Room service is impeccable. They delivered with a smile and perfect timing."},
        {"user": "Sophia", "review": "Exceptional room service staff. They went above and beyond to meet all my needs."},
        {"user": "Benjamin", "review": "The level of service is incredible. Room service feels genuinely personal and thoughtful."},
        # Consensus: Food is TERRIBLE
        {"user": "Henry", "review": "The food is incredibly expensive and not authentic at all. It's a classic tourist trap."},
        {"user": "Amelia", "review": "My meal was cold and the portions were tiny for the exorbitant price. A huge disappointment."},
        {"user": "Frederick", "review": "Overpriced and underwhelming menu options. Not worth the cost at all."},
        {"user": "Isabella", "review": "The restaurant serves mediocre food at premium prices. Total ripoff."},
        {"user": "Charles", "review": "Food quality doesn't match the price point. Very disappointed with the dining experience."},
        # Consensus: Rooms are EXCELLENT
        {"user": "George", "review": "Staying in the Maharaja suite was a dream. The room was gigantic, with beautiful traditional decor and artifacts."},
        {"user": "Ella", "review": "Our room was beautifully preserved and felt like stepping back in time, but with all modern comforts. Absolutely stunning."},
        {"user": "Michael", "review": "The rooms are magnificently decorated with royal touches. A truly luxurious experience."},
        {"user": "Alice", "review": "Every detail in the room is carefully curated. It's like staying in a museum of elegance."},
        {"user": "David", "review": "The rooms exude grandeur and comfort. Stunning architecture and impeccable maintenance."},
        # Consensus: Surroundings are TERRIBLE
        {"user": "Arthur", "review": "The constant noise from weddings and events held at the palace made it impossible to rest."},
        {"user": "Grace", "review": "The location is right on a busy, loud main road. The palace gardens are small and not well-maintained."},
        {"user": "Robert", "review": "Surrounded by chaos and noise. Not suitable for a peaceful retreat."},
        {"user": "Margaret", "review": "The noise levels are unacceptable. Wedding functions happening every night."},
        {"user": "Joseph", "review": "Loud and chaotic surroundings. The hotel organizes too many events which disturb guests."}
    ],
    "Bangalore Tech Park Hotel": [
        # Consensus: WiFi is EXCELLENT
        {"user": "Advik", "review": "As expected for a hotel in the tech capital, the internet was flawless and incredibly high-speed."},
        {"user": "Saanvi", "review": "Gigabit speeds and zero downtime. This is the best hotel internet I've ever experienced, period."},
        {"user": "Nirav", "review": "Lightning-fast WiFi throughout the hotel. Perfect for a tech-focused establishment."},
        {"user": "Anjali", "review": "The internet is incredibly reliable and fast. No buffering during my video conferences."},
        {"user": "Arjun", "review": "5G-like speeds in the hotel. Exceptional connectivity for work and streaming."},
        # Consensus: Room Service is TERRIBLE
        {"user": "Ayaan", "review": "The service is robotic and impersonal. They just leave the tray and rush out without a word."},
        {"user": "Kiara", "review": "They completely forgot one of the items in my order and still tried to charge me for it."},
        {"user": "Varun", "review": "Room service is dismissive and unhelpful. No effort to address concerns."},
        {"user": "Neha", "review": "Food arrived late and cold. Staff showed no concern for customer satisfaction."},
        {"user": "Sanjay", "review": "Very poor service quality. The staff seemed irritated by requests."},
        # Consensus: Food is EXCELLENT
        {"user": "Vivaan", "review": "The international cuisine at the buffet is top-notch, catering to all palates. The sushi bar was a surprise hit!"},
        {"user": "Tara", "review": "The South Indian breakfast options were authentic and delicious. The filter coffee was perfect."},
        {"user": "Rohit", "review": "Excellent variety at the buffet. Something for everyone's taste. Fresh and well-prepared."},
        {"user": "Priya", "review": "The food quality is exceptional. The chefs clearly take pride in their work."},
        {"user": "Vikram", "review": "Outstanding international cuisine with Indian comfort food options. Highly satisfied."},
        # Consensus: Rooms are TERRIBLE
        {"user": "Aditya", "review": "The room felt like a sterile, small box. It was clean but had absolutely no character or comfort."},
        {"user": "Ananya", "review": "For the price, the room is incredibly small. There's barely enough space to open a suitcase."},
        {"user": "Harsh", "review": "Tiny room with minimal amenities. More like a capsule hotel than a luxury property."},
        {"user": "Diya", "review": "Cramped and uncomfortable rooms. Not worth the premium pricing."},
        {"user": "Karan", "review": "The room was uncomfortable and claustrophobic. Poor design choices throughout."},
        # Consensus: Surroundings are EXCELLENT
        {"user": "Ishaan", "review": "The location is perfect for business in the tech park, and the basement parking is secure and spacious."},
        {"user": "Riya", "review": "It's very well-connected to the metro and airport, making it an extremely convenient location for a business trip."},
        {"user": "Mahesh", "review": "Strategic location with excellent connectivity to all business hubs. Perfect for professionals."},
        {"user": "Ritika", "review": "Easy access to tech parks and business centers. The neighborhood is safe and well-developed."},
        {"user": "Suresh", "review": "Ideal location for business travelers. All amenities and transportation options nearby."}
    ],
    "Grand Ocean Palace": [
        # Consensus: WiFi is EXCELLENT
        {"user": "Marcus", "review": "The WiFi here is phenomenal. Streaming 4K videos without buffering, perfect for my media work."},
        {"user": "Sarah", "review": "Staying connected was seamless. The internet speed was blazing fast throughout my 5-day stay."},
        {"user": "Patricia", "review": "Best connectivity I've experienced in a beach resort. Excellent for remote work."},
        {"user": "Jonathan", "review": "Ultra-fast WiFi with excellent coverage throughout the entire property. Impressed!"},
        {"user": "Rebecca", "review": "The internet is incredibly stable. Never had a single drop in connection during my stay."},
        # Consensus: Room Service is EXCELLENT
        {"user": "Luke", "review": "Room service was attentive and quick. They delivered my order within 15 minutes and everything was hot and fresh."},
        {"user": "Emma", "review": "The staff responded to requests immediately and with a smile. Truly exceptional service."},
        {"user": "Nicholas", "review": "Room service is world-class. Staff anticipated my needs before I even asked."},
        {"user": "Catherine", "review": "Impeccable room service with staff who genuinely care. Outstanding experience."},
        {"user": "Andrew", "review": "The room service team is professional and attentive. Every request handled perfectly."},
        # Consensus: Food is EXCELLENT
        {"user": "Robert", "review": "The restaurant serves world-class seafood. The fish curry was absolutely divine and authentic."},
        {"user": "Jessica", "review": "Every meal was a culinary masterpiece. The chef clearly knows their craft with exceptional flavors."},
        {"user": "William", "review": "The seafood here is fresh and expertly prepared. Absolutely delicious every time."},
        {"user": "Amanda", "review": "Fine dining at its best. The menu is creative and the execution is flawless."},
        {"user": "Joseph", "review": "Outstanding culinary experience. The restaurant deserves Michelin recognition."},
        # Consensus: Rooms are EXCELLENT
        {"user": "Daniel", "review": "The oceanview room was spacious with premium bedding and modern amenities throughout."},
        {"user": "Rachel", "review": "Our suite was impeccably clean, luxurious, and had a stunning view of the ocean horizon."},
        {"user": "Christopher", "review": "The rooms are beautifully designed with top-quality furnishings. Pure luxury."},
        {"user": "Angela", "review": "Spacious and elegant rooms with all the modern comforts. Absolutely worth the price."},
        {"user": "Matthew", "review": "Every detail in the room is perfect. Premium amenities and impeccable cleanliness."},
        # Consensus: Surroundings are EXCELLENT
        {"user": "Michael", "review": "Located right on the beach with private access. The sunset views are absolutely breathtaking every evening."},
        {"user": "Lisa", "review": "The beachfront location is premium. Safe area, beautiful surroundings, and convenient access to everything."},
        {"user": "James", "review": "The beach setting is paradise. Private access with pristine sandy shores. Perfect!"},
        {"user": "Jennifer", "review": "Stunning location with exclusive beach access. The views are mesmerizing."},
        {"user": "Richard", "review": "Excellent beachfront location with safe, clean surroundings. Everything about it is premium."}
    ]
}


ASPECT_LABELS = [
    'physical features of the guest room, including its size, bed comfort, and amenities', 
    'hotel staff, reception, and room service responsiveness', 
    'cleanliness of the room and hotel', 
    'WiFi speed, internet signal, and connectivity', 
    'quality and taste of restaurant food and breakfast', 
    'the hotel\'s geographical location, its surrounding environment, and parking facilities'
]
SENTIMENT_LABELS = ['positive feedback', 'negative feedback']

# --- Cache for storing consensus maps to improve performance and consistency ---
_consensus_cache = {}

# --- Helper function to split reviews ---
def split_review_into_clauses(review_text):
    """Splits a review by conjunctions and punctuation to analyze parts separately."""
    clauses = re.split(r'\s*[,.]\s*|\s+\b(?:but|and)\b\s+', review_text)
    return [clause.strip() for clause in clauses if clause and clause.strip()]


# --- Helper function using the transformer pipeline ---
def analyze_review_aspect_and_sentiment(review_text):
    """
    Uses a zero-shot classification model to determine the primary aspect and sentiment of a review.
    """
    classifier = get_zero_shot_classifier()
    aspect_result = classifier(review_text, candidate_labels=ASPECT_LABELS)
    top_aspect = aspect_result['labels'][0]
    sentiment_result = classifier(review_text, candidate_labels=SENTIMENT_LABELS)
    top_sentiment = sentiment_result['labels'][0]
    return top_aspect, top_sentiment

# --- Your existing prediction function (no changes) ---
def predict_review(review_text):
    inputs = fake_review_tokenizer(review_text, return_tensors="pt", padding=True, truncation=True, max_length=256)
    with torch.no_grad():
        outputs = fake_review_model(**inputs)
    logits = outputs.logits
    probabilities = F.softmax(logits, dim=1)
    prediction_index = torch.argmax(probabilities, dim=1).item()
    predicted_label = LABELS[prediction_index]
    confidence_score = probabilities[0][prediction_index].item() * 100 
    return predicted_label, confidence_score


# --- API Endpoint now uses caching with real-time scraping support ---
@app.route('/cross-check-review', methods=['POST'])
def handle_cross_check():
    data = request.get_json()
    if not data or 'hotel_name' not in data or 'review_text' not in data:
        return jsonify({'error': 'Request must include "hotel_name" and "review_text"'}), 400

    hotel_name = data['hotel_name']
    new_review_text = data['review_text']
    booking_url = data.get('booking_url', None)  # Optional parameter for real data

    # --- Fetch reviews: from URL if provided, else from mock database ---
    reviews_to_analyze = None
    cache_key = hotel_name

    if booking_url:
        # Scrape real reviews from Booking.com
        print(f"--- Scraping real reviews from Booking.com: {booking_url} ---")
        try:
            scraped_df = scrape_booking_reviews(booking_url, max_reviews=50)
            if scraped_df.empty:
                return jsonify({'overall_verdict': 'INCONCLUSIVE', 'reason': 'Could not fetch reviews from the provided Booking.com URL.'}), 200
            reviews_to_analyze = [{'review': row['review']} for _, row in scraped_df.iterrows()]
            cache_key = booking_url  # Use URL as cache key for real data
            print(f"--- Scraped {len(reviews_to_analyze)} reviews from {booking_url} ---")
        except Exception as e:
            print(f"Error scraping Booking.com: {e}")
            return jsonify({'overall_verdict': 'INCONCLUSIVE', 'reason': f'Error fetching real reviews: {str(e)}'}), 200
    else:
        # Use mock database if no URL provided
        if hotel_name not in existing_reviews_db:
            return jsonify({'overall_verdict': 'INCONCLUSIVE', 'reason': f'Not enough data for "{hotel_name}" to perform a cross-check.'}), 200
        reviews_to_analyze = existing_reviews_db[hotel_name]

    # --- CACHING LOGIC ---
    if cache_key in _consensus_cache:
        consensus_map = _consensus_cache[cache_key]
    else:
        print(f"--- Building new consensus cache for {cache_key} ---")
        consensus_map = {}
        for review in reviews_to_analyze:
            aspect, sentiment = analyze_review_aspect_and_sentiment(review['review'])
            if aspect not in consensus_map:
                consensus_map[aspect] = []
            consensus_map[aspect].append(sentiment)
        _consensus_cache[cache_key] = consensus_map
        print(f"--- Cache for {cache_key} built: {consensus_map} ---")
    # --- END CACHING LOGIC ---

    clauses = split_review_into_clauses(new_review_text)
    if not clauses:
        return jsonify({'overall_verdict': 'INCONCLUSIVE', 'reason': 'Review text is too short to analyze.'}), 200

    analysis_results = []
    is_outlier_found = False

    for clause in clauses:
        clause_aspect, clause_sentiment = analyze_review_aspect_and_sentiment(clause)

        if clause_aspect in consensus_map:
            sentiments = consensus_map[clause_aspect]
            positive_count = sentiments.count('positive feedback')
            negative_count = len(sentiments) - positive_count
            
            is_clause_outlier = False
            reason = ""
            
            if clause_sentiment == 'positive feedback' and negative_count > positive_count:
                is_clause_outlier = True
                is_outlier_found = True
                reason = f"This positive comment conflicts with a mostly negative consensus ({negative_count} vs {positive_count}) on this topic."
            
            elif clause_sentiment == 'negative feedback' and positive_count > negative_count:
                is_clause_outlier = True
                is_outlier_found = True
                reason = f"This negative comment conflicts with a mostly positive consensus ({positive_count} vs {negative_count}) on this topic."
            
            else:
                reason = "This comment is consistent with feedback from other guests."
            
            analysis_results.append({
                "clause": clause,
                "aspect": clause_aspect,
                "sentiment": clause_sentiment.split(' ')[0],
                "is_outlier": is_clause_outlier,
                "reason": reason
            })
        else:
             analysis_results.append({
                "clause": clause,
                "aspect": clause_aspect,
                "sentiment": clause_sentiment.split(' ')[0],
                "is_outlier": False,
                "reason": "There is not enough historical data about this specific topic to form a consensus."
            })


    if not analysis_results:
        return jsonify({'overall_verdict': 'INCONCLUSIVE', 'reason': 'Could not identify specific aspects in the review.'}), 200

    if is_outlier_found:
        overall_verdict = "FAKE_REVIEW"
    else:
        overall_verdict = "GENUINE_REVIEW"
        
    return jsonify({
        "overall_verdict": overall_verdict,
        "analysis": analysis_results
    })


# --- Existing API Endpoints 
@app.route('/predict', methods=['POST'])
def handle_prediction():
    if not request.json or 'review' not in request.json:
        return jsonify({'error': 'Invalid request. Please provide a JSON with a "review" key.'}), 400
    review_text = request.json['review']
    try:
        prediction, confidence_score = predict_review(review_text)
        response_data = {
            'prediction': prediction.upper(),
            'confidence_score': f"{confidence_score:.2f}%"
        }
        return jsonify(response_data)
    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'error': 'Failed to process the review.'}), 500
    
@app.route('/scrape-and-predict', methods=['POST'])
def handle_scraping():
    if not request.json or 'url' not in request.json:
        return jsonify({'error': 'Invalid request. Please provide a "url" key.'}), 400
    target_url = request.json['url']
    try:
        reviews_df = scrape_booking_reviews(target_url, max_reviews=50)
        if reviews_df.empty:
            return jsonify({'error': 'Could not scrape any reviews from the URL.'}), 404
        results = []
        for review_text in reviews_df['review']:
            prediction, confidence_score = predict_review(review_text)
            results.append({
                'review_text': review_text[:100] + "...",
                'prediction': prediction.upper(),
                'confidence_score': f"{confidence_score:.2f}%"
            })
        print("Scraping and analysis complete.")
        return jsonify(results)
    except Exception as e:
        print(f"An error occurred during scraping/analysis: {e}")
        return jsonify({'error': 'An internal error occurred.'}), 500

@app.route('/analyze-file', methods=['POST'])
def analyze_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400
    try:
        df = pd.read_csv(file)
        if 'review' not in df.columns:
            return jsonify({'error': 'CSV must contain a "review" column'}), 400
        results = []
        for review in df['review'].fillna(''):
            if isinstance(review, str) and review.strip():
                prediction, confidence_score = predict_review(review)
                results.append({
                    'review': review,
                    'prediction': prediction.upper(),
                    'confidence_score': f"{confidence_score:.2f}%"
                })
        return jsonify(results)
    except Exception as e:
        print(f"Error processing file: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)

