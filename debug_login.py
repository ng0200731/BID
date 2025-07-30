"""
Debug script to inspect the login page and find correct selectors
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def debug_login_page():
    """Debug the login page to find correct selectors"""
    
    # Setup Chrome
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
        driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("Opening login page...")
        driver.get("https://app.e-brandid.com/login/login.aspx")
        time.sleep(5)
        
        print("\n=== PAGE SOURCE ANALYSIS ===")
        
        # Find all input elements
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"\nFound {len(inputs)} input elements:")
        for i, inp in enumerate(inputs):
            inp_type = inp.get_attribute("type")
            inp_name = inp.get_attribute("name")
            inp_id = inp.get_attribute("id")
            inp_value = inp.get_attribute("value")
            inp_class = inp.get_attribute("class")
            print(f"  {i+1}. Type: {inp_type}, Name: {inp_name}, ID: {inp_id}, Value: {inp_value}, Class: {inp_class}")
        
        # Find all button elements
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"\nFound {len(buttons)} button elements:")
        for i, btn in enumerate(buttons):
            btn_type = btn.get_attribute("type")
            btn_name = btn.get_attribute("name")
            btn_id = btn.get_attribute("id")
            btn_text = btn.text
            btn_class = btn.get_attribute("class")
            print(f"  {i+1}. Type: {btn_type}, Name: {btn_name}, ID: {btn_id}, Text: '{btn_text}', Class: {btn_class}")
        
        # Find all form elements
        forms = driver.find_elements(By.TAG_NAME, "form")
        print(f"\nFound {len(forms)} form elements:")
        for i, form in enumerate(forms):
            form_action = form.get_attribute("action")
            form_method = form.get_attribute("method")
            form_id = form.get_attribute("id")
            print(f"  {i+1}. Action: {form_action}, Method: {form_method}, ID: {form_id}")
        
        print("\n=== TRYING TO FIND LOGIN ELEMENTS ===")
        
        # Try to find username field
        username_selectors = [
            "input[type='text']",
            "input[name*='user']",
            "input[name*='User']",
            "input[id*='user']",
            "input[id*='User']",
            "input[name*='name']",
            "input[name*='Name']"
        ]
        
        for selector in username_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"✅ Username field found with: {selector}")
                print(f"   Element details: name={element.get_attribute('name')}, id={element.get_attribute('id')}")
                break
            except:
                print(f"❌ Username field NOT found with: {selector}")
        
        # Try to find password field
        try:
            password_element = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            print(f"✅ Password field found")
            print(f"   Element details: name={password_element.get_attribute('name')}, id={password_element.get_attribute('id')}")
        except:
            print(f"❌ Password field NOT found")
        
        # Try to find login button
        login_selectors = [
            "input[type='submit']",
            "button[type='submit']",
            "input[value*='LOGIN']",
            "input[value*='Login']",
            "input[value*='login']",
            "button",
            "input[type='button']"
        ]

        for selector in login_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"✅ Login button candidates found with: {selector}")
                    for i, elem in enumerate(elements):
                        value = elem.get_attribute('value')
                        text = elem.text
                        name = elem.get_attribute('name')
                        id_attr = elem.get_attribute('id')
                        print(f"   Candidate {i+1}: value='{value}', text='{text}', name='{name}', id='{id_attr}'")
                else:
                    print(f"❌ No elements found with: {selector}")
            except Exception as e:
                print(f"❌ Error with selector {selector}: {e}")

        print("\n=== SEARCHING FOR ALL CLICKABLE ELEMENTS ===")

        # Find all elements with onclick
        onclick_elements = driver.find_elements(By.XPATH, "//*[@onclick]")
        print(f"\nFound {len(onclick_elements)} elements with onclick:")
        for i, elem in enumerate(onclick_elements):
            tag = elem.tag_name
            onclick = elem.get_attribute('onclick')
            text = elem.text.strip()
            id_attr = elem.get_attribute('id')
            class_attr = elem.get_attribute('class')
            print(f"  {i+1}. Tag: {tag}, Text: '{text}', ID: {id_attr}, Class: {class_attr}, OnClick: {onclick}")

        # Find all div elements (might be styled as buttons)
        divs = driver.find_elements(By.TAG_NAME, "div")
        clickable_divs = []
        for div in divs:
            text = div.text.strip().lower()
            if any(word in text for word in ['login', 'submit', 'sign in', 'enter']):
                clickable_divs.append(div)

        print(f"\nFound {len(clickable_divs)} potential clickable divs:")
        for i, div in enumerate(clickable_divs):
            text = div.text.strip()
            id_attr = div.get_attribute('id')
            class_attr = div.get_attribute('class')
            onclick = div.get_attribute('onclick')
            print(f"  {i+1}. Text: '{text}', ID: {id_attr}, Class: {class_attr}, OnClick: {onclick}")

        # Find all span elements
        spans = driver.find_elements(By.TAG_NAME, "span")
        clickable_spans = []
        for span in spans:
            text = span.text.strip().lower()
            if any(word in text for word in ['login', 'submit', 'sign in', 'enter']):
                clickable_spans.append(span)

        print(f"\nFound {len(clickable_spans)} potential clickable spans:")
        for i, span in enumerate(clickable_spans):
            text = span.text.strip()
            id_attr = span.get_attribute('id')
            class_attr = span.get_attribute('class')
            onclick = span.get_attribute('onclick')
            print(f"  {i+1}. Text: '{text}', ID: {id_attr}, Class: {class_attr}, OnClick: {onclick}")

        # Check if form can be submitted by pressing Enter
        print(f"\n=== FORM SUBMISSION TEST ===")
        try:
            form = driver.find_element(By.TAG_NAME, "form")
            print(f"Form found with ID: {form.get_attribute('id')}")
            print("Trying to submit form by pressing Enter on password field...")

            # Fill in test credentials
            username_field = driver.find_element(By.ID, "txtUserName")
            password_field = driver.find_element(By.ID, "txtPassword")

            username_field.clear()
            username_field.send_keys("test")
            password_field.clear()
            password_field.send_keys("test")

            from selenium.webdriver.common.keys import Keys
            password_field.send_keys(Keys.RETURN)

            time.sleep(3)
            current_url = driver.current_url
            print(f"After pressing Enter, URL is: {current_url}")

        except Exception as e:
            print(f"Form submission test failed: {e}")
        
        print("\n=== MANUAL INSPECTION ===")
        print("Browser window is open. Please manually inspect the page.")
        print("Press Enter when you're done inspecting...")
        input()
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_login_page()
