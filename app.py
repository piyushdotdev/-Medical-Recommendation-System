from flask import Flask, request, jsonify, session, redirect, url_for, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import logging
from functools import wraps
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or "7d02cda47055b0492da796d8dd9e67b66f3d83b43c2ef44b7f0a2c6e6e66f037"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('CSRF_SECRET') or "super_secure_csrf_key"
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session lifetime

# Ensure instance folder exists
os.makedirs(app.instance_path, exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

# Constants
DISEASE_DATA_PATH = 'final_optimized_medical_dataset.csv'
MIN_SYMPTOM_MATCH = 1
HIGH_SEVERITY_THRESHOLD = 7

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    allergies = db.Column(db.String(500))
    medical_conditions = db.Column(db.String(500))
    past_medications = db.Column(db.String(500))
    age = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer)
    weight = db.Column(db.Integer)
    gender = db.Column(db.String(50))

class DiseasePredictor:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialize()
        return cls._instance
    
    def initialize(self):
        try:
            self.data = pd.read_csv(DISEASE_DATA_PATH, on_bad_lines='skip')
            self.data.fillna('', inplace=True)
            self._preprocess_data()
            logger.info("Dataset loaded and preprocessed successfully")
        except Exception as e:
            logger.error(f"Error initializing predictor: {str(e)}")
            self.data = pd.DataFrame()

    def _preprocess_data(self):
        symptom_cols = [col for col in self.data.columns if col.startswith('Symptom_')]
        self.data['Symptoms'] = self.data[symptom_cols].astype(str).agg(','.join, axis=1)
        self.data['Symptoms'] = self.data['Symptoms'].str.lower().str.split(',').apply(
            lambda x: [s.strip() for s in x if s.strip() and s != 'nan']
        )
        
        precaution_cols = [col for col in self.data.columns if col.startswith('Precaution_')]
        self.data['Precautions'] = self.data[precaution_cols].astype(str).agg(', '.join, axis=1)
    
    def predict(self, user_input, user_profile):
        if self.data.empty:
            logger.error("Medical dataset not loaded")
            return {"message": "System is initializing. Please try again shortly."}, False
        
        try:
            symptoms = [s.strip().lower() for s in user_input.split(',') if s.strip()]
            if not symptoms:
                return {"message": "Please enter at least one valid symptom"}, False
            
            self.data['match_score'] = self.data['Symptoms'].apply(
                lambda x: len(set(x) & set(symptoms))
            )
            
            max_match = self.data['match_score'].max()
            if max_match < MIN_SYMPTOM_MATCH:
                return {"message": "No strong matches found. Try more specific symptoms."}, False
            
            best_match = self.data.loc[self.data['match_score'].idxmax()]
            return self._format_result(best_match, symptoms, user_profile), True
        
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return {"message": "System is processing your request. Please try again."}, False
    
    def _format_result(self, disease_data, user_symptoms, user_profile):
        age_group = "Child" if user_profile['age'] < 18 else "Adult"
        med_key = 'Medicine_y' if age_group == "Child" else 'Medicine_x'
        dosage_key = 'Dosage_y' if age_group == "Child" else 'Dosage_x'
        
        matched_symptoms = set(user_symptoms) & set(disease_data['Symptoms'])
        probability = min(100, round(len(matched_symptoms) / len(set(user_symptoms)) * 100, 2))
        
        recommendations = []
        medicine = disease_data.get(med_key, 'Consult doctor')
        dosage = disease_data.get(dosage_key, 'Consult doctor')
        
        if user_profile['allergies'] and self._check_allergy(medicine, user_profile['allergies']):
            recommendations.append(f"⚠️ Allergy warning for {medicine}")
            alt_med = disease_data.get('Alternative_Therapies', 'Consult doctor for alternatives')
            recommendations.append(f"💊 Alternative: {alt_med}")
            medicine = "Consult doctor (allergy risk)"
            dosage = "Consult doctor"
        
        if int(disease_data.get('Severity_Score', 0)) >= HIGH_SEVERITY_THRESHOLD:
            recommendations.append("🚨 High severity - seek immediate care")
        
        if not recommendations:
            recommendations.append("✅ Follow standard treatment guidelines")
            recommendations.append("🩺 Monitor symptoms and consult doctor if they worsen")
        
        return {
            "disease": disease_data.get('Disease', 'Unknown condition'),
            "description": disease_data.get('Description', 'Consult healthcare professional'),
            "probability": probability,
            "medicine": medicine,
            "dosage": dosage,
            "precautions": disease_data.get('Precautions', 'General health precautions recommended'),
            "workout": [w for w in disease_data.get('Workout', '').split(',') if w.strip()],
            "severity": min(10, int(disease_data.get('Severity_Score', 5))),
            "recommendations": recommendations
        }
    
    def _check_allergy(self, medication, allergies):
        if not medication or not allergies:
            return False
        return any(
            med.strip().lower() in allergies.lower() 
            for med in medication.split(',')
        )

# Initialize predictor singleton
predictor = DiseasePredictor()

# Decorators
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
@csrf.exempt
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password required"}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify({
            "status": "error", 
            "message": "Invalid credentials"
        }), 401
    
    if not check_password_hash(user.password, password):
        return jsonify({
            "status": "error", 
            "message": "Invalid credentials"
        }), 401
    
    session['user_id'] = user.id
    session.permanent = True
    
    return jsonify({
        "status": "success",
        "redirect": url_for('dashboard')
    })

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    if not user:
        flash('Session expired. Please login again.', 'warning')
        return redirect(url_for('index'))
    return render_template('dashboard.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    try:
        required_fields = ['username', 'password', 'age']
        if any(field not in request.form for field in required_fields):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400
            
        if User.query.filter_by(username=request.form['username']).first():
            return jsonify({
                "status": "error", 
                "message": "Username already exists"
            }), 400
            
        user = User(
            username=request.form['username'],
            password=generate_password_hash(request.form['password']),
            age=int(request.form.get('age', 0)),
            height=int(request.form.get('height', 0)),
            weight=int(request.form.get('weight', 0)),
            gender=request.form.get('gender', 'other'),
            allergies='',
            medical_conditions='',
            past_medications=''
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Registration successful. Please login."
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error", 
            "message": f"Registration failed: {str(e)}"
        }), 400

@app.route('/predict', methods=['POST'])
@login_required
@csrf.exempt
def predict():
    try:
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({"status": "error", "message": "Session expired. Please login again."}), 401

        symptoms = request.form.get('symptoms', '').strip()
        if not symptoms:
            return jsonify({"status": "error", "message": "Please enter symptoms"}), 400

        user_profile = {
            'age': user.age,
            'allergies': user.allergies or '',
            'medical_conditions': user.medical_conditions or '',
            'past_medications': user.past_medications or ''
        }
        
        result, success = predictor.predict(symptoms, user_profile)
        
        if not success:
            return jsonify({
                "status": "info",
                "message": result.get("message", "No strong matches found"),
                "data": None
            })

        medical_history_match = False
        if user.medical_conditions and result.get('disease'):
            user_conditions = [c.strip().lower() for c in user.medical_conditions.split(',')]
            disease_lower = result['disease'].lower()
            medical_history_match = any(
                condition in disease_lower or disease_lower in condition
                for condition in user_conditions
                if condition
            )
            if medical_history_match and 'recommendations' in result:
                result['recommendations'].insert(0, "⚠️ History match - consult your doctor")

        return jsonify({
            "status": "success",
            "data": {
                **result,
                "medical_history_match": medical_history_match
            }
        })

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "Our system is currently busy. Please try again shortly."
        }), 500

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    try:
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({"status": "error", "message": "Session expired"}), 401
            
        user.age = int(request.form.get('age', user.age))
        user.height = int(request.form.get('height', user.height))
        user.weight = int(request.form.get('weight', user.weight))
        user.gender = request.form.get('gender', user.gender)
        
        db.session.commit()
        return jsonify({
            "status": "success", 
            "message": "Profile updated successfully"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error", 
            "message": f"Update failed: {str(e)}"
        }), 400

@app.route('/update_medical_info', methods=['POST'])
@login_required
def update_medical_info():
    try:
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({"status": "error", "message": "Session expired"}), 401
            
        user.allergies = request.form.get('allergies', '')
        user.medical_conditions = request.form.get('medical_conditions', '')
        user.past_medications = request.form.get('past_medications', '')
        
        db.session.commit()
        return jsonify({
            "status": "success", 
            "message": "Medical information updated successfully"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error", 
            "message": f"Update failed: {str(e)}"
        }), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)