# RevCheck 🛡️
### AI-Powered Fake Review Detection & Consensus Analysis System

![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Backend-Flask-black?logo=flask&logoColor=white)
![PyTorch](https://img.shields.io/badge/AI-PyTorch%20%26%20Transformers-EE4C2C?logo=pytorch&logoColor=white)
![Selenium](https://img.shields.io/badge/Scraping-Selenium%20%2B%20Chromium-43B02A?logo=selenium&logoColor=white)
![Docker](https://img.shields.io/badge/Deployment-Docker-2496ED?logo=docker&logoColor=white)

## 📌 Overview

**RevCheck** is an AI-powered fake review detection platform designed to identify potentially fraudulent reviews in the hospitality industry. It combines transformer-based natural language processing (NLP), automated web scraping, and contextual consensus analysis to help users evaluate the authenticity of online reviews.

The system uses a fine-tuned **DistilRoBERTa** model to classify reviews as real or fake and provide prediction confidence scores. Its distinctive **Cross-Check Engine** compares individual reviews against historical review patterns to identify suspicious inconsistencies.

By combining machine learning with contextual analysis, RevCheck goes beyond simple text classification to provide a more comprehensive approach to review authenticity verification.

## 🌟 Live Demo

- **Frontend:** Add your Netlify deployment URL here.
- **Backend API:** Add your Hugging Face Spaces URL here.

## ✨ Key Features

### 🧠 AI-Powered Fake Review Detection
- Uses a fine-tuned DistilRoBERTa transformer model for review classification.
- Trained on a dataset containing 20,000+ real and fake reviews.
- Generates prediction confidence scores to help interpret classification results.
- Leverages contextual language representations to analyze review text.

### 🌐 Real-Time Review Scraping
- Accepts Booking.com hotel URLs for review analysis.
- Uses Selenium and headless Chromium to automate browser-based review collection.
- Uses BeautifulSoup4 for HTML parsing and Selenium-Stealth for browser automation compatibility.
- Connects collected reviews to the AI detection pipeline.

### 📊 Contextual Cross-Check Engine
- Analyzes review patterns and aggregate sentiment to establish a historical consensus.
- Identifies reviews that contradict commonly reported hotel experiences.
- Highlights potentially suspicious outliers for further investigation.

**Example:** If historical reviews consistently report poor Wi-Fi connectivity, a new review claiming exceptionally fast Wi-Fi may be flagged for contextual review.

> A contradiction does not automatically prove that a review is fake. The Cross-Check Engine identifies inconsistencies that may require further investigation.

### 📂 Bulk Review Analysis
- Supports CSV uploads for batch processing.
- Enables analysis of large collections of reviews.
- Helps users identify potentially suspicious reviews across datasets.

## 🏗️ System Architecture

RevCheck separates the user interface, API processing, machine learning inference, and browser automation into distinct logical components.

```text
                  ┌──────────────────────┐
                  │        User          │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   Frontend Interface  │
                  │     HTML / CSS / JS  │
                  └──────────┬───────────┘
                             │ REST API
                             ▼
                  ┌──────────────────────┐
                  │     Flask Backend    │
                  │   Request Handling   │
                  └──────────┬───────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────────┐ ┌────────────┐ ┌────────────────┐
     │ Transformer AI │ │ Web Scraper│ │  CSV Processor │
     │ DistilRoBERTa  │ │  Selenium  │ │ Batch Analysis │
     └────────┬───────┘ └──────┬─────┘ └───────┬────────┘
              │                │               │
              └────────────────┼───────────────┘
                               ▼
                  ┌──────────────────────┐
                  │ Cross-Check Engine    │
                  │ Consensus & Outliers  │
                  └──────────┬───────────┘
                             ▼
                  ┌──────────────────────┐
                  │ Analysis Results     │
                  │ Predictions & Scores │
                  └──────────────────────┘
```

### Deployment Architecture

- **Frontend:** Netlify — hosts the web interface.
- **Backend:** Hugging Face Spaces — hosts the Flask API and model inference environment.
- **Containerization:** Docker — packages the Python application and browser automation dependencies.
- **Model Storage:** Git LFS — manages large model files.

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python 3.10 |
| Frontend | HTML5, CSS3, JavaScript |
| Backend | Flask, REST APIs |
| Machine Learning | PyTorch, Hugging Face Transformers |
| NLP Model | Fine-tuned DistilRoBERTa |
| Web Scraping | Selenium, Selenium-Stealth, BeautifulSoup4 |
| Browser Automation | Headless Chromium |
| Deployment | Docker, Hugging Face Spaces, Netlify |
| Model Versioning | Git LFS |
| Data Processing | CSV, Python data-processing libraries |

## ⚙️ How It Works

1. **Input:** The user submits review text, a supported hotel URL, or a CSV file.
2. **Data Collection:** For URL-based analysis, the scraper attempts to collect available reviews from the specified page.
3. **Preprocessing:** Review text is cleaned and prepared for model inference.
4. **AI Classification:** DistilRoBERTa predicts whether each review is likely to be real or fake and returns a confidence score.
5. **Consensus Analysis:** The Cross-Check Engine evaluates review patterns and potential inconsistencies against the available historical data.
6. **Results:** The system presents the classification and relevant contextual findings to the user.

## 🚀 Getting Started

### Prerequisites

Make sure you have the following installed:

- Python 3.10
- Git
- pip
- Google Chrome or Chromium, with compatible browser-driver dependencies if required
- Git LFS, if the repository stores model weights using LFS

### Installation

**1. Clone the repository**

```bash
git clone <YOUR_REV​​CHECK_REPOSITORY_URL>
cd RevCheck
```

Replace the placeholder with your actual GitHub repository URL.

**2. Create a virtual environment**

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

On macOS or Linux:

```bash
source venv/bin/activate
```

**3. Install dependencies**

If your repository includes a `requirements.txt` file:

```bash
pip install -r requirements.txt
```

**4. Download model files**

Ensure the fine-tuned DistilRoBERTa model and tokenizer files are available at the paths expected by the application. If they are stored using Git LFS, install Git LFS and pull the required files:

```bash
git lfs install
git lfs pull
```

**5. Configure environment variables**

Set any required configuration values, such as model paths or API settings, according to your project configuration. Do not commit secret keys or credentials.

**6. Run the application**

Use the Flask entry point configured in your repository. For example, if your main file is `app.py`:

```bash
python app.py
```

Open the local URL displayed in your terminal.

> The commands above assume a conventional Flask project structure. Adjust the entry point, dependencies, model paths, and browser configuration to match your actual repository.

## 📥 Input Options

RevCheck is designed to support multiple review-analysis workflows:

- **Single Review:** Analyze an individual review's text.
- **Hotel URL:** Collect and analyze available reviews from a supported Booking.com page.
- **CSV Upload:** Process a collection of reviews in bulk.

The exact input fields and supported CSV columns depend on the application's implementation.

## 🔒 Responsible Use

- Model predictions are estimates, not definitive proof of fraud.
- Contextual inconsistencies can result from genuine changes in service or individual experiences.
- Scraping functionality must comply with the target website's terms, access restrictions, and applicable laws.
- Avoid submitting sensitive personal information unnecessarily.
- Review results should be interpreted alongside other relevant evidence.

## 🔮 Future Enhancements

- Support additional hotel and e-commerce review platforms.
- Improve contextual analysis using aspect-based sentiment analysis.
- Add interactive visualizations for fake-review trends and consensus patterns.
- Introduce explainability features to highlight text patterns influencing predictions.
- Add historical review storage and hotel-specific consensus tracking.
- Optimize inference latency and support scalable batch processing.
- Expand model evaluation using precision, recall, F1-score, and confusion matrices.

## 🤝 Contributing

Contributions, suggestions, and bug reports are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes with a descriptive message.
4. Open a pull request describing your changes.


⭐ If you find RevCheck useful, consider giving the repository a star!
