# 🚗 FuelPulse – Intelligent Fleet & Fuel Analytics Management System

**FuelPulse** is a feature-rich, dynamic web application designed to help individual vehicle owners and fleet managers track, analyze, and optimize vehicle performance, expenses, logs, and maintenance cycles. Built on a robust monolithic backend, the platform bridges the gap between conventional log-keeping and predictive management by incorporating machine learning models, automated data extraction, and an interactive generative AI assistant.

---

## 🔑 Key Modules & Implementations

* **Dynamic Fleet Logging System**: Developed automated computational flows within Django models to seamlessly calculate tracking distance metrics, trip tracking, and fuel consumption formulas.
* **AI-Powered OCR Expense Extraction**: Integrated computer vision routines utilizing Tesseract OCR and Pillow to scan physical fuel or service receipts, extract numeric characters via custom RegEx parsing, and auto-populate transactional inputs.
* **Dynamic Machine Learning Outlier Detection**: Programmed statistical anomaly protection modules powered by **NumPy** and **scikit-learn** that compute running moving variations (Z-Scores) on historically registered fuel efficiency entries to immediately flag data errors or vehicle mechanical inefficiencies.
* **Integrated Generative AI Chatbot**: Configured an asynchronous chat gateway utilizing the Google Gemini API (`gemini-1.5-flash`), enriching model interactions with contextual state injections compiled on demand from relational history fields (such as document expiry tracking and maintenance milestones).
* **Predictive Maintenance Architectures**: Designed dynamic threshold algorithms adjusting to vehicle categorization metrics (Two Wheeler vs. Four Wheeler standards) to evaluate operational status flags (Good, Warning, Critical, Overdue) across critical component systems.
* **TCO & Financial Intelligence Dashboards**: Consolidated raw query values into interactive JavaScript visual components (Chart.js wrappers) detailing comprehensive parameters like Total Cost of Ownership (TCO) models, spending distributions, and targeted efficiency deviation variances ("What-If" Analysis).

---

## 🛠️ Technical Skill Stack Acquired

Through the end-to-end architecture, development, and deployment of **FuelPulse**, the following core capabilities and competencies were mastered:

### 1. Software Engineering & Full-Stack Web Architecture
* **Advanced Django Core Patterns**: Mastered relational model compositions, functional model overriding (`save()`), object aggregations, query optimizations, custom authentication models, and administrative role boundaries (`user_passes_test`).
* **Relational Database Design**: Designed relational schemas handling multi-tier dependency cascade deletions across multi-factor entities like `User`, `Vehicle`, `FuelLog`, `TripLog`, `MaintenanceLog`, and `NewCar` catalogs.
* **Modular Interface Structuring**: Constructed reusable application frontends utilizing template inheritance engines, customized form controls (`django-crispy-forms`), multi-tier conditional navigation interfaces, and adaptive feedback channels.

### 2. Artificial Intelligence & Data Engineering
* **Generative AI API Orchestration**: Experienced in managing state contexts, constructing specific structural constraints for system prompts, handling API error protections, and orchestrating failover logic when utilizing LLMs (`google-generativeai`).
* **Computer Vision and Document Processing**: Applied OCR engineering techniques (`pytesseract`) alongside image optimization concepts (`Pillow`) to accurately filter alphanumeric string inputs under variable quality conditions.
* **Statistical Data Analysis & Analytics**: Implemented scientific calculation computing routines (`NumPy`, `pandas`) to evaluate sequential trend pipelines and multi-layer array metrics.

### 3. Core Software Practices & Dependability Engineering
* **Clean Code & Robust Python Practices**: Mastered exception handling strategies (`OperationalError`, `ProgrammingError`), explicit type normalization routines, and defensive programming checks to prevent division-by-zero or mathematical format conversion faults.
* **Dependency & Environment Management**: Managed complex package structures and third-party libraries across active application dependencies (`scikit-learn`, `openai`, `httpx`).
