

import re
import math
from typing import Dict, Any, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# Department Mappings with Heads and SLA limits (in hours)
DEPARTMENTS = {
    "Infrastructure & Civil": {
        "code": "INFRA",
        "head": "Engr. Rajesh Sharma",
        "email": "civil-help@campus.edu",
        "icon": "building",
        "keywords": ["wall", "door", "window", "roof", "leak", "plumbing", "tap", "pipe", "water", "drain", "furniture", "chair", "desk", "building", "floor", "tiles", "crack"]
    },
    "IT & Network Services": {
        "code": "IT_NET",
        "head": "Dr. Ananya Roy",
        "email": "it-support@campus.edu",
        "icon": "wifi",
        "keywords": ["wifi", "wi-fi", "internet", "network", "router", "lan", "portal", "login", "server", "computer", "lab pc", "website", "software", "password", "ethernet"]
    },
    "Electrical & HVAC": {
        "code": "ELEC_HVAC",
        "head": "Mr. Vikram Patel",
        "email": "electrical@campus.edu",
        "icon": "zap",
        "keywords": ["power", "electricity", "spark", "short circuit", "fan", "ac", "air conditioner", "light", "bulb", "switch", "wiring", "socket", "elevator", "lift", "transformer", "blackout"]
    },
    "Hostel & Mess Services": {
        "code": "HOSTEL_MESS",
        "head": "Warden S. K. Gupta",
        "email": "hostel-office@campus.edu",
        "icon": "home",
        "keywords": ["mess", "food", "hygiene", "room", "bed", "geyser", "hot water", "laundry", "canteen", "dinner", "lunch", "breakfast", "warden", "hostel", "dorm", "insect"]
    },
    "Campus Security & Safety": {
        "code": "SECURITY",
        "head": "Chief Officer R. V. Singh",
        "email": "security@campus.edu",
        "icon": "shield",
        "keywords": ["theft", "stolen", "cctv", "security", "guard", "gate", "unauthorized", "harassment", "emergency", "stranger", "lockout", "id card", "parking", "vehicle"]
    },
    "Academic & Library": {
        "code": "ACADEMIC",
        "head": "Prof. Meera Deshmukh",
        "email": "academic-ops@campus.edu",
        "icon": "book-open",
        "keywords": ["projector", "podium", "mic", "speaker", "classroom", "lecture hall", "library", "book", "lab equipment", "bench", "blackboard", "whiteboard", "av system"]
    },
    "Sanitation & Housekeeping": {
        "code": "SANITATION",
        "head": "Ms. Sunita Verma",
        "email": "cleanliness@campus.edu",
        "icon": "trash-2",
        "keywords": ["dustbin", "trash", "garbage", "cleaning", "washroom", "toilet", "stink", "smell", "dirt", "sweeping", "hygiene", "litter", "sanitizer", "pest", "mosquito"]
    }
}

# High Urgency Triggers (Force Critical/High Priority)
CRITICAL_TRIGGERS = [
    "fire", "smoke", "sparking", "short circuit", "gas leak", "elevator stuck", "lift stuck",
    "medical emergency", "sewage overflow", "power outage", "blackout", "security breach",
    "harassment", "physical threat", "exposed high voltage"
]

HIGH_TRIGGERS = [
    "water leak", "pipe burst", "no water", "exam tomorrow", "no internet in lab",
    "food poisoning", "stolen", "theft", "door lock broken", "geyser burst", "fan fell",
    "ac failure in server room"
]

# Negative sentiment words for urgency calculation
NEGATIVE_WORDS = [
    "terrible", "worst", "urgent", "immediately", "hazard", "dangerous", "unbearable",
    "broken", "failed", "disaster", "extreme", "severe", "frustrated", "unacceptable", "affecting exam"
]

# Synthetic Dataset for training ML Classifier
TRAINING_DATA = [
    # Infrastructure & Civil
    ("Water is leaking continuously from ceiling in Room 304 Civil Block", "Infrastructure & Civil"),
    ("The wooden door frame is broken and won't lock properly in hostel room", "Infrastructure & Civil"),
    ("Cracks on the wall near staircase in Science Block floor 2", "Infrastructure & Civil"),
    ("Restroom tap is broken and gushing water uncontrollably", "Infrastructure & Civil"),
    ("Floor tiles are loose and causing tripping hazard in main hallway", "Infrastructure & Civil"),
    ("Window glass broken after thunderstorm near chemistry laboratory", "Infrastructure & Civil"),
    ("Plumbing line blocked in central library ground floor washroom", "Infrastructure & Civil"),
    ("Desk and chairs broken in Classroom 102", "Infrastructure & Civil"),

    # IT & Network Services
    ("Wi-Fi connection is dropping every 5 minutes in Boys Hostel Block B", "IT & Network Services"),
    ("Cannot login to student portal to submit semester registration", "IT & Network Services"),
    ("Ethernet jack not working at desk 14 in Central Computer Lab", "IT & Network Services"),
    ("Library catalog website returning 500 server error", "IT & Network Services"),
    ("Slow internet speed across campus Wi-Fi SSID Campus_Guest", "IT & Network Services"),
    ("Lab PC 22 hard drive failure and OS not booting", "IT & Network Services"),
    ("Router in CSE department 3rd floor red light blinking no connection", "IT & Network Services"),
    ("Unable to reset password for college email account", "IT & Network Services"),

    # Electrical & HVAC
    ("Short circuit and sparks coming out of electrical board in Room 201", "Electrical & HVAC"),
    ("Complete power blackout in Hostel Block A since 2 hours", "Electrical & HVAC"),
    ("Air conditioner in Seminar Hall 1 making loud noise and not cooling", "Electrical & HVAC"),
    ("Ceiling fan wobbling dangerously in Lecture Hall 4", "Electrical & HVAC"),
    ("Corridor lights out on 3rd floor IT block pitch dark at night", "Electrical & HVAC"),
    ("Elevator stuck between floor 2 and 3 in Administrative Building", "Electrical & HVAC"),
    ("Electrical switch board warm to touch and smells like burning plastic", "Electrical & HVAC"),
    ("Geyser in hostel bathroom not heating water", "Electrical & HVAC"),

    # Hostel & Mess Services
    ("Food served at dinner was undercooked and unhygienic in Mess 2", "Hostel & Mess Services"),
    ("Hot water supply not working in Girls Hostel 1 bathrooms", "Hostel & Mess Services"),
    ("Bed mattress provided in Room 108 is damaged and infested with bugs", "Hostel & Mess Services"),
    ("Mess drinking water cooler dispenser dirty and unserviceable", "Hostel & Mess Services"),
    ("Cockroaches and insects found in dining hall mess area", "Hostel & Mess Services"),
    ("Laundry washing machine in Hostel Block C out of order", "Hostel & Mess Services"),
    ("Warden office closed during posted grievance hours", "Hostel & Mess Services"),

    # Campus Security & Safety
    ("Laptop stolen from central library reading room while on break", "Campus Security & Safety"),
    ("CCTV camera non-functional near North Gate parking area", "Campus Security & Safety"),
    ("Unauthorized personnel roaming in hostel area without visitor pass", "Campus Security & Safety"),
    ("Street lights near sports complex dark creating security safety risk", "Campus Security & Safety"),
    ("Bicycle missing from designated parking lot B", "Campus Security & Safety"),
    ("Security guard absent at South Entry Gate during night hours", "Campus Security & Safety"),
    ("Harassment incident near canteen reported by student group", "Campus Security & Safety"),

    # Academic & Library
    ("Projector in Hall 3 display flickering and color corrupted", "Academic & Library"),
    ("Podium microphone in Auditorium cutting out during lectures", "Academic & Library"),
    ("Required reference books missing from library computer science section", "Academic & Library"),
    ("Digital smartboard in Classroom 204 touch screen unresponsive", "Academic & Library"),
    ("Lab oscilloscope in Electrical Engineering lab out of calibration", "Academic & Library"),
    ("Air conditioning unit in Library Silent Study zone too cold and noisy", "Academic & Library"),

    # Sanitation & Housekeeping
    ("Dustbin overflowing near Canteen block attracting stray dogs", "Sanitation & Housekeeping"),
    ("Restroom on 2nd floor Engineering Block not cleaned and foul smell", "Sanitation & Housekeeping"),
    ("Garbage accumulation behind sports complex pavilion", "Sanitation & Housekeeping"),
    ("Hand sanitizer dispenser empty across all main entry gates", "Sanitation & Housekeeping"),
    ("Stagnant water near garden area mosquito breeding hazard", "Sanitation & Housekeeping"),
    ("Dirty corridors in Hostel Block D ground floor", "Sanitation & Housekeeping")
]


class CampusNLPEngine:
    def __init__(self):
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), stop_words='english', max_features=1000)),
            ('clf', MultinomialNB(alpha=0.1))
        ])
        self._train_model()

    def _train_model(self):
        X = [item[0] for item in TRAINING_DATA]
        y = [item[1] for item in TRAINING_DATA]
        self.pipeline.fit(X, y)

    def preprocess_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9\s-]', '', text)
        return text.strip()

    def predict_category(self, title: str, description: str) -> Tuple[str, float, Dict[str, float]]:
        combined_text = f"{title} {description}".strip()
        cleaned_text = self.preprocess_text(combined_text)

        # Keyword matching fallback/boost score
        keyword_scores = {cat: 0.0 for cat in DEPARTMENTS.keys()}
        words = set(cleaned_text.split())
        
        for cat, details in DEPARTMENTS.items():
            for kw in details["keywords"]:
                if kw in cleaned_text:
                    keyword_scores[cat] += 2.5 if len(kw.split()) > 1 else 1.0

        # ML Model Prediction Probabilities
        probs = self.pipeline.predict_proba([cleaned_text])[0]
        classes = self.pipeline.classes_

        class_prob_map = {classes[i]: float(probs[i]) for i in range(len(classes))}

        # Combined hybrid scoring (70% ML + 30% Keyword exact matching)
        max_kw_score = max(keyword_scores.values()) or 1.0
        final_scores = {}
        for cat in DEPARTMENTS.keys():
            ml_p = class_prob_map.get(cat, 0.0)
            kw_p = keyword_scores[cat] / max_kw_score if max_kw_score > 0 else 0.0
            final_scores[cat] = round((0.65 * ml_p) + (0.35 * kw_p), 4)

        best_category = max(final_scores, key=final_scores.get)
        confidence = round(float(final_scores[best_category]) * 100, 1)
        # Ensure minimum baseline confidence for user UI clarity
        confidence = min(99.5, max(68.5, confidence))

        return best_category, confidence, final_scores

    def analyze_priority_and_urgency(self, title: str, description: str) -> Dict[str, Any]:
        text = f"{title} {description}".lower()
        
        # Check Critical triggers
        critical_matches = [t for t in CRITICAL_TRIGGERS if t in text]
        high_matches = [t for t in HIGH_TRIGGERS if t in text]
        sentiment_matches = [w for w in NEGATIVE_WORDS if w in text]

        score = 25  # Base score out of 100

        if critical_matches:
            score += 55 + (len(critical_matches) * 10)
        elif high_matches:
            score += 35 + (len(high_matches) * 10)

        score += len(sentiment_matches) * 8

        # Exclamation mark or ALL CAPS intensity indicator
        if "!" in title or "!" in description:
            score += 10
        if title.isupper() or "URGENT" in title.upper():
            score += 15

        # Cap score between 10 and 100
        score = min(100, max(10, score))

        if score >= 75 or len(critical_matches) > 0:
            priority = "Critical"
            sla_hours = 2
            badge_color = "#ef4444"
        elif score >= 55 or len(high_matches) > 0:
            priority = "High"
            sla_hours = 12
            badge_color = "#f97316"
        elif score >= 35:
            priority = "Medium"
            sla_hours = 24
            badge_color = "#eab308"
        else:
            priority = "Low"
            sla_hours = 48
            badge_color = "#3b82f6"

        # Key phrases / extracted tags
        extracted_keywords = list(set(critical_matches + high_matches + sentiment_matches))
        if not extracted_keywords:
            # Fallback to salient words
            words = [w for w in re.findall(r'\b[a-z]{4,}\b', text) if w not in ['this', 'that', 'with', 'from', 'have', 'there', 'please', 'working']]
            extracted_keywords = words[:4]

        sentiment_label = "Very Negative" if score > 70 else ("Negative" if score > 40 else "Neutral")

        return {
            "priority": priority,
            "urgency_score": score,
            "sla_hours": sla_hours,
            "badge_color": badge_color,
            "sentiment": sentiment_label,
            "triggers_found": extracted_keywords[:5],
            "is_emergency": priority == "Critical"
        }

    def analyze_complaint(self, title: str, description: str, user_category: str = None) -> Dict[str, Any]:
        best_cat, confidence, score_distribution = self.predict_category(title, description)
        priority_info = self.analyze_priority_and_urgency(title, description)
        
        final_cat = best_cat
        if user_category and user_category in DEPARTMENTS:
            # If user explicitly selected category, keep it but note NLP prediction
            final_cat = user_category

        dept_meta = DEPARTMENTS.get(final_cat, {})

        return {
            "predicted_category": best_cat,
            "final_category": final_cat,
            "confidence": confidence,
            "score_distribution": score_distribution,
            "priority": priority_info["priority"],
            "urgency_score": priority_info["urgency_score"],
            "sla_hours": priority_info["sla_hours"],
            "sentiment": priority_info["sentiment"],
            "triggers_found": priority_info["triggers_found"],
            "is_emergency": priority_info["is_emergency"],
            "assigned_department": final_cat,
            "department_code": dept_meta.get("code", "GENERAL"),
            "department_head": dept_meta.get("head", "Campus Administration"),
            "contact_email": dept_meta.get("email", "support@campus.edu")
        }


# Global Singleton
nlp_engine = CampusNLPEngine()

if __name__ == "__main__":
    test_text = "Urgent! Sparks coming out of switchboard near Room 302 Boys Hostel Block B!"
    result = nlp_engine.analyze_complaint("Short circuit in switchboard", test_text)
    print("NLP Analysis Test Result:")
    print(result)
