# 🌾 Project Golden Rice — Student Placement Data Analysis System

An executive, privacy-compliant campus recruitment intelligence platform built with **Flask**, **Pandas**, **NumPy**, and **Matplotlib**. Designed with a fluid glassmorphism interface, real-time eligibility evaluation, cohort analytics, and full Dark/Light theme switching.

---

## ✨ Features

- **📊 Executive Analytics Dashboard:** Real-time KPI calculations (Placement Rate, Average Package, Median Package, Dream Offer Peak) with transparent, borderless Matplotlib visualizations.
- **🎓 Student Records & Eligibility Registry:** Instant live client-side eligibility evaluation (CGPA $\ge 6.00$ and $0$ active backlogs) as student records are entered.
- **💼 Placement Tracking & Dream Offers:** Campus offer logging with compensation metrics (in LPA) and automated highlighting for top-tier offers ($\ge 15\text{ LPA}$).
- **⚡ Technical Skills Catalog:** Student skill tagging and industry skill demand distribution analysis.
- **📑 Cohort Performance Auditing:** Disaggregated departmental outcome reports engineered with strict eligibility denominator verification.
- **🌙 Fluid UI with Dark/Light Mode:** Seamless theme switching with zero-flicker `localStorage` persistence, ambient lighting gradients, and responsive glassmorphism cards.
- **🔄 Dual Database Engine:** Out-of-the-box local **SQLite** support with seamless one-click switching to an enterprise **MySQL** database.
- **🔐 Role-Based Authentication:** Secure user authentication (`werkzeug.security` password hashing) with persistent 30-day "Remember Me" sessions.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.10+, Flask
- **Data & Analytics:** Pandas, NumPy, Matplotlib
- **Database:** SQLite (default) / MySQL 8.0+
- **Frontend:** HTML5, CSS3 (Custom Glassmorphism & Gradient System), Vanilla JS
- **Design:** Figma & FigJam ([UI Flow & Architecture](https://www.figma.com/board/VBUKxaGDNJkCKieymxFCpf))

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/project-golden-rice.git
cd project-golden-rice
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize & Seed Database (Optional)
To populate the database with realistic sample cohorts (60 students, 10 skills, 38+ placement records):
```bash
python seed_data.py
```

### 4. Run the Web Server
On Windows:
```cmd
run_server.bat
```
Or with Python:
```bash
python app.py
```

Open your browser to: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 Default Credentials

- **Username:** `admin`
- **Password:** `admin123`
*(You can also register a new account on the `/signup` page)*

---

## 📜 License
MIT License. Developed for Academic Placement Intelligence & Analytics.
