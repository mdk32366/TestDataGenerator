# FSC Insurance Test Data Generator

A Streamlit application for generating realistic test data for FSC Insurance Salesforce CRM. This tool creates comprehensive datasets including campaigns, leads, accounts, contacts, opportunities, and policies.

## Features

- **Multi-Object Data Generation**: Creates interconnected Salesforce objects
  - Campaigns with budgets and expected revenue
  - Leads with realistic contact information
  - Accounts with company details
  - Contacts assigned to accounts
  - Opportunities with various sales stages
  - Insurance policies with carriers and payment methods

- **US Geographic Coverage**: Generates addresses across all 50 states with realistic addresses and zip codes

- **Salesforce Integration**: 
  - Direct upload to Salesforce via API
  - Bulk insert operations with error handling
  - Support for both sandbox and production environments

- **Data Export**: 
  - CSV export of each object type
  - Batch download as ZIP file

- **Customization Options**:
  - Regional filtering (Northeast, Southeast, Midwest, Southwest, West, Pacific Northwest, Mountain West, Sunbelt)
  - Adjustable record counts per object
  - Configurable percentages for closed/won opportunities
  - Custom date ranges for historical data

## Requirements

- Python 3.8+
- Streamlit
- Pandas
- simple-salesforce
- requests

See `requirements.txt` for complete dependency list.

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/mdk32366/TestDataGenerator.git
   cd TestDataGenerator
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**

   ⚠️ **Important:** You MUST activate the virtual environment BEFORE installing dependencies.
   
   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```
   
   On Windows (PowerShell):
   ```powershell
   venv\Scripts\Activate.ps1
   
   # If you get an execution policy error, try:
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   venv\Scripts\Activate.ps1
   ```
   
   On Windows (Command Prompt):
   ```cmd
   venv\Scripts\activate.bat
   ```

   After activation, your shell prompt should show `(venv)` at the beginning.

4. **Install dependencies**
   
   With the virtual environment activated, install all required packages:
   ```bash
   pip install -r requirements.txt
   ```
   
   This will install:
   - `streamlit` - Web framework for the application
   - `pandas` - Data manipulation
   - `simple-salesforce` - Salesforce API client
   - `requests` - HTTP library
   - `python-dotenv` - Environment variable management

## Quick Start

### 1. Run the Application

**First, ensure your virtual environment is activated.** Your shell prompt should show `(venv)` at the beginning.

Once your virtual environment is activated and dependencies are installed, start the Streamlit app:

```bash
streamlit run fsc_data_generator_v2.py
```

The application will automatically open in your default browser at `http://localhost:8501`. If it doesn't open automatically, navigate to that URL manually.

### To Deactivate the Virtual Environment (when done)

Simply type:
```bash
deactivate
```

### 2. Configure Your Settings

In the **Sidebar**, you'll see configuration options for data generation:

- **Region**: Select geographic area (All 50 States, Northeast, Southeast, Midwest, Southwest, West, etc.)
- **Record Counts**: Set how many records to generate for:
  - Campaigns
  - Leads
  - Accounts
  - Contacts (per account)
  - Opportunities
  - Policies (for won opportunities)
- **Opportunity Settings**: 
  - Percentage of Closed Won opportunities
  - Months of historical data to include
  - Months of forward-dated opportunities
- **Industry & Business Types**: Select which industries and company types to include

### 3. Generate Data Locally

1. Adjust all parameters in the sidebar as desired
2. Click the **"Generate Data"** button
3. Monitor progress in the main panel—you'll see real-time statistics
4. Once complete, download options appear:
   - **Download as CSV**: Individual files for each object type
   - **Download as ZIP**: All files compressed into a single ZIP archive

### 4. Upload to Salesforce (Optional)

To push generated data directly to your Salesforce instance:

1. **Enter Salesforce Credentials** in the "Salesforce Connection" section:
   - Instance URL (e.g., `https://my-instance.salesforce.com`)
   - Username (your Salesforce email)
   - Password
   - Security Token (see below for how to obtain)
   - Select **Sandbox** or **Production** environment

2. **Click "Upload to Salesforce"** button

3. **Monitor the upload progress** in the real-time log panel
   - Green messages indicate successful inserts
   - Red messages indicate errors or failures
   - The log shows object counts and any validation issues

### Getting Your Salesforce Security Token

1. Log in to Salesforce
2. Click your profile icon in the top-right
3. Select **Settings**
4. In the left sidebar, go to **Personal Setup** > **My Personal Information** > **Reset Security Token**
5. Click **Reset Security Token**
6. Check your email for the new token
7. Copy and paste it into the app (or use the `.env` file—see below)

## Salesforce Credentials

You have two options for providing Salesforce credentials:

### Option 1: Use the Web Interface (Easiest)

Simply enter your credentials directly in the app's sidebar when it runs. This is the quickest way to get started for one-time use.

### Option 2: Use Environment Variables (.env file) — Recommended

For better security and automation, use a `.env` file (make sure your virtual environment is activated first):

1. **Activate your virtual environment** (if not already active)
   ```bash
   # macOS/Linux
   source venv/bin/activate
   
   # Windows PowerShell
   venv\Scripts\Activate.ps1
   
   # Windows Command Prompt
   venv\Scripts\activate.bat
   ```

2. **Create a `.env` file** in the project root:
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env`** with your actual Salesforce credentials:
   ```
   SALESFORCE_INSTANCE_URL=https://your-instance.salesforce.com
   SALESFORCE_USERNAME=your.email@example.com
   SALESFORCE_PASSWORD=your_password
   SALESFORCE_SECURITY_TOKEN=your_security_token
   SALESFORCE_ENVIRONMENT=sandbox
   ```

4. **Run the app** (within the activated virtual environment):
   ```bash
   streamlit run fsc_data_generator_v2.py
   ```
   
   The app will automatically load credentials from the `.env` file via `python-dotenv`.

**⚠️ Important Security Notes:**
- **Never commit `.env` to version control** — it's excluded by `.gitignore`
- **Never hardcode credentials in the code**
- Use `.env` file only for development and testing
- Always activate the virtual environment before running the app so `python-dotenv` can load the environment variables
- For production deployments, use your CI/CD platform's secure secret management (GitHub Secrets, GitLab CI/CD variables, etc.)

## Data Objects

### Campaign
- Name, Type, Status
- Start/End dates
- Budget and expected revenue
- Number sent

### Lead
- Name, Email, Phone
- Company, Title, Industry
- Address (Street, City, State, ZIP)
- Status, Lead Source
- Annual Revenue, Employee Count

### Account
- Company Name
- Account Type and Source
- Industry, Revenue, Employees
- Billing Address
- Website

### Contact
- Name, Title, Email, Phone
- Department, Lead Source
- Assigned to Account
- Mailing Address

### Opportunity
- Opportunity Name
- Account association
- Stage (Prospecting through Closed Won)
- Close Date, Amount, Probability
- Type, Forecast Category

### Policy
- Policy Number and Type
- Carrier
- Effective/Expiration Dates
- Premium Amount
- Payment Method and Frequency
- Status (In Force)

## Project Structure

```
TestDataGenerator/
├── fsc_data_generator_v2.py    # Main Streamlit application
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules (secrets, cache)
├── README.md                    # This file
└── .env.example                 # Environment variables template
```

## Security

- Never commit Salesforce credentials to version control
- Use environment variables or `.env` file for sensitive data
- See `.gitignore` for excluded files

## Troubleshooting

### Connection Issues
- Verify Salesforce Instance URL format (e.g., `https://my-instance.salesforce.com`)
- Confirm username and password are correct
- Ensure Security Token is appended to password if using IP-restricted org
- Check sandbox vs. production environment selection

### Data Upload Failures
- Review error log in the app for specific field validation errors
- Verify object field mappings are correct
- Check API usage limits in Salesforce

### Performance
- Large datasets (10,000+ records) may take time to process
- Bulk API batches are limited to 200 records per request
- Consider generating data in stages

## License

Internal FSC Insurance project. All rights reserved.

## Support

For issues or feature requests, contact the development team.
