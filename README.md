# Rank2College 🎓 | JOSAA Seat Allocation Predictor

A full-stack web application designed to help engineering aspirants predict their college admissions through JOSAA and CSAB counseling. 

## 💡 Why I Built This
Navigating JOSAA counseling can be incredibly stressful. I wanted to build a tool that doesn't just dump raw cutoff data onto a screen, but actually gives students a realistic probability of getting into specific NITs, IIITs, and GFTIs. Instead of just showing past ranks, this engine calculates a +/- 10% variance margin to classify admission chances into **Safe, Likely, Moderate, and Stretch**.

## 🚀 Features
* **Advanced Filtering:** Query historical data by Exam Type (Mains/Advanced), Category, Gender, Quota (Home State/Outside State), and specific Branch keywords.
* **Smart Probability Algorithm:** Dynamically calculates admission chances based on user rank vs. historical closing ranks.
* **Responsive UI:** Custom-built frontend featuring a clean, data-heavy table that gracefully handles long Indian engineering college names without breaking layout.
* **Secure Backend:** RESTful API built with Express.js, utilizing environment variables to protect database credentials.

## 🛠️ Tech Stack
* **Frontend:** HTML5, Vanilla CSS, Vanilla JavaScript (DOM Manipulation & Fetch API)
* **Backend:** Node.js, Express.js
* **Database:** MySQL
* **Security/Config:** `dotenv` for environment variable management

## 💻 Local Setup & Installation

If you want to run this project locally, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/SHUBHANKAR1605/rank2college.git](https://github.com/SHUBHANKAR1605/rank2college.git)
   cd rank2college