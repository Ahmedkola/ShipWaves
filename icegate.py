from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
import easyocr
import time

reader = easyocr.Reader(['en'])

options = Options()
options.add_argument("--headless=new")  
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920x1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

app = Flask(__name__)

@app.route('/track_sb', methods=['POST'])
def track_sb():
    
    data = request.json
    selected_location = data.get('location')
    sb_number = data.get('sb_number')
    date_input = data.get('date')

    # Validate inputs
    if not selected_location:
        return jsonify({"error": "Location is required."}), 400

    if not sb_number or not sb_number.isdigit():
        return jsonify({"error": "Invalid Bill No. (SB Number). Please enter digits only."}), 400

    if not date_input or len(date_input) != 8 or not date_input.isdigit():
        return jsonify({"error": "Invalid Date format! Please enter exactly 8 digits in DDMMYYYY format."}), 400

    # Parse date
    day, month, year = date_input[:2], date_input[2:4], date_input[4:]

    # Initialize Selenium WebDriver
    driver = webdriver.Chrome(options=options)
    driver.get("https://enquiry.icegate.gov.in/enquiryatices/sbTrack")

    # Check for website errors
    page_content = driver.page_source.lower()
    if "an error occurred while processing your request" in page_content or "proxy error" in page_content:
        driver.quit()
        return jsonify({"error": "Website is not available at the moment. Please try again later."}), 503

    # Fill the form
    try:
        location_dropdown = Select(driver.find_element(By.ID, "location"))
        location_dropdown.select_by_visible_text(selected_location)
    except NoSuchElementException:
        driver.quit()
        return jsonify({"error": f"Location '{selected_location}' not found in the dropdown."}), 400

    text_box = driver.find_element(By.ID, "sbNO")
    text_box.send_keys(sb_number)

    # Handle CAPTCHA
    while True:
        # Enter Date
        date_icon = driver.find_element(By.XPATH, "//img[@src='/enquiryatices/image/Dateicon.gif']")
        date_icon.click()
        time.sleep(1)

        year_dropdown = Select(driver.find_element(By.NAME, "calendar-year"))
        year_dropdown.select_by_value(year)

        month_dropdown = Select(driver.find_element(By.NAME, "calendar-month"))
        month_dropdown.select_by_value(str(int(month) - 1))

        time.sleep(1)
        date_xpath = f"//td[@onclick=\"updateDateField('SB_DT', '{year}/{month}/{day}');\"]"
        driver.find_element(By.XPATH, date_xpath).click()

        # Solve CAPTCHA
        captcha_img = driver.find_element(By.ID, "capimg")
        captcha_img.screenshot("captcha.png")

        # Read CAPTCHA using EasyOCR
        result = reader.readtext("captcha.png")
        captcha_text = result[0][1].strip() if result else ""

        captcha_input = driver.find_element(By.ID, "captchaResp")
        captcha_input.clear()
        captcha_input.send_keys(captcha_text)

        submit_button = driver.find_element(By.ID, "SubB")
        submit_button.click()
        time.sleep(3)

        # Check for CAPTCHA errors
        try:
            driver.find_element(By.XPATH, "//*[contains(text(), 'Invalid captcha')]")
            driver.find_element(By.XPATH, "//img[@src='/enquiryatices/image/reload.gif']").click()
            time.sleep(2)
            continue  # Restart loop if CAPTCHA fails
        except NoSuchElementException:
            pass

        try:
            driver.find_element(By.XPATH, "//span[contains(text(), 'Invalid Code! Please try again!')]")
            driver.find_element(By.XPATH, "//img[@src='/enquiryatices/image/reload.gif']").click()
            time.sleep(2)
            continue  # Restart loop if CAPTCHA fails
        except NoSuchElementException:
            break  # Exit loop if CAPTCHA is correct

    time.sleep(3)  # Wait for the page to load

    # Extract table data
    if driver.current_url == "https://enquiry.icegate.gov.in/enquiryatices/SBTrack_Ices_action":
        try:
            egm_button = driver.find_element(By.XPATH, "//a[@class='page_button'][contains(span, 'EGM Status')]")
            egm_button.click()
            time.sleep(3)  # Wait for the table to load

            # Extract table data
            table_rows = driver.find_elements(By.XPATH, "//table//tr[position()>1]")  # Skip header
            table_data = []

            for row in table_rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 5:
                    # Extract clean data from each cell
                    egm_no = cells[0].text.strip()
                    egm_date = cells[1].text.strip()
                    container_no = cells[2].text.strip()
                    seal_no = cells[3].text.strip()
                    error_message = cells[4].text.strip()

                    # Ensure the row does not contain header data
                    if "EGM No." not in egm_no and "Container No." not in container_no:
                        clean_row = {
                            "egm_no": egm_no,
                            "egm_date": egm_date,
                            "container_no": container_no,
                            "seal_no": seal_no,
                            "error_message": error_message
                        }
                        table_data.append(clean_row)

            driver.quit()
            return jsonify({"status": "success", "data": table_data})

        except NoSuchElementException:
            driver.quit()
            return jsonify({"error": "EGM Status button not found."}), 404

    driver.quit()
    return jsonify({"error": "Unexpected error occurred."}), 500


if __name__ == '__main__':
    app.run(debug=True)
