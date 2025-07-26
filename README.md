# 🏥 Medical Recommendation System (Machine Learning Project)

A **machine learning–based Flask web application** that provides preliminary medical recommendations (possible conditions, medicines, precautions) based on user-entered symptoms.  
This project demonstrates the integration of **AI/ML, data-driven decision-making, and secure web development** for healthcare applications.

---

## ✅ Key Features

- 🤖 **Symptom-based prediction** using a structured medical dataset
- ✅ Personalized suggestions considering:
  - Age group
  - Allergies
  - Past medical history
- ⚠️ Severity detection with emergency alerts
- 🔐 Secure user authentication (hashed passwords, CSRF protection)
- 📦 Cloud-ready backend (AWS/OpenSearch integration planned)
- Modular design for future ML model upgrades

---

## 🤖 Machine Learning Approach

- **Dataset:** `final_optimized_medical_dataset.csv` containing:
  - Diseases
  - Multiple symptoms per disease
  - Medicines & dosages
  - Severity scores
  - Precautions & alternative therapies
- **Algorithm:**  
  - Matches user symptoms against dataset entries
  - Calculates a "match score"
  - Predicts the most likely condition(s)
- **Probability Calculation:**  
  - Based on the ratio of matched symptoms to total symptoms
- **Future Enhancements:**
  - Train ML classifiers (Random Forest, SVM, Neural Networks)
  - Add NLP-based symptom extraction
  - Reinforcement learning for self-improving recommendations

---

## 🧠 Tech Stack

**Frontend:** HTML, CSS, JavaScript (Jinja templates)  
**Backend:** Flask (Python), SQLAlchemy ORM, Pandas  
**Database:** SQLite (local) → AWS RDS (future)  
**Cloud:** AWS EC2, OpenSearch (future integration)  
**Security:** CSRF protection, hashed passwords, session management

---

## 📂 Project Structure

Medical-Recommendation-System/
├── app.py
├── final_optimized_medical_dataset.csv
├── requirements.txt
├── templates/
│ ├── index.html
│ └── dashboard.html
├── static/
│ ├── css/
│ ├── js/
│ └── images/
├── report/
│ └── Medical_Recommendation_System_Report.pdf
└── README.md


## ⚙️ Installation & Setup
 
FOR INSTALLATION AND SETUP YOU CAN CONNECT THROUGH MY EMAIL - (piyushtawde2004@gmail.com)




🚀 Future Scope
✅ Full ML model integration

✅ Deploy on AWS with CI/CD pipelines

✅ Multilingual + voice input support

✅ Telemedicine integration

✅ IoT device data for real-time health monitoring

👨‍💻 Authors
Piyush Tawde – GitHub

Bhavana Satam(@Bhavanasatam07)


Mentor: Mr. Pratyush Urade
Institute: NHITM (University of Mumbai)
