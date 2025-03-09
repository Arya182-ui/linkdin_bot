from __future__ import annotations
import json
import csv
import logging
import os
import random
import re
import time
from datetime import datetime, timedelta
import getpass
from pathlib import Path
import pandas as pd
import pyautogui
import yaml
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service as ChromeService
import webdriver_manager.chrome as ChromeDriverManager
ChromeDriverManager = ChromeDriverManager.ChromeDriverManager

# Arya: This sets up our logging—super useful for tracking what’s happening!
log = logging.getLogger(__name__)

def setupLogger() -> None:
    # Arya: Creating a timestamped log file to save everything
    dt: str = datetime.strftime(datetime.now(), "%m_%d_%y %H_%M_%S ")
    if not os.path.isdir('./logs'):
        os.mkdir('./logs')
    
    # Arya: Setting up the log format—file output
    logging.basicConfig(
        filename=('./logs/' + str(dt) + 'applyJobs.log'),
        filemode='w',
        format='%(asctime)s::%(name)s::%(levelname)s::%(message)s',
        datefmt='./logs/%d-%b-%y %H:%M:%S'
    )
    log.setLevel(logging.DEBUG)
    
    # Arya: Adding console output so you can watch live
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.DEBUG)
    c_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%H:%M:%S')
    c_handler.setFormatter(c_format)
    log.addHandler(c_handler)

class EasyApplyBot:
    # Arya: Our awesome job application bot—MAX_SEARCH_TIME limits runtime
    setupLogger()
    MAX_SEARCH_TIME = 60 * 60  # 1 hour for now, originally 10 hours

    def __init__(self, username, password, phone_number, profile_path=None, salary=None, rate=None,
                 uploads={}, filename='output.csv', blacklist=[],
                 blackListTitles=[], experience_level=[]) -> None:
        # Arya: Initializing the bot with your settings—profile_path is now optional!
        log.info("Welcome to Easy Apply Bot, Arya!")
        dirpath: str = os.getcwd()
        log.info(f"Arya, we’re running from: {dirpath}")
        log.info("Arya, setting up the bot—hang on!")
        
        # Arya: Showing which experience levels we’re targeting
        if experience_level:
            experience_levels = {
                1: "Entry level", 2: "Associate", 3: "Mid-Senior level",
                4: "Director", 5: "Executive", 6: "Internship"
            }
            applied_levels = [experience_levels[level] for level in experience_level]
            log.info(f"Arya, targeting experience levels: {', '.join(applied_levels)}")
        else:
            log.info("Arya, going for all experience levels!")
        
        # Arya: Setting up all variables—profile_path defaults to None if not provided
        self.uploads = uploads
        self.salary = salary
        self.rate = rate
        self.profile_path = profile_path if profile_path else os.path.expanduser("~/.config/chrome-profile")
        past_ids: list | None = self.get_appliedIDs(filename)
        self.appliedJobIDs: list = past_ids if past_ids is not None else []
        self.filename: str = filename
        self.options = self.browser_options()
        
        # Arya: Starting Chrome with WebDriver
        try:
            self.browser = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
                options=self.options
            )
            self.wait = WebDriverWait(self.browser, 30)
        except Exception as e:
            log.error(f"Arya, couldn’t start the browser: {str(e)}")
            raise
        
        self.blacklist = blacklist
        self.blackListTitles = blackListTitles
        self.start_linkedin(username, password)
        self.phone_number = phone_number
        self.experience_level = experience_level

        # Arya: Locators for finding elements on LinkedIn pages
        self.locator = {
            "next": (By.CSS_SELECTOR, "button[aria-label='Continue to next step']"),
            "review": (By.CSS_SELECTOR, "button[aria-label='Review your application']"),
            "submit": (By.CSS_SELECTOR, "button[aria-label='Submit application']"),
            "error": (By.CLASS_NAME, "artdeco-inline-feedback__message"),
            "upload_resume": (By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-resume')]"),
            "upload_cv": (By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-cover-letter')]"),
            "follow": (By.CSS_SELECTOR, "label[for='follow-company-checkbox']"),
            "upload": (By.NAME, "file"),
            "search": (By.CLASS_NAME, "jobs-search-results-list"),
            "links": ("xpath", '//div[@data-job-id]'),
            "fields": (By.CLASS_NAME, "jobs-easy-apply-form-section__grouping"),
            "radio_select": (By.CSS_SELECTOR, "input[type='radio']"),
            "multi_select": (By.XPATH, "//*[contains(@id, 'text-entity-list-form-component')]"),
            "text_select": (By.CLASS_NAME, "artdeco-text-input--input"),
            "2fa_oneClick": (By.ID, 'reset-password-submit-button'),
            "easy_apply_button": (By.XPATH, '//button[contains(@class, "jobs-apply-button")]')
        }

        # Arya: Setting up the Q&A file for form questions
        self.qa_file = Path("qa.csv")
        self.answers = {}
        if self.qa_file.is_file():
            df = pd.read_csv(self.qa_file)
            for index, row in df.iterrows():
                self.answers[row['Question']] = row['Answer']
        else:
            df = pd.DataFrame(columns=["Question", "Answer"])
            df.to_csv(self.qa_file, index=False, encoding='utf-8')

    def get_appliedIDs(self, filename) -> list | None:
        # Arya: Loading job IDs we’ve already applied to
        try:
            df = pd.read_csv(filename,
                            header=None,
                            names=['timestamp', 'jobID', 'job', 'company', 'attempted', 'result'],
                            lineterminator='\n',
                            encoding='utf-8')
            df['timestamp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H:%M:%S")
            df = df[df['timestamp'] > (datetime.now() - timedelta(days=2))]
            jobIDs: list = list(df.jobID)
            log.info(f"Arya, loaded {len(jobIDs)} jobIDs from recent applications")
            return jobIDs
        except Exception as e:
            log.info(f"Arya, failed to load jobIDs from {filename}: {str(e)}")
            return None

    def browser_options(self):
        # Arya: Setting up Chrome options to avoid detection
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")
        # Arya: Using profile_path if provided
        if self.profile_path:
            options.add_argument(f"--user-data-dir={self.profile_path}")
        return options

    def start_linkedin(self, username, password) -> None:
        # Arya: Logging into LinkedIn—let’s get in there!
        log.info("Arya, logging in—please wait :)")
        self.browser.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
        try:
            user_field = self.browser.find_element("id", "username")
            pw_field = self.browser.find_element("id", "password")
            login_button = self.browser.find_element("xpath",
                        '//*[@id="organic-div"]/form/div[3]/button')
            user_field.send_keys(username)
            user_field.send_keys(Keys.TAB)
            time.sleep(2)
            pw_field.send_keys(password)
            time.sleep(2)
            login_button.click()
            time.sleep(15)
            # Arya: Handling 2FA if it pops up
            if self.is_present(self.locator["2fa_oneClick"]):
                oneclick_auth = self.browser.find_element(by='id', value='reset-password-submit-button')
                if oneclick_auth is not None:
                    log.info("Arya, 2FA needed—sleeping 15s for you to handle")
                    time.sleep(15)
            log.info("Arya, we’re logged in!")
        except TimeoutException:
            log.info("Arya, timeout—couldn’t find login fields!")

    def fill_data(self) -> None:
        # Arya: Minimizing the window so it’s out of your way
        self.browser.set_window_size(1, 1)
        self.browser.set_window_position(2000, 2000)

    def start_apply(self, positions, locations) -> None:
        # Arya: Starting the job application process—here we go!
        start: float = time.time()
        self.fill_data()
        self.positions = positions
        self.locations = locations
        combos: list = []
        while len(combos) < len(positions) * len(locations):
            position = positions[random.randint(0, len(positions) - 1)]
            location = locations[random.randint(0, len(locations) - 1)]
            combo: tuple = (position, location)
            if combo not in combos:
                combos.append(combo)
                log.info(f"Arya, targeting {position} in {location}")
                location = "&location=" + location
                self.applications_loop(position, location)
            if len(combos) > 500:
                break

    def applications_loop(self, position, location):
        # Arya: Looping through job listings to find matches
        count_application = 0
        count_job = 0
        jobs_per_page = 0
        start_time: float = time.time()

        log.info("Arya, searching for jobs—be patient!")
        self.browser.set_window_position(1, 1)
        self.browser.maximize_window()
        self.browser, _ = self.next_jobs_page(position, location, jobs_per_page, experience_level=self.experience_level)
        log.info("Arya, still hunting—hold on!")

        while time.time() - start_time < self.MAX_SEARCH_TIME:
            try:
                log.info(f"Arya, {(self.MAX_SEARCH_TIME - (time.time() - start_time)) // 60} minutes remaining")
                randoTime: float = random.uniform(1.5, 2.9)
                log.debug(f"Arya, pausing for {round(randoTime, 1)}s to seem human")
                time.sleep(randoTime)
                self.load_page(sleep=0.5)

                # Arya: Scrolling to load all jobs
                if self.is_present(self.locator["search"]):
                    scrollresults = self.get_elements("search")
                    for i in range(300, 3000, 100):
                        self.browser.execute_script("arguments[0].scrollTo(0, {})".format(i), scrollresults[0])
                    scrollresults = self.get_elements("search")
                    time.sleep(1)

                # Arya: Gathering job links
                if self.is_present(self.locator["links"]):
                    links = self.get_elements("links")
                    jobIDs = {}
                    for link in links:
                        if 'Applied' not in link.text:
                            if link.text not in self.blacklist:
                                jobID = link.get_attribute("data-job-id")
                                if jobID == "search":
                                    log.debug(f"Arya, got 'search' instead of jobID: {link.text}")
                                    continue
                                else:
                                    jobIDs[jobID] = "To be processed"
                    if len(jobIDs) > 0:
                        self.apply_loop(jobIDs)
                    self.browser, jobs_per_page = self.next_jobs_page(position,
                                                                    location,
                                                                    jobs_per_page, 
                                                                    experience_level=self.experience_level)
                else:
                    self.browser, jobs_per_page = self.next_jobs_page(position,
                                                                    location,
                                                                    jobs_per_page, 
                                                                    experience_level=self.experience_level)
            except Exception as e:
                log.error(f"Arya, hit an issue in the loop: {str(e)}")

    def apply_loop(self, jobIDs):
        # Arya: Applying to each job one by one
        for jobID in jobIDs:
            if jobIDs[jobID] == "To be processed":
                applied = self.apply_to_job(jobID)
                if applied:
                    log.info(f"Arya, applied to {jobID}")
                else:
                    log.info(f"Arya, couldn’t apply to {jobID}")
                jobIDs[jobID] = applied

    def apply_to_job(self, jobID):
        # Arya: Applying to a specific job—let’s do this!
        self.get_job_page(jobID)
        time.sleep(1)
        button = self.get_easy_apply_button()

        if button is not False:
            if any(word in self.browser.title for word in self.blackListTitles):
                log.info('Arya, skipping—found a blacklisted title')
                string_easy = "* Contains blacklisted keyword"
                result = False
            else:
                string_easy = "* has Easy Apply Button"
                log.info("Arya, clicking Easy Apply!")
                button.click()
                clicked = True
                time.sleep(1)
                self.fill_out_fields()
                result: bool = self.send_resume()
                if result:
                    string_easy = "*Applied: Sent Resume"
                else:
                    string_easy = "*Did not apply: Failed to send Resume"
        elif "You applied on" in self.browser.page_source:
            log.info("Arya, already applied to this job!")
            string_easy = "* Already Applied"
            result = False
        else:
            log.info("Arya, no Easy Apply button found")
            string_easy = "* Doesn't have Easy Apply Button"
            result = False

        log.info(f"\nArya, Position {jobID}:\n {self.browser.title} \n {string_easy} \n")
        self.write_to_file(button, jobID, self.browser.title, result)
        return result

    def write_to_file(self, button, jobID, browserTitle, result) -> None:
        # Arya: Writing application details to our CSV file
        def re_extract(text, pattern):
            target = re.search(pattern, text)
            if target:
                target = target.group(1)
            return target

        timestamp: str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        attempted: bool = False if button == False else True
        job = re_extract(browserTitle.split(' | ')[0], r"\(?\d?\)?\s?(\w.*)")
        company = re_extract(browserTitle.split(' | ')[1], r"(\w.*)")

        toWrite: list = [timestamp, jobID, job, company, attempted, result]
        with open(self.filename, 'a+') as f:
            writer = csv.writer(f)
            writer.writerow(toWrite)

    def get_job_page(self, jobID):
        # Arya: Loading the job page we want to apply to
        job: str = 'https://www.linkedin.com/jobs/view/' + str(jobID)
        self.browser.get(job)
        self.job_page = self.load_page(sleep=0.5)
        return self.job_page

    def get_easy_apply_button(self):
        # Arya: Looking for that Easy Apply button!
        EasyApplyButton = False
        try:
            buttons = self.get_elements("easy_apply_button")
            for button in buttons:
                if "Easy Apply" in button.text:
                    EasyApplyButton = button
                    self.wait.until(EC.element_to_be_clickable(EasyApplyButton))
                else:
                    log.debug("Arya, no Easy Apply in this button")
        except Exception as e: 
            log.debug(f"Arya, error finding Easy Apply: {str(e)}")
        return EasyApplyButton

    def fill_out_fields(self):
        # Arya: Filling out basic form fields like phone number
        fields = self.browser.find_elements(By.CLASS_NAME, "jobs-easy-apply-form-section__grouping")
        for field in fields:
            if "Mobile phone number" in field.text:
                field_input = field.find_element(By.TAG_NAME, "input")
                field_input.clear()
                field_input.send_keys(self.phone_number)

    def get_elements(self, type) -> list:
        # Arya: Getting multiple elements from the page
        elements = []
        element = self.locator[type]
        if self.is_present(element):
            elements = self.browser.find_elements(element[0], element[1])
        return elements

    def is_present(self, locator):
        # Arya: Checking if an element is on the page
        return len(self.browser.find_elements(locator[0], locator[1])) > 0

    def send_resume(self) -> bool:
        # Arya: Submitting the application with resume and cover letter
        def is_present(button_locator) -> bool:
            return len(self.browser.find_elements(button_locator[0], button_locator[1])) > 0

        try:
            next_locator = (By.CSS_SELECTOR, "button[aria-label='Continue to next step']")
            review_locator = (By.CSS_SELECTOR, "button[aria-label='Review your application']")
            submit_locator = (By.CSS_SELECTOR, "button[aria-label='Submit application']")
            error_locator = (By.CLASS_NAME, "artdeco-inline-feedback__message")
            upload_resume_locator = (By.XPATH, '//span[text()="Upload resume"]')
            upload_cv_locator = (By.XPATH, '//span[text()="Upload cover letter"]')
            follow_locator = (By.CSS_SELECTOR, "label[for='follow-company-checkbox']")

            submitted = False
            loop = 0
            while loop < 2:
                time.sleep(1)
                if is_present(upload_resume_locator):
                    try:
                        resume_locator = self.browser.find_element(By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-resume')]")
                        resume = self.uploads["Resume"]
                        resume_locator.send_keys(resume)
                        log.info("Arya, uploaded resume!")
                    except Exception as e:
                        log.error(f"Arya, resume upload failed: {str(e)}")
                
                if is_present(upload_cv_locator):
                    cv = self.uploads["Cover Letter"]
                    cv_locator = self.browser.find_element(By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-cover-letter')]")
                    cv_locator.send_keys(cv)
                    log.info("Arya, uploaded cover letter!")

                elif len(self.get_elements("follow")) > 0:
                    elements = self.get_elements("follow")
                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        button.click()
                        log.info("Arya, clicked follow company!")

                if len(self.get_elements("submit")) > 0:
                    elements = self.get_elements("submit")
                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        button.click()
                        log.info("Arya, application submitted!")
                        submitted = True
                        break

                elif len(self.get_elements("error")) > 0:
                    elements = self.get_elements("error")
                    if "application was sent" in self.browser.page_source:
                        log.info("Arya, application confirmed sent!")
                        submitted = True
                        break
                    elif len(elements) > 0:
                        while len(elements) > 0:
                            log.info("Arya, questions detected—waiting 5s...")
                            time.sleep(5)
                            elements = self.get_elements("error")
                            for element in elements:
                                self.process_questions()
                            if "application was sent" in self.browser.page_source:
                                log.info("Arya, submitted after questions!")
                                submitted = True
                                break
                            elif is_present(self.locator["easy_apply_button"]):
                                log.info("Arya, skipping this one")
                                submitted = False
                                break
                        continue

                elif len(self.get_elements("next")) > 0:
                    elements = self.get_elements("next")
                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        button.click()
                        log.info("Arya, moving to next step!")

                elif len(self.get_elements("review")) > 0:
                    elements = self.get_elements("review")
                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        button.click()
                        log.info("Arya, reviewing application!")

                elif len(self.get_elements("follow")) > 0:
                    elements = self.get_elements("follow")
                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        button.click()

                loop += 1
        except Exception as e:
            log.error(f"Arya, submission error: {str(e)}")
        return submitted

    def process_questions(self):
        # Arya: Handling extra questions in the application
        time.sleep(1)
        form = self.get_elements("fields")
        for field in form:
            question = field.text
            answer = self.ans_question(question.lower())
            if self.is_present(self.locator["radio_select"]):
                try:
                    input = field.find_element(By.CSS_SELECTOR, "input[type='radio'][value={}]".format(answer))
                    input.execute_script("arguments[0].click();", input)
                except Exception as e:
                    log.error(f"Arya, radio button issue: {str(e)}")
                    continue
            elif self.is_present(self.locator["multi_select"]):
                try:
                    input = field.find_element(self.locator["multi_select"])
                    input.send_keys(answer)
                except Exception as e:
                    log.error(f"Arya, multi-select issue: {str(e)}")
                    continue
            elif self.is_present(self.locator["text_select"]):
                try:
                    input = field.find_element(self.locator["text_select"])
                    input.send_keys(answer)
                except Exception as e:
                    log.error(f"Arya, text input issue: {str(e)}")
                    continue
            elif self.is_present(self.locator["text_select"]):
                pass

            if "Yes" or "No" in answer:
                try:
                    input = form.find_element(By.CSS_SELECTOR, "input[type='radio'][value={}]".format(answer))
                    form.execute_script("arguments[0].click();", input)
                except:
                    pass
            else:
                input = form.find_element(By.CLASS_NAME, "artdeco-text-input--input")
                input.send_keys(answer)

    def ans_question(self, question):
        # Arya: Auto-answering questions—basic logic here
        answer = None
        if "how many" in question:
            answer = "1"
        elif "experience" in question:
            answer = "1"
        elif "sponsor" in question:
            answer = "No"
        elif 'do you ' in question:
            answer = "Yes"
        elif "have you " in question:
            answer = "Yes"
        elif "US citizen" in question:
            answer = "Yes"
        elif "are you " in question:
            answer = "Yes"
        elif "salary" in question:
            answer = self.salary
        elif "can you" in question:
            answer = "Yes"
        elif "gender" in question:
            answer = "Male"
        elif "race" in question:
            answer = "Wish not to answer"
        elif "lgbtq" in question:
            answer = "Wish not to answer"
        elif "ethnicity" in question:
            answer = "Wish not to answer"
        elif "nationality" in question:
            answer = "Wish not to answer"
        elif "government" in question:
            answer = "I do not wish to self-identify"
        elif "are you legally" in question:
            answer = "Yes"
        else:
            log.info("Arya, unknown question—please answer manually!")
            answer = "user provided"
            time.sleep(15)

        if question not in self.answers:
            self.answers[question] = answer
            new_data = pd.DataFrame({"Question": [question], "Answer": [answer]})
            new_data.to_csv(self.qa_file, mode='a', header=False, index=False, encoding='utf-8')
            log.info(f"Arya, saved '{question}' with '{answer}' to QA file")
        log.info(f"Arya, answered '{question}' with '{answer}'")
        return answer

    def load_page(self, sleep=1):
        # Arya: Loading and scrolling the page to get all content
        scroll_page = 0
        while scroll_page < 4000:
            self.browser.execute_script("window.scrollTo(0," + str(scroll_page) + " );")
            scroll_page += 500
            time.sleep(sleep)

        if sleep != 1:
            self.browser.execute_script("window.scrollTo(0,0);")
            time.sleep(sleep)

        page = BeautifulSoup(self.browser.page_source, "lxml")
        return page

    def avoid_lock(self) -> None:
        # Arya: Preventing browser lock with fake mouse movements
        x, _ = pyautogui.position()
        pyautogui.moveTo(x + 200, pyautogui.position().y, duration=1.0)
        pyautogui.moveTo(x, pyautogui.position().y, duration=0.5)
        pyautogui.keyDown('ctrl')
        pyautogui.press('esc')
        pyautogui.keyUp('ctrl')
        time.sleep(0.5)
        pyautogui.press('esc')

    def next_jobs_page(self, position, location, jobs_per_page, experience_level=[]):
        # Arya: Moving to the next page of jobs
        experience_level_str = ",".join(map(str, experience_level)) if experience_level else ""
        experience_level_param = f"&f_E={experience_level_str}" if experience_level_str else ""
        self.browser.get(
            "https://www.linkedin.com/jobs/search/?f_LF=f_AL&keywords=" +
            position + location + "&start=" + str(jobs_per_page) + experience_level_param)
        self.avoid_lock()
        log.info("Arya, loading next job page!")
        self.load_page()
        return (self.browser, jobs_per_page)

if __name__ == '__main__':
    # Arya: Loading your config file—let’s get started!
    with open("config.yaml", 'r') as stream:
        try:
            parameters = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            log.error(f"Arya, couldn’t load config.yaml: {str(exc)}")
            raise exc

    # Arya: Checking required fields
    required_fields = ['positions', 'locations', 'username', 'password', 'phone_number']
    for field in required_fields:
        if field not in parameters or not parameters[field]:
            raise ValueError(f"Arya, missing or empty required field: {field}")

    if 'uploads' in parameters.keys() and type(parameters['uploads']) == list:
        raise Exception("Arya, uploads should be a dict, not a list in config.yaml!")

    log.info({k: parameters[k] for k in parameters.keys() if k not in ['username', 'password']})

    # Arya: Setting defaults for optional fields
    output_filename: list = [f for f in parameters.get('output_filename', ['output.csv']) if f is not None]
    output_filename: list = output_filename[0] if len(output_filename) > 0 else 'output.csv'
    blacklist = parameters.get('blacklist', [])
    blackListTitles = parameters.get('blackListTitles', [])
    uploads = {} if parameters.get('uploads', {}) is None else parameters.get('uploads', {})
    for key in uploads.keys():
        if not uploads[key]:
            raise ValueError(f"Arya, empty path for {key} in uploads!")

    locations: list = [l for l in parameters['locations'] if l is not None]
    positions: list = [p for p in parameters['positions'] if p is not None]

    # Arya: Starting the bot with all parameters—profile_path is optional now!
    bot = EasyApplyBot(
        parameters['username'],
        parameters['password'],
        parameters['phone_number'],
        parameters.get('profile_path'),  # Optional, defaults to None
        parameters.get('salary'),        # Optional
        parameters.get('rate'),          # Optional
        uploads=uploads,
        filename=output_filename,
        blacklist=blacklist,
        blackListTitles=blackListTitles,
        experience_level=parameters.get('experience_level', [])
    )
    bot.start_apply(positions, locations)