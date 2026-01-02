# 🏥 Intelligent Appointment Optimization System

AI-powered healthcare appointment matching system that combines clinical triage with intelligent scheduling algorithms to route patients to optimal care appointments.

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31-red.svg)](https://streamlit.io/)
[![Infermedica](https://img.shields.io/badge/Infermedica-API%20v3-green.svg)](https://developer.infermedica.com/)

> ⚠️ **Important:** This is an MVP/portfolio implementation that uses a **simplified Infermedica integration** for demonstration purposes. It does NOT implement the full recommended Infermedica interview flow. See [Important Notes](#important-notes) for details.

---

## 📋 Table of Contents

- [Overview](#overview)
- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [Important Notes](#important-notes)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Architecture](#architecture)
- [Algorithm Details](#algorithm-details)
- [Demo](#demo)
- [Roadmap](#roadmap)
- [Contact](#contact)

---

## Overview

This system demonstrates intelligent healthcare appointment optimization by combining:

- **Clinical AI** (Infermedica) for symptom assessment and triage
- **Smart matching algorithm** that scores appointments by urgency, specialty, and availability
- **Cost transparency** showing estimated costs for different care options
- **Alternative recommendations** including ER, urgent care, and telemedicine

**Proof of Concept:** Demonstrates technical feasibility of appointment optimization approach that could address documented healthcare inefficiencies.

**Built by:** Eric McLean, Senior Delivery Manager with 5+ years of Infermedica implementation experience

---

## The Problem

Healthcare organizations face significant inefficiencies in appointment scheduling:

- **[$150B lost annually](https://www.hcinnovationgroup.com/clinical-it/article/13008175/missed-appointments-cost-the-us-healthcare-system-150b-each-year)** from appointment no-shows in the US ([Healthcare Innovation, 2024](https://www.hcinnovationgroup.com/clinical-it/article/13008175/missed-appointments-cost-the-us-healthcare-system-150b-each-year))
- **[20-30% no-show rate](https://curogram.com/blog/average-patient-no-show-rate)** often due to inappropriate bookings ([Curogram, 2025](https://curogram.com/blog/average-patient-no-show-rate))
- **[19.7M inappropriate specialist referrals](https://www.healthcaredive.com/news/survey-almost-20m-referrals-per-year-go-to-the-wrong-specialist/331410/)** annually, costing $2B ([Kyruus, 2014](https://www.healthcaredive.com/news/survey-almost-20m-referrals-per-year-go-to-the-wrong-specialist/331410/))
- **[Urgent cases waiting 76+ days](https://www.hcinnovationgroup.com/clinical-it/article/13008175/missed-appointments-cost-the-us-healthcare-system-150b-each-year)** for complex diagnostics ([Healthcare Innovation, 2024](https://www.hcinnovationgroup.com/clinical-it/article/13008175/missed-appointments-cost-the-us-healthcare-system-150b-each-year))
- **[20-30% of ER visits are non-urgent](https://doctorsa.com/stories/er-waiting-times/)**, wasting emergency resources ([DoctorsA, 2025](https://doctorsa.com/stories/er-waiting-times/))

**Result:** Frustrated patients, inefficient resource use, and lost revenue.

---

## The Solution

An AI-powered system that:

1. **Analyzes symptoms** using medical-grade NLP (Infermedica)
2. **Assesses urgency** with 5-level clinical triage
3. **Scores appointments** using intelligent matching algorithm
4. **Recommends optimal care** with transparent reasoning
5. **Provides alternatives** (ER, urgent care, telemedicine)

**Outcome:** Right patient → Right provider → Right time → Right cost

---

## Important Notes

### ⚠️ Simplified Infermedica Integration

**This is an MVP/portfolio implementation that uses a simplified Infermedica flow.**

#### ✅ What This System DOES:

- Uses Infermedica `/parse` endpoint for symptom NLP
- Uses Infermedica `/triage` endpoint for urgency assessment
- Uses Infermedica `/recommend_specialist` for specialist recommendation
- Demonstrates core API integration capabilities
- Shows intelligent appointment matching algorithm

#### ❌ What This System Does NOT Do:

- **Does NOT implement the full Infermedica interview flow** using the `/diagnosis` endpoint
- **Does NOT conduct iterative questioning** (the recommended production approach)
- **Does NOT use `should_stop` flag** to dynamically end the interview
- **Does NOT implement red flags checking** via `/suggest` with `suggest_method: "red_flags"`
- **Does NOT collect common risk factors** via `/suggest` with `suggest_method: "demographic_risk_factors"`
- **Does NOT gather related symptoms** via `/suggest` with `suggest_method: "symptoms"`

#### 📖 Recommended Production Flow (Per Infermedica Documentation)

According to [Infermedica's Engine API best practices](https://developer.infermedica.com/documentation/engine-api/), the recommended flow includes:

```
1. Initial symptoms (/parse or /search)
2. Common risk factors (/suggest with suggest_method="demographic_risk_factors")
3. Related symptoms (/suggest with suggest_method="symptoms")
4. Red flags check (/suggest with suggest_method="red_flags")
5. Interview loop (/diagnosis until should_stop=true)  ← NOT IMPLEMENTED IN MVP
6. Final triage (/triage)
7. Specialist recommendation (/recommend_specialist)
```

**This MVP skips steps 2-5** and goes directly from symptom parsing → triage.

#### 🎯 Why This Simplified Approach?

**For Portfolio/Demo Purposes:**

- ✅ Faster to build and demo (1-2 weeks vs 3-4 weeks)
- ✅ Still demonstrates API integration skills
- ✅ Shows understanding of clinical triage
- ✅ Proves appointment matching algorithm capabilities
- ✅ Allows focus on the novel intelligent matching logic

**Production Implementation Would Add:**

- Full `/diagnosis` interview loop with dynamic questioning
- Risk factor collection and management
- Red flags detection for safety
- Related symptoms suggestion for thoroughness
- `should_stop` logic for optimal interview length
- Enhanced accuracy through iterative evidence refinement

#### 📊 Accuracy Implications

| Approach                  | Evidence Collection        | Accuracy         | Use Case            |
| ------------------------- | -------------------------- | ---------------- | ------------------- |
| **Current (MVP)**         | Initial symptom parse only | Good for demo    | Portfolio, learning |
| **Full Infermedica Flow** | Iterative questioning      | Production-grade | Clinical use        |

### 🔒 Additional Limitations

- **Demonstration system** - Uses simulated appointment data
- **No PHI storage** - Session-based processing only
- **Not for medical use** - Educational/portfolio purposes only
- **Not HIPAA compliant** - Would require additional security for production

---

## Key Features

### ✅ Clinical Intelligence

- **Medical-grade NLP** - Handles "I have a cold" → symptoms automatically
- **5-level triage** - Emergency ambulance → Self-care
- **Specialist recommendation** - AI suggests appropriate specialty
- **Serious symptom detection** - Flags concerning findings

### ✅ Smart Appointment Matching

- **Multi-factor scoring** - Urgency (50%) + Specialty (30%) + Availability (20%)
- **Explainable recommendations** - Clear reasoning for each suggestion
- **Ranked results** - Best match first, alternatives shown
- **Cost transparency** - Estimated costs for each option

### ✅ User Experience

- **Clean, healthcare-appropriate UI** - Built with Streamlit
- **Real-time results** - Analysis in ~1-2 seconds
- **Session management** - Review results without re-running
- **Mobile-friendly** - Responsive design

---

## Technology Stack

### Core Technologies

- **Python 3.13** - Primary language
- **Streamlit 1.31** - Web interface framework
- **Infermedica API v3** - Clinical triage and NLP

### APIs Used

- **Infermedica `/parse`** - Natural language symptom parsing
- **Infermedica `/triage`** - 5-level urgency assessment
- **Infermedica `/recommend_specialist`** - Specialist recommendation (optional)

### Libraries

- **requests** - HTTP client for API calls
- **python-dotenv** - Environment variable management
- **dataclasses** - Type-safe data structures

---

## Getting Started

### Prerequisites

- Python 3.13 or higher
- Infermedica API credentials ([Get free developer access](https://developer.infermedica.com/))
- pip package manager

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/appointment-optimizer.git
cd appointment-optimizer
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

```bash
cp .env.example .env
```

Edit `.env` and add your Infermedica credentials:

```bash
INFERMEDICA_APP_ID=your_app_id_here
INFERMEDICA_APP_KEY=your_app_key_here
INFERMEDICA_BASE_URL=https://api.infermedica.com/v3
```

5. **Launch the application**

```bash
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

---

## Usage

### Example Scenarios

#### Emergency Case

```
Age: 45
Sex: Male
Symptoms: "I have chest pain and feel dizzy when I stand up"

Expected Result:
- Urgency: Emergency (24 hours)
- Specialist: Cardiologist
- Best Match: Next-day cardiology appointment
```

#### Routine Case

```
Age: 28
Sex: Female
Symptoms: "I have a cold and fever for 3 days"

Expected Result:
- Urgency: Consultation
- Specialist: Primary Care
- Best Match: This week primary care appointment
```

---

## Architecture

```
User Input (Streamlit)
        ↓
Orchestrator (appointment_optimizer.py)
        ↓
    ┌───┴────┬──────────────┐
    ▼        ▼              ▼
Infermedica  Matcher    Simulator
  (API)     (Algorithm)  (Data)
```

**Design Principles:**

- **Separation of Concerns** - Each component has single responsibility
- **Loose Coupling** - Components interact through clean interfaces
- **Stateless Processing** - Deterministic, predictable behavior

---

## Algorithm Details

### Matching Algorithm

```python
total_score = (urgency_match * 0.5) +   # Clinical safety first
              (specialist_match * 0.3) + # Specialist fit important
              (availability * 0.2)       # Sooner is better
```

**Urgency Match (50%):** Emergency → must be <24 hours  
**Specialist Match (30%):** Exact match = 1.0, Primary care fallback = 0.7  
**Availability (20%):** Sooner is better for urgent cases

[See full algorithm documentation in code]

---

## Demo

[Add screenshots/video link here]

### Live Demo (if deployed)

[Your Streamlit Cloud URL]

---

## Roadmap

### ✅ Completed (MVP - V1)

- [x] Infermedica API integration (simplified)
- [x] Intelligent matching algorithm
- [x] Streamlit UI
- [x] Cost transparency

### 🚧 Next (V2)

- [ ] Full Infermedica `/diagnosis` interview flow
- [ ] Iterative questioning with `should_stop`
- [ ] Red flags detection
- [ ] Risk factors collection
- [ ] Related symptoms

### 📋 Future (Production)

- [ ] Epic/Cerner FHIR integration
- [ ] Real appointment booking
- [ ] HIPAA compliance
- [ ] User authentication

---

## Disclaimer

**This is a demonstration/portfolio project and is NOT intended for actual medical use.**

- ✅ Educational purposes
- ✅ Portfolio demonstration
- ❌ Not HIPAA compliant
- ❌ Not for clinical decisions
- ❌ Not a medical device

**For medical emergencies, always call 911.**

---

## Contact

**Eric McLean**  
Senior Delivery Manager | Healthcare AI Solutions

📧 Email: [ericmc21@gmail.com]  
🔗 Portfolio: [https://eric-mclean.com](https://eric-mclean.com)  
💼 LinkedIn: [https://www.linkedin.com/in/ejmclean/]  
🐙 GitHub: [https://github.com/ericmc21]

---

**Built with ❤️ and Python**

_Demonstrating healthcare technology expertise, clinical AI integration, and intelligent algorithm design_
