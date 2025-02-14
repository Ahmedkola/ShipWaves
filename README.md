# Flask Shipping Bill Tracker

This Flask application automates the tracking of Shipping Bills (SB) using Selenium and OCR-based CAPTCHA solving.

## Features
- Tracks Shipping Bills from the ICEGATE website.
- Uses Selenium for web scraping.
- Uses EasyOCR for CAPTCHA recognition.
- Returns EGM status in JSON format.

## Prerequisites
Make sure you have the following installed before proceeding:

- Python (>=3.8)
- Google Chrome
- ChromeDriver (compatible with your Chrome version)
- Virtual environment (recommended)

## Installation

### 1. Clone the Repository
```sh
[git clone https://github.com/yourusername/shipping-bill-tracker.git
cd shipping-bill-tracker](https://github.com/Ahmedkola/ShipWaves.git)
```

### 2. Create and Activate a Virtual Environment
#### Windows:
```sh
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux:
```sh
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```sh
pip install -r requirements.txt
```

### 4. Install ChromeDriver
Download ChromeDriver from [ChromeDriver Download Page](https://sites.google.com/chromium.org/driver/) and ensure it matches your Chrome version. Add it to your system's PATH.

### 5. Run the Flask App
```sh
python icegate.py
```

## API Usage
## Use Postman(optional)
### Endpoint: `/track_sb`
#### Method: `POST`

#### Request JSON Format:
```json
{
  "location":  "VIZAG SEA (INVTZ1)",
  "sb_number": "6960808",
  "date": "02012025"
}
```

#### Example cURL Request:
```sh
curl -X POST "http://127.0.0.1:5000/track_sb" -H "Content-Type: application/json" -d '{
  "location": "VIZAG SEA (INVTZ1)",
  "sb_number": "6960808",
  "date": "02122025"
}'
```

#### Sample Response (Success):
```json
{
  "status": "success",
  "data": [
    {
      "egm_no": "123456",
      "egm_date": "02-01-2024",
      "container_no": "XYZ1234",
      "seal_no": "SEAL5678",
      "error_message": "No error"
    }
  ]
}
```

#### Sample Response (Error):
```json
{
  "error": "Invalid Bill No. (SB Number). Please enter digits only."
}
```





---
For any issues, feel free to open an issue in the repository.

