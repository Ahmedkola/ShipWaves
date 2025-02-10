import tkinter as tk
from tkinter import ttk, messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from PIL import Image
import easyocr
import time
import re

# Initialize EasyOCR
reader = easyocr.Reader(['en'])

# Selenium options for headless execution
options = Options()
options.add_argument("--headless=new")  # Fully headless mode
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920x1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Locations list
locations = [
    "ICDPLIL GHUNGRANA (INGPL6)",
    "ACC KANNUR (INCNN4)",
    "ACC MOPA (INGOX4)",
    "AFS Kapashera (INBWS6)",
    "AGARTALA LCS (INAGTB)",
    "VIZAG SEA (INVTZ1)",
    "AHEMDABAD AIR ACC (INAMD4)"
]

def submit_form():
    selected_location = location_combobox.get()
    if selected_location == "":
        messagebox.showerror("Error", "Please select a location.")
        return

    sb_number = sb_number_entry.get().strip()
    if not sb_number.isdigit():
        messagebox.showerror("Error", "Invalid Bill No. (SB Number). Please enter digits only.")
        return

    date_input = date_entry.get().strip()
    if len(date_input) != 8 or not date_input.isdigit():
        messagebox.showerror("Error", "Invalid Date format! Please enter exactly 8 digits in DDMMYYYY format.")
        return
    
    day, month, year = date_input[:2], date_input[2:4], date_input[4:]

    driver = webdriver.Chrome(options=options)  # Headless browser
    driver.get("https://enquiry.icegate.gov.in/enquiryatices/sbTrack")

    # Check for website errors
    page_content = driver.page_source.lower()
    if "an error occurred while processing your request" in page_content or "proxy error" in page_content:
        messagebox.showerror("Error", "Website is not available at the moment. Please try again later.")
        driver.quit()
        return

    location_dropdown = Select(driver.find_element(By.ID, "location"))
    location_dropdown.select_by_visible_text(selected_location)

    text_box = driver.find_element(By.ID, "sbNO")
    text_box.send_keys(sb_number)

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

    if driver.current_url == "https://enquiry.icegate.gov.in/enquiryatices/SBTrack_Ices_action":
        try:
            egm_button = driver.find_element(By.XPATH, "//a[@class='page_button'][contains(span, 'EGM Status')]")
            egm_button.click()
            time.sleep(3)  # Wait for the table to load

            # Extract table data
            # Extract table data correctly
            table_rows = driver.find_elements(By.XPATH, "//table//tr[position()>1]")  # Skip header
            table_data = []
            
            for row in table_rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 5:
                    clean_row = [
                        cells[0].text.strip(),  # EGM No.
                        cells[1].text.strip(),  # EGM Date
                        cells[2].text.strip(),  # Container No.
                        cells[3].text.strip(),  # Seal No.
                        cells[4].text.strip()   # Error Message
                    ]
                    
                    # Ensure the first row is not a combined header         
                    if "EGM No." not in clean_row[0]:  
                        table_data.append(clean_row)

            # Call GUI function to display cleaned table data
            show_table(table_data)


        except NoSuchElementException:
            messagebox.showerror("Error", "EGM Status button not found.")
    
    driver.quit()

def show_table(data):
    table_window = tk.Toplevel(root)
    table_window.title("EGM Status Table")

    columns = ["EGM No.", "EGM Date", "Container No.", "Seal No.", "Error Message"]
    tree = ttk.Treeview(table_window, columns=columns, show="headings")  # Remove the first column

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center")

    for row in data:
        tree.insert("", "end", values=row)

    tree.pack(expand=True, fill="both")
# Tkinter GUI
root = tk.Tk()
root.title("Selenium Automation with CAPTCHA Solver")

tk.Label(root, text="Select a Location:").grid(row=0, column=0, padx=10, pady=10)
location_combobox = ttk.Combobox(root, values=locations, state="normal", width=40)
location_combobox.grid(row=0, column=1, padx=10, pady=10)

tk.Label(root, text="Enter Bill No. (SB Number):").grid(row=1, column=0, padx=10, pady=10)
sb_number_entry = tk.Entry(root, width=40)
sb_number_entry.grid(row=1, column=1, padx=10, pady=10)

tk.Label(root, text="Enter Date (DDMMYYYY):").grid(row=2, column=0, padx=10, pady=10)
date_entry = tk.Entry(root, width=40)
date_entry.grid(row=2, column=1, padx=10, pady=10)

submit_button = tk.Button(root, text="Submit", command=submit_form, width=20)
submit_button.grid(row=3, column=0, columnspan=2, pady=20)

root.mainloop()
