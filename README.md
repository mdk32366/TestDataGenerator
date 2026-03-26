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

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the Streamlit app:
```bash
streamlit run fsc_data_generator_v2.py
```

The app will open in your browser at `http://localhost:8501`

### Generating Data Locally

1. Use the sidebar to configure generation parameters
2. Adjust record counts, date ranges, and regional filters
3. Click "Generate Data" to create test datasets
4. Download as CSV or ZIP file

### Upload to Salesforce

1. Enter your Salesforce credentials (Instance URL, Username, Password, Security Token)
2. Select sandbox or production environment
3. Click "Upload to Salesforce"
4. Monitor progress in the real-time log panel

## Salesforce Credentials

For security, use environment variables or `.env` file (see `.gitignore`):

```bash
export SALESFORCE_INSTANCE_URL="https://your-instance.salesforce.com"
export SALESFORCE_USERNAME="your.email@example.com"
export SALESFORCE_PASSWORD="your_password"
export SALESFORCE_SECURITY_TOKEN="your_security_token"
```

Never commit credentials to version control.

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
