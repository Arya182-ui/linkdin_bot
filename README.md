# Easy Apply Bot

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg) ![Python](https://img.shields.io/badge/python-3.x-blue.svg) ![License](https://img.shields.io/badge/license-MIT-green.svg)

## Overview

The **Easy Apply Bot** automates the job application process on LinkedIn, allowing users to apply for multiple jobs efficiently. By eliminating repetitive tasks, this bot helps job seekers save time and focus on securing the right opportunities.

## Features

- **Automated Job Searching**: Find jobs based on specified positions and locations.
- **One-Click Easy Apply**: Automatically apply to jobs with the "Easy Apply" button.
- **Customizable Application Settings**: Configure LinkedIn credentials, phone number, and upload necessary documents (resume and cover letter).
- **Intelligent Question Handling**: Automatically respond to common application questions.
- **Blacklist Support**: Exclude jobs based on blacklisted titles or keywords.
- **Detailed Logging**: Track application attempts and results with timestamped logs.

## Requirements

Ensure you have the following dependencies installed before running the bot:

- Python 3.x
- Selenium
- Pandas
- PyAutoGUI
- BeautifulSoup
- YAML
- Chrome WebDriver (managed by `webdriver-manager`)

## Installation

Follow these steps to set up and run the project:

### 1. Clone the Repository
```bash
git https://github.com/Arya182-ui/linkdin_bot.git
cd linkdin_bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Your Settings
Edit the `config.yaml` file to include your LinkedIn credentials, job preferences, and file paths.

#### Example `config.yaml`
```yaml
username: your_username
password: your_password
phone_number: your_phone_number

positions:
  - Software Engineer
  - Data Scientist

locations:
  - New York
  - San Francisco

uploads:
  Resume: path/to/your/resume.pdf
  Cover Letter: path/to/your/cover_letter.pdf

blacklist:
  - "Intern"
  - "Junior"

blackListTitles:
  - "Intern"
  - "Junior Developer"

experience_level: [1, 2, 3]  # Entry level, Associate, Mid-Senior level
```

## Usage

Run the bot using the following command:
```bash
python bot.py
```

## Logging

The bot generates logs for all application attempts and results in the `logs/` directory. Each log file is timestamped for easy tracking and debugging.

## Contribution Guidelines

Contributions are welcome! Follow these steps to contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them with clear messages.
4. Push your branch and open a pull request.

Please ensure that your code adheres to best practices and includes relevant test cases.

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.

## Acknowledgments

Special thanks to the open-source community and the developers of Selenium, Pandas, and BeautifulSoup for their invaluable contributions.

## Contact

For any inquiries or feedback, reach out via:

- **GitHub**: [GitHub Profile](https://github.com/Arya182-ui) 
- **Email**: arya119000@gmail.com
- **LinkedIn**: [Ayush Gangwar](https://www.linkedin.com/in/ayush-gangwar-3b3526237)

## ☕ Support Me

Do you like My projects? You can show your support by buying me a coffee! Your contributions motivate me to keep improving and building more awesome projects. 💻❤  
[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](http://buymeacoffee.com/Arya182)
