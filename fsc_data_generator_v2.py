import streamlit as st
import pandas as pd
import random
import uuid
import io
import zipfile
import time
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FSC Insurance Test Data Generator",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# STYLING
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a3a5c 0%, #2563a8 100%);
        padding: 2rem 2.5rem; border-radius: 12px;
        color: white; margin-bottom: 2rem;
    }
    .main-header h1 { margin: 0; font-size: 2rem; font-weight: 700; }
    .main-header p  { margin: 0.4rem 0 0; opacity: 0.85; font-size: 1rem; }

    .metric-row { display: flex; gap: 0.8rem; flex-wrap: wrap; margin-bottom: 1.2rem; }
    .metric-box {
        background: white; border: 1px solid #dce7f5;
        border-radius: 8px; padding: 0.9rem 1.2rem;
        min-width: 110px; text-align: center; flex: 1;
    }
    .metric-box .val { font-size: 1.7rem; font-weight: 700; color: #2563a8; }
    .metric-box .lbl { font-size: 0.72rem; color: #666; margin-top: 2px;
                       text-transform: uppercase; letter-spacing: 0.05em; }

    .sf-connected {
        background: #eafaf1; border: 1px solid #82d9a8;
        border-radius: 8px; padding: 0.8rem 1rem;
        color: #1a5c36; font-size: 0.88rem; margin-bottom: 0.8rem;
    }
    .sf-disconnected {
        background: #fdf2f2; border: 1px solid #f5a8a8;
        border-radius: 8px; padding: 0.8rem 1rem;
        color: #7a1a1a; font-size: 0.88rem; margin-bottom: 0.8rem;
    }
    .success-box {
        background: #eafaf1; border: 1px solid #82d9a8;
        border-radius: 8px; padding: 0.8rem 1rem;
        color: #1a5c36; font-size: 0.88rem; margin-bottom: 1rem;
    }
    .warn-box {
        background: #fff8e6; border: 1px solid #f5c842;
        border-radius: 8px; padding: 0.8rem 1rem;
        color: #7a5200; font-size: 0.88rem; margin-bottom: 1rem;
    }
    .error-box {
        background: #fdf2f2; border: 1px solid #f5a8a8;
        border-radius: 8px; padding: 0.8rem 1rem;
        color: #7a1a1a; font-size: 0.88rem; margin-bottom: 1rem;
    }
    .load-log {
        background: #0d1117; color: #c9d1d9;
        border-radius: 8px; padding: 1rem 1.2rem;
        font-family: 'Courier New', monospace; font-size: 0.78rem;
        max-height: 360px; overflow-y: auto; line-height: 1.6;
    }
    .log-success { color: #3fb950; }
    .log-error   { color: #f85149; }
    .log-info    { color: #58a6ff; }
    .log-warn    { color: #d29922; }

    .progress-step {
        display: flex; align-items: center; gap: 0.6rem;
        padding: 0.45rem 0.8rem; border-radius: 6px;
        font-size: 0.85rem; margin-bottom: 0.3rem;
    }
    .step-pending  { background: #f0f4f8; color: #666; }
    .step-running  { background: #e8f0fe; color: #1a3a5c; font-weight: 600; }
    .step-done     { background: #eafaf1; color: #1a5c36; }
    .step-error    { background: #fdf2f2; color: #7a1a1a; }
    .step-skipped  { background: #f5f5f5; color: #aaa; }

    div[data-testid="stExpander"] {
        border: 1px solid #dce7f5 !important; border-radius: 8px !important;
    }
    div[data-testid="stTabs"] button { font-weight: 600; }
    .stButton > button { border-radius: 8px; }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1a3a5c, #2563a8);
        border: none; font-weight: 700; letter-spacing: 0.03em;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# REFERENCE DATA
# ─────────────────────────────────────────────────────────────────────────────
US_CITIES = {
    "AL": (["Birmingham","Montgomery","Huntsville","Mobile","Tuscaloosa","Hoover","Dothan","Auburn","Decatur","Madison"], "35"),
    "AK": (["Anchorage","Fairbanks","Juneau","Sitka","Ketchikan","Wasilla","Kenai","Kodiak","Palmer","Homer"], "99"),
    "AZ": (["Phoenix","Tucson","Mesa","Chandler","Scottsdale","Glendale","Gilbert","Tempe","Peoria","Surprise"], "85"),
    "AR": (["Little Rock","Fort Smith","Fayetteville","Springdale","Jonesboro","North Little Rock","Conway","Rogers","Bentonville","Pine Bluff"], "72"),
    "CA": (["Los Angeles","San Francisco","San Diego","Sacramento","San Jose","Fresno","Long Beach","Oakland","Bakersfield","Anaheim"], "9"),
    "CO": (["Denver","Colorado Springs","Aurora","Fort Collins","Lakewood","Thornton","Arvada","Westminster","Pueblo","Centennial"], "80"),
    "CT": (["Bridgeport","New Haven","Hartford","Stamford","Waterbury","Norwalk","Danbury","New Britain","Greenwich","Meriden"], "06"),
    "DE": (["Wilmington","Dover","Newark","Middletown","Smyrna","Milford","Seaford","Georgetown","Elsmere","New Castle"], "19"),
    "FL": (["Jacksonville","Miami","Tampa","Orlando","St. Petersburg","Hialeah","Tallahassee","Fort Lauderdale","Port St. Lucie","Cape Coral"], "3"),
    "GA": (["Atlanta","Augusta","Columbus","Macon","Savannah","Athens","Sandy Springs","Roswell","Johns Creek","Albany"], "30"),
    "HI": (["Honolulu","Pearl City","Hilo","Kailua","Waipahu","Kaneohe","Mililani","Kahului","Ewa Beach","Kihei"], "96"),
    "ID": (["Boise","Nampa","Meridian","Idaho Falls","Pocatello","Caldwell","Coeur d'Alene","Twin Falls","Lewiston","Post Falls"], "83"),
    "IL": (["Chicago","Aurora","Rockford","Joliet","Naperville","Springfield","Peoria","Elgin","Waukegan","Champaign"], "6"),
    "IN": (["Indianapolis","Fort Wayne","Evansville","South Bend","Carmel","Fishers","Bloomington","Hammond","Gary","Lafayette"], "46"),
    "IA": (["Des Moines","Cedar Rapids","Davenport","Sioux City","Iowa City","Waterloo","Ames","West Des Moines","Council Bluffs","Dubuque"], "50"),
    "KS": (["Wichita","Overland Park","Kansas City","Topeka","Olathe","Lawrence","Shawnee","Manhattan","Lenexa","Salina"], "67"),
    "KY": (["Louisville","Lexington","Bowling Green","Owensboro","Covington","Richmond","Georgetown","Florence","Hopkinsville","Nicholasville"], "40"),
    "LA": (["New Orleans","Baton Rouge","Shreveport","Metairie","Lafayette","Lake Charles","Kenner","Bossier City","Monroe","Alexandria"], "70"),
    "ME": (["Portland","Lewiston","Bangor","South Portland","Auburn","Biddeford","Sanford","Saco","Augusta","Westbrook"], "04"),
    "MD": (["Baltimore","Columbia","Germantown","Silver Spring","Waldorf","Glen Burnie","Ellicott City","Frederick","Dundalk","Rockville"], "21"),
    "MA": (["Boston","Worcester","Springfield","Lowell","Cambridge","New Bedford","Brockton","Quincy","Lynn","Fall River"], "02"),
    "MI": (["Detroit","Grand Rapids","Warren","Sterling Heights","Ann Arbor","Lansing","Flint","Dearborn","Livonia","Westland"], "48"),
    "MN": (["Minneapolis","St. Paul","Rochester","Duluth","Bloomington","Brooklyn Park","Plymouth","St. Cloud","Eagan","Woodbury"], "55"),
    "MS": (["Jackson","Gulfport","Southaven","Hattiesburg","Biloxi","Meridian","Tupelo","Olive Branch","Greenville","Horn Lake"], "39"),
    "MO": (["Kansas City","St. Louis","Springfield","Columbia","Independence","Lee's Summit","O'Fallon","St. Joseph","St. Charles","St. Peters"], "63"),
    "MT": (["Billings","Missoula","Great Falls","Bozeman","Butte","Helena","Kalispell","Havre","Anaconda","Miles City"], "59"),
    "NE": (["Omaha","Lincoln","Bellevue","Grand Island","Kearney","Fremont","Hastings","Norfolk","North Platte","Columbus"], "68"),
    "NV": (["Las Vegas","Henderson","Reno","North Las Vegas","Sparks","Carson City","Fernley","Elko","Mesquite","Boulder City"], "89"),
    "NH": (["Manchester","Nashua","Concord","Dover","Rochester","Keene","Portsmouth","Laconia","Lebanon","Claremont"], "03"),
    "NJ": (["Newark","Jersey City","Paterson","Elizabeth","Edison","Woodbridge","Lakewood","Toms River","Hamilton","Trenton"], "07"),
    "NM": (["Albuquerque","Las Cruces","Rio Rancho","Santa Fe","Roswell","Farmington","Clovis","Hobbs","Alamogordo","Carlsbad"], "87"),
    "NY": (["New York City","Buffalo","Rochester","Yonkers","Syracuse","Albany","New Rochelle","Mount Vernon","Schenectady","Utica"], "1"),
    "NC": (["Charlotte","Raleigh","Greensboro","Durham","Winston-Salem","Fayetteville","Cary","Wilmington","High Point","Concord"], "27"),
    "ND": (["Fargo","Bismarck","Grand Forks","Minot","West Fargo","Williston","Dickinson","Mandan","Jamestown","Wahpeton"], "58"),
    "OH": (["Columbus","Cleveland","Cincinnati","Toledo","Akron","Dayton","Parma","Canton","Youngstown","Lorain"], "44"),
    "OK": (["Oklahoma City","Tulsa","Norman","Broken Arrow","Lawton","Edmond","Moore","Midwest City","Enid","Stillwater"], "73"),
    "OR": (["Portland","Salem","Eugene","Gresham","Hillsboro","Beaverton","Bend","Medford","Springfield","Corvallis"], "97"),
    "PA": (["Philadelphia","Pittsburgh","Allentown","Erie","Reading","Scranton","Bethlehem","Lancaster","Harrisburg","Altoona"], "19"),
    "RI": (["Providence","Cranston","Warwick","Pawtucket","East Providence","Woonsocket","Coventry","Cumberland","North Providence","West Warwick"], "02"),
    "SC": (["Columbia","Charleston","North Charleston","Mount Pleasant","Rock Hill","Greenville","Summerville","Goose Creek","Hilton Head","Sumter"], "29"),
    "SD": (["Sioux Falls","Rapid City","Aberdeen","Brookings","Watertown","Mitchell","Yankton","Pierre","Huron","Vermillion"], "57"),
    "TN": (["Nashville","Memphis","Knoxville","Chattanooga","Clarksville","Murfreesboro","Franklin","Jackson","Johnson City","Bartlett"], "37"),
    "TX": (["Houston","San Antonio","Dallas","Austin","Fort Worth","El Paso","Arlington","Corpus Christi","Plano","Laredo"], "7"),
    "UT": (["Salt Lake City","West Valley City","Provo","West Jordan","Orem","Sandy","Ogden","St. George","Layton","South Jordan"], "84"),
    "VT": (["Burlington","South Burlington","Rutland","Barre","Montpelier","Winooski","St. Albans","Newport","Vergennes","Middlebury"], "05"),
    "VA": (["Virginia Beach","Norfolk","Chesapeake","Richmond","Newport News","Alexandria","Hampton","Roanoke","Portsmouth","Suffolk"], "23"),
    "WA": (["Seattle","Spokane","Tacoma","Vancouver","Bellevue","Kent","Everett","Renton","Spokane Valley","Federal Way"], "98"),
    "WV": (["Charleston","Huntington","Morgantown","Parkersburg","Wheeling","Weirton","Fairmont","Martinsburg","Beckley","Clarksburg"], "25"),
    "WI": (["Milwaukee","Madison","Green Bay","Kenosha","Racine","Appleton","Waukesha","Eau Claire","Oshkosh","Janesville"], "53"),
    "WY": (["Cheyenne","Casper","Laramie","Gillette","Rock Springs","Sheridan","Green River","Evanston","Riverton","Jackson"], "82"),
    "DC": (["Washington"], "20"),
}
STREET_NAMES = ["Oak","Maple","Cedar","Pine","Elm","Washington","Lincoln","Park","Lake","Hill",
    "Ridge","Valley","River","Forest","Meadow","Summit","Sunset","Sunrise","Highland",
    "Lakewood","Greenfield","Fairview","Brookside","Willow","Birch","Spruce","Chestnut",
    "Heritage","Pioneer","Commerce","Market","Main","Broadway","Central","Liberty",
    "Independence","Jefferson","Madison","Monroe","Adams","Franklin","Hamilton","Jackson",
    "Peachtree","Magnolia","Palmetto","Bluegrass","Lone Star","Prairie","Canyon","Mesa",
    "Harbor","Bay","Coastal","Shoreline","Creekside","Riverside","Mountainview","Cliffside"]
STREET_TYPES   = ["Ave","St","Blvd","Dr","Way","Ln","Ct","Rd","Pkwy","Pl","Cir","Terr"]
COMPANY_PREFIXES = ["Pacific","Atlantic","National","American","United","Premier","Apex","Summit","Heritage",
    "Pioneer","Frontier","Midwest","Southern","Northern","Western","Eastern","Central",
    "Coastal","Inland","Continental","Tri-State","Metro","Regional","Community","Allied",
    "Integrated","Advanced","Strategic","Dynamic","Global","Federal","Liberty","Patriot",
    "Capital","Crown","Pinnacle","Keystone","Cornerstone","Landmark","Bedrock","Foundation",
    "Horizon","Beacon","Shield","Guardian","Sentinel","Vanguard","Nexus","Axiom","Crest",
    "Blue Ridge","Silver Lake","Golden Gate","Lone Star","Great Plains","Heartland"]
COMPANY_TYPES  = ["Insurance Group","Financial Services","Risk Management","Wealth Advisors",
    "Capital Partners","Holdings LLC","Enterprises Inc","Solutions Group",
    "Associates LLC","Consulting Group","Insurance Agency","Risk Advisors",
    "Benefits Group","Financial Partners","Asset Management","Investment Group"]
FIRST_NAMES = ["James","Mary","John","Patricia","Robert","Jennifer","Michael","Linda","William","Barbara",
    "David","Susan","Richard","Jessica","Joseph","Sarah","Thomas","Karen","Charles","Lisa",
    "Christopher","Nancy","Daniel","Betty","Matthew","Margaret","Anthony","Sandra","Mark","Ashley",
    "Donald","Dorothy","Steven","Kimberly","Paul","Emily","Andrew","Donna","Joshua","Michelle",
    "Kenneth","Carol","Kevin","Amanda","Brian","Melissa","George","Deborah","Timothy","Stephanie",
    "Ronald","Rebecca","Edward","Sharon","Jason","Laura","Jeffrey","Cynthia","Ryan","Kathleen",
    "Jacob","Amy","Gary","Angela","Nicholas","Shirley","Eric","Anna","Jonathan","Brenda",
    "Stephen","Pamela","Larry","Emma","Justin","Virginia","Scott","Helen","Brandon","Katharine",
    "Benjamin","Samantha","Samuel","Christine","Raymond","Janet","Gregory","Catherine","Frank","Frances",
    "Alexander","Ann","Patrick","Joyce","Jack","Diane","Dennis","Alice","Walter","Jean",
    "Harold","Cheryl","Joe","Megan","Henry","Andrea","Douglas","Marie","Peter","Gloria"]
LAST_NAMES = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
    "Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin",
    "Lee","Perez","Thompson","White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson",
    "Walker","Young","Allen","King","Wright","Scott","Torres","Nguyen","Hill","Flores",
    "Green","Adams","Nelson","Baker","Hall","Rivera","Campbell","Mitchell","Carter","Roberts",
    "Turner","Phillips","Evans","Collins","Stewart","Morris","Rogers","Reed","Cook","Morgan",
    "Bell","Murphy","Bailey","Cooper","Richardson","Cox","Howard","Ward","Brooks","Kelly",
    "Sanders","Price","Bennett","Wood","Barnes","Ross","Henderson","Coleman","Jenkins","Perry",
    "Powell","Long","Patterson","Hughes","Washington","Butler","Simmons","Foster","Gonzales","Bryant",
    "Alexander","Russell","Griffin","Diaz","Hayes","Myers","Ford","Hamilton","Graham","Sullivan"]
POLICY_TYPES   = ["Homeowners","Auto","Life","Commercial Property","General Liability",
    "Workers Compensation","Umbrella","Health","Disability","Renters",
    "Business Owners Policy","Professional Liability","Cyber Liability","Flood","Earthquake"]
CARRIERS       = ["State Farm","Allstate","Progressive","Nationwide","Travelers","Liberty Mutual",
    "Farmers","USAA","American Family","Erie Insurance","Hartford","Chubb",
    "AIG","Zurich","CNA Financial","Markel","Cincinnati Financial","Hanover"]
INDUSTRIES     = ["Insurance","Financial Services","Healthcare","Real Estate","Manufacturing",
    "Technology","Retail","Education","Government","Nonprofit","Construction",
    "Transportation","Legal","Hospitality","Agriculture","Energy","Media"]
OPP_STAGES_OPEN= ["Prospecting","Qualification","Needs Analysis","Value Proposition","Proposal/Price Quote","Negotiation/Review"]
PAYMENT_METHODS= ["ACH","Check","Credit Card","EFT","Wire Transfer"]
PAYMENT_FREQS  = ["Monthly","Quarterly","Semi-Annual","Annual"]
LEAD_STATUSES  = ["Open - Not Contacted","Working","Nurturing","Contacted"]
LEAD_SOURCES   = ["Campaign","Web","Phone Inquiry","Partner Referral","Word of Mouth","Trade Show","Email"]
CONTACT_TITLES = ["CEO","CFO","COO","VP Finance","Risk Manager","Controller","Owner","Director of Operations","President","Managing Partner"]
ACCOUNT_SOURCES= ["Web","Phone Inquiry","Campaign","Partner Referral","Word of Mouth","Trade Show"]
ACCOUNT_TYPES  = ["Prospect","Customer - Direct","Customer - Channel","Partner"]
OPP_TYPES      = ["New Business","Renewal","Cross-Sell","Upsell"]
FORECAST_CATS  = {"Closed Won":"Closed","Prospecting":"Pipeline","Qualification":"Pipeline",
    "Needs Analysis":"Pipeline","Value Proposition":"Pipeline",
    "Proposal/Price Quote":"Best Case","Negotiation/Review":"Commit"}

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS — DATA
# ─────────────────────────────────────────────────────────────────────────────
def fake_sf_id(prefix):
    return prefix + uuid.uuid4().hex[:12].upper()

def random_phone():
    return f"({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}"

def random_address(state=None):
    if state is None or state not in US_CITIES:
        state = random.choice(list(US_CITIES.keys()))
    cities, zip_prefix = US_CITIES[state]
    city    = random.choice(cities)
    street  = f"{random.randint(100,9999)} {random.choice(STREET_NAMES)} {random.choice(STREET_TYPES)}"
    remaining = 5 - len(zip_prefix)
    suffix    = str(random.randint(0, 10**remaining - 1)).zfill(remaining)
    zipcode   = (zip_prefix + suffix)[:5]
    return street, city, state, zipcode

def random_company():
    return f"{random.choice(COMPANY_PREFIXES)} {random.choice(COMPANY_TYPES)}"

def random_name():
    return random.choice(FIRST_NAMES), random.choice(LAST_NAMES)

def random_email(first, last, domain=None):
    if domain is None:
        domain = f"{random.choice(COMPANY_PREFIXES).lower().replace(' ','')}ins.com"
    return f"{first.lower()}.{last.lower()}{random.randint(1,99)}@{domain}"

def random_revenue():
    return random.choice([250000,500000,750000,1000000,2500000,5000000,10000000,25000000,50000000])

def random_employees():
    return random.choice([5,10,15,25,50,75,100,200,250,500,750,1000,2500])

def states_for_region(region):
    regions = {
        "All 50 States":    list(US_CITIES.keys()),
        "Northeast":        ["ME","NH","VT","MA","RI","CT","NY","NJ","PA","DE","MD","DC"],
        "Southeast":        ["VA","WV","NC","SC","GA","FL","AL","MS","TN","KY","AR","LA"],
        "Midwest":          ["OH","IN","IL","MI","WI","MN","IA","MO","ND","SD","NE","KS"],
        "Southwest":        ["TX","OK","NM","AZ","NV"],
        "West":             ["CA","OR","WA","ID","MT","WY","CO","UT","AK","HI"],
        "Pacific Northwest":["WA","OR","ID","MT"],
        "Mountain West":    ["CO","UT","NV","AZ","NM","WY","ID","MT"],
        "Sunbelt":          ["FL","GA","TX","AZ","CA","NV","NM"],
        "Custom":           [],
    }
    return regions.get(region, list(US_CITIES.keys()))

# ─────────────────────────────────────────────────────────────────────────────
# GENERATORS
# ─────────────────────────────────────────────────────────────────────────────
def generate_campaigns(count, names, campaign_type, status, budget_range, revenue_range):
    rows = []
    for i in range(count):
        start = datetime(2026, (i % 4) * 3 + 1, 1)
        end   = start + timedelta(days=90)
        name  = names[i] if i < len(names) else f"Campaign {i+1} – Insurance Outreach"
        rows.append({"Id": fake_sf_id("701"), "Name": name, "Type": campaign_type,
            "Status": status, "StartDate": start.strftime("%Y-%m-%d"),
            "EndDate": end.strftime("%Y-%m-%d"), "IsActive": True,
            "Description": f"Insurance lead generation campaign – {name}.",
            "BudgetedCost": random.randint(*budget_range)*1000,
            "ExpectedRevenue": random.randint(*revenue_range)*1000,
            "NumberSentInCampaign": random.randint(200,2000)})
    return pd.DataFrame(rows)

def generate_leads(count, campaign_df, state_pool, lead_statuses, lead_sources, industries):
    rows = []
    cids = campaign_df["Id"].tolist()
    for i in range(count):
        fn, ln = random_name()
        state  = random.choice(state_pool)
        st, city, state, zipcode = random_address(state)
        rows.append({"Id": fake_sf_id("00Q"), "FirstName": fn, "LastName": ln,
            "Email": random_email(fn,ln), "Phone": random_phone(),
            "Company": random_company(), "Title": random.choice(CONTACT_TITLES),
            "Street": st, "City": city, "State": state, "PostalCode": zipcode, "Country": "US",
            "Status": random.choice(lead_statuses), "LeadSource": random.choice(lead_sources),
            "Industry": random.choice(industries),
            "AnnualRevenue": random_revenue(), "NumberOfEmployees": random_employees(),
            "Description": "Inbound lead from campaign interest in insurance products.",
            "_campaign_id": cids[i % len(cids)] if cids else ""})
    return pd.DataFrame(rows)

def generate_accounts(count, state_pool, industries, account_types, account_sources):
    rows = []
    for i in range(count):
        state   = random.choice(state_pool)
        st, city, state, zipcode = random_address(state)
        company = random_company()
        domain  = company.lower().replace(" ","").replace(",","")[:15] + ".com"
        rows.append({"Id": fake_sf_id("001"), "Name": company,
            "Type": random.choice(account_types), "Industry": random.choice(industries),
            "AnnualRevenue": random_revenue(), "NumberOfEmployees": random_employees(),
            "Phone": random_phone(), "BillingStreet": st, "BillingCity": city,
            "BillingState": state, "BillingPostalCode": zipcode, "BillingCountry": "US",
            "Website": f"www.{domain}", "Description": "Commercial insurance prospect account.",
            "AccountSource": random.choice(account_sources), "_domain": domain})
    return pd.DataFrame(rows)

def generate_contacts(account_df, contacts_per_account, contact_titles):
    rows = []
    for _, acc in account_df.iterrows():
        for _ in range(contacts_per_account):
            fn, ln = random_name()
            rows.append({"Id": fake_sf_id("003"), "_account_id": acc["Id"],
                "FirstName": fn, "LastName": ln, "Title": random.choice(contact_titles),
                "Email": random_email(fn,ln,acc.get("_domain")),
                "Phone": random_phone(), "MobilePhone": random_phone(),
                "MailingStreet": acc["BillingStreet"], "MailingCity": acc["BillingCity"],
                "MailingState": acc["BillingState"], "MailingPostalCode": acc["BillingPostalCode"],
                "MailingCountry": "US", "LeadSource": random.choice(LEAD_SOURCES),
                "Department": random.choice(["Finance","Operations","Executive","Risk Management","Administration"]),
                "Description": "Primary contact for insurance account."})
    return pd.DataFrame(rows)

def generate_opportunities(account_df, closed_won_pct, opp_types, amount_range, months_back, months_fwd):
    rows = []
    closed_count = int(len(account_df) * closed_won_pct / 100)
    for i, (_, acc) in enumerate(account_df.iterrows()):
        is_won  = i < closed_count
        stage   = "Closed Won" if is_won else random.choice(OPP_STAGES_OPEN)
        amount  = random.randint(*amount_range) * 1000
        if is_won:
            close_dt = datetime.now() - timedelta(days=random.randint(30, months_back*30))
        else:
            close_dt = datetime.now() + timedelta(days=random.randint(30, months_fwd*30))
        rows.append({"Id": fake_sf_id("006"),
            "Name": f"{acc['Name']} – Insurance {datetime.now().year}",
            "_account_id": acc["Id"], "StageName": stage,
            "CloseDate": close_dt.strftime("%Y-%m-%d"), "Amount": amount,
            "Probability": 100 if is_won else random.choice([10,20,30,40,50,60,70,80]),
            "Type": random.choice(opp_types), "LeadSource": random.choice(LEAD_SOURCES),
            "Description": f"Commercial insurance opportunity for {acc['Name']}.",
            "NextStep": "" if is_won else random.choice(["Schedule call","Send proposal","Follow up","Negotiate terms"]),
            "ForecastCategoryName": FORECAST_CATS.get(stage,"Pipeline"),
            "_is_won": is_won})
    return pd.DataFrame(rows)

def generate_policies(opp_df, account_df, policy_types, carriers, payment_methods, payment_freqs, premium_pct_range):
    won_opps = opp_df[opp_df["_is_won"] == True].copy()
    acc_map  = {r["Id"]: r for _, r in account_df.iterrows()}
    rows = []
    for idx, (_, opp) in enumerate(won_opps.iterrows()):
        acc      = acc_map.get(opp["_account_id"], {})
        close_dt = datetime.strptime(opp["CloseDate"], "%Y-%m-%d")
        eff_dt   = close_dt + timedelta(days=random.randint(1,30))
        exp_dt   = eff_dt   + timedelta(days=365)
        ptype    = random.choice(policy_types)
        carrier  = random.choice(carriers)
        pct      = random.uniform(*[p/100 for p in premium_pct_range])
        rows.append({"Id": fake_sf_id("a0C"),
            "Name": f"POL-{str(idx+1).zfill(5)}",
            "_account_id": opp["_account_id"], "_opp_id": opp["Id"],
            "PolicyType": ptype, "Status": "In Force",
            "EffectiveDate": eff_dt.strftime("%Y-%m-%d"),
            "ExpirationDate": exp_dt.strftime("%Y-%m-%d"),
            "PremiumAmount": round(opp["Amount"] * pct, 2),
            "PolicyNumber": f"POL{random.randint(1000000,9999999)}",
            "Description": f"{ptype} policy for {acc.get('Name','Account')} through {carrier}.",
            "IssuedDate": opp["CloseDate"], "Carrier__c": carrier,
            "PaymentMethod__c": random.choice(payment_methods),
            "PaymentFrequency__c": random.choice(payment_freqs)})
    return pd.DataFrame(rows)

# ─────────────────────────────────────────────────────────────────────────────
# CSV HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def df_to_csv_bytes(df):
    export = df[[c for c in df.columns if not c.startswith("_")]]
    buf = io.StringIO()
    export.to_csv(buf, index=False)
    return buf.getvalue().encode()

def build_zip(dataframes: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, df in dataframes.items():
            zf.writestr(filename, df_to_csv_bytes(df))
    return buf.getvalue()

def metric_html(value, label):
    return f'<div class="metric-box"><div class="val">{value:,}</div><div class="lbl">{label}</div></div>'

# ─────────────────────────────────────────────────────────────────────────────
# SALESFORCE API — CONNECTION
# ─────────────────────────────────────────────────────────────────────────────
def sf_connect(instance_url, username, password, security_token, is_sandbox):
    from simple_salesforce import Salesforce
    domain = "test" if is_sandbox else "login"
    sf = Salesforce(
        username=username,
        password=password,
        security_token=security_token,
        domain=domain,
    )
    return sf

def sf_query(sf, soql):
    result = sf.query_all(soql)
    return result.get("records", [])

# ─────────────────────────────────────────────────────────────────────────────
# SALESFORCE API — BULK LOADER
# ─────────────────────────────────────────────────────────────────────────────
LOAD_CHUNK = 200  # records per batch API call (SF limit: 200)

@dataclass
class LoadResult:
    object_name: str
    total: int = 0
    inserted: int = 0
    failed: int = 0
    errors: list = field(default_factory=list)
    sf_ids: dict = field(default_factory=dict)   # local_id -> sf_id

def _batch_insert(sf, object_name: str, records: list[dict]) -> tuple[list, list]:
    """Submit up to 200 records via SObject Collections API. Returns (successes, failures)."""
    import requests, json
    endpoint = f"{sf.base_url}composite/sobjects"
    headers  = {"Authorization": f"Bearer {sf.session_id}",
                 "Content-Type": "application/json"}
    payload  = {"allOrNone": False, "records": [{"attributes":{"type":object_name}, **r} for r in records]}
    resp     = requests.post(endpoint, headers=headers, json=payload)
    results  = resp.json()
    successes, failures = [], []
    for i, res in enumerate(results):
        if res.get("success"):
            successes.append({"idx": i, "id": res["id"]})
        else:
            errs = "; ".join(e.get("message","?") for e in res.get("errors",[]))
            failures.append({"idx": i, "errors": errs})
    return successes, failures


def load_campaigns(sf, df, log_fn) -> LoadResult:
    result = LoadResult("Campaign", total=len(df))
    fields = ["Name","Type","Status","StartDate","EndDate","IsActive",
              "Description","BudgetedCost","ExpectedRevenue","NumberSentInCampaign"]
    local_ids = df["Id"].tolist()
    records   = [{f: row.get(f) for f in fields} for _, row in df.iterrows()]
    for i in range(0, len(records), LOAD_CHUNK):
        chunk    = records[i:i+LOAD_CHUNK]
        lid_chunk = local_ids[i:i+LOAD_CHUNK]
        ok, fail = _batch_insert(sf, "Campaign", chunk)
        for o in ok:
            result.inserted += 1
            result.sf_ids[lid_chunk[o["idx"]]] = o["id"]
        for f in fail:
            result.failed += 1
            result.errors.append(f"Campaign row {i+f['idx']}: {f['errors']}")
        log_fn(f"  Campaigns: {result.inserted}/{result.total} inserted", ok=result.failed==0)
    return result


def load_leads(sf, df, campaign_sf_ids: dict, log_fn) -> LoadResult:
    result  = LoadResult("Lead", total=len(df))
    fields  = ["FirstName","LastName","Email","Phone","Company","Title",
               "Street","City","State","PostalCode","Country",
               "Status","LeadSource","Industry","AnnualRevenue","NumberOfEmployees","Description"]
    records = []
    for _, row in df.iterrows():
        rec = {f: row.get(f) for f in fields}
        # CampaignId added as lookup if campaign was loaded
        camp_sf = campaign_sf_ids.get(row.get("_campaign_id",""), "")
        if camp_sf:
            rec["Campaign"] = None   # Campaign member created separately below
        records.append((rec, row.get("_campaign_id",""), camp_sf))

    local_ids = df["Id"].tolist()
    lead_sf_ids = {}
    for i in range(0, len(records), LOAD_CHUNK):
        chunk      = [r for r,_,_ in records[i:i+LOAD_CHUNK]]
        lid_chunk  = local_ids[i:i+LOAD_CHUNK]
        ok, fail   = _batch_insert(sf, "Lead", chunk)
        for o in ok:
            result.inserted += 1
            lead_sf_ids[lid_chunk[o["idx"]]] = o["id"]
            result.sf_ids[lid_chunk[o["idx"]]] = o["id"]
        for f in fail:
            result.failed += 1
            result.errors.append(f"Lead row {i+f['idx']}: {f['errors']}")
        log_fn(f"  Leads: {result.inserted}/{result.total} inserted", ok=result.failed==0)

    # Create CampaignMembers for each Lead
    members = []
    for local_id, (rec, local_camp_id, sf_camp_id) in zip(local_ids, records):
        sf_lead = lead_sf_ids.get(local_id)
        if sf_lead and sf_camp_id:
            members.append({"LeadId": sf_lead, "CampaignId": sf_camp_id, "Status": "Sent"})
    if members:
        log_fn(f"  Creating {len(members)} Campaign Members…", ok=True)
        for i in range(0, len(members), LOAD_CHUNK):
            ok, fail = _batch_insert(sf, "CampaignMember", members[i:i+LOAD_CHUNK])
            for f in fail:
                result.errors.append(f"CampaignMember: {f['errors']}")
        log_fn(f"  Campaign Members created", ok=True)
    return result


def load_accounts(sf, df, log_fn) -> LoadResult:
    result = LoadResult("Account", total=len(df))
    fields = ["Name","Type","Industry","AnnualRevenue","NumberOfEmployees","Phone",
              "BillingStreet","BillingCity","BillingState","BillingPostalCode","BillingCountry",
              "Website","Description","AccountSource"]
    local_ids = df["Id"].tolist()
    records   = [{f: row.get(f) for f in fields} for _, row in df.iterrows()]
    for i in range(0, len(records), LOAD_CHUNK):
        chunk     = records[i:i+LOAD_CHUNK]
        lid_chunk = local_ids[i:i+LOAD_CHUNK]
        ok, fail  = _batch_insert(sf, "Account", chunk)
        for o in ok:
            result.inserted += 1
            result.sf_ids[lid_chunk[o["idx"]]] = o["id"]
        for f in fail:
            result.failed += 1
            result.errors.append(f"Account row {i+f['idx']}: {f['errors']}")
        log_fn(f"  Accounts: {result.inserted}/{result.total} inserted", ok=result.failed==0)
    return result


def load_contacts(sf, df, account_sf_ids: dict, log_fn) -> LoadResult:
    result = LoadResult("Contact", total=len(df))
    fields = ["FirstName","LastName","Title","Email","Phone","MobilePhone",
              "MailingStreet","MailingCity","MailingState","MailingPostalCode","MailingCountry",
              "LeadSource","Department","Description"]
    local_ids = df["Id"].tolist()
    records   = []
    for _, row in df.iterrows():
        rec = {f: row.get(f) for f in fields}
        sf_acct = account_sf_ids.get(row.get("_account_id",""), "")
        if sf_acct:
            rec["AccountId"] = sf_acct
        records.append(rec)
    for i in range(0, len(records), LOAD_CHUNK):
        chunk     = records[i:i+LOAD_CHUNK]
        lid_chunk = local_ids[i:i+LOAD_CHUNK]
        ok, fail  = _batch_insert(sf, "Contact", chunk)
        for o in ok:
            result.inserted += 1
            result.sf_ids[lid_chunk[o["idx"]]] = o["id"]
        for f in fail:
            result.failed += 1
            result.errors.append(f"Contact row {i+f['idx']}: {f['errors']}")
        log_fn(f"  Contacts: {result.inserted}/{result.total} inserted", ok=result.failed==0)
    return result


def load_opportunities(sf, df, account_sf_ids: dict, log_fn) -> LoadResult:
    result = LoadResult("Opportunity", total=len(df))
    fields = ["Name","StageName","CloseDate","Amount","Probability","Type",
              "LeadSource","Description","NextStep","ForecastCategoryName"]
    local_ids = df["Id"].tolist()
    records   = []
    for _, row in df.iterrows():
        rec = {f: row.get(f) for f in fields if row.get(f) != ""}
        sf_acct = account_sf_ids.get(row.get("_account_id",""), "")
        if sf_acct:
            rec["AccountId"] = sf_acct
        records.append(rec)
    for i in range(0, len(records), LOAD_CHUNK):
        chunk     = records[i:i+LOAD_CHUNK]
        lid_chunk = local_ids[i:i+LOAD_CHUNK]
        ok, fail  = _batch_insert(sf, "Opportunity", chunk)
        for o in ok:
            result.inserted += 1
            result.sf_ids[lid_chunk[o["idx"]]] = o["id"]
        for f in fail:
            result.failed += 1
            result.errors.append(f"Opportunity row {i+f['idx']}: {f['errors']}")
        log_fn(f"  Opportunities: {result.inserted}/{result.total} inserted", ok=result.failed==0)
    return result


def load_policies(sf, df, account_sf_ids: dict, opp_sf_ids: dict, has_opp_field: bool, log_fn) -> LoadResult:
    result = LoadResult("InsurancePolicy", total=len(df))
    fields = ["Name","PolicyType","Status","EffectiveDate","ExpirationDate",
              "PremiumAmount","PolicyNumber","Description","IssuedDate"]
    local_ids = df["Id"].tolist()
    records   = []
    for _, row in df.iterrows():
        rec = {f: row.get(f) for f in fields}
        sf_acct = account_sf_ids.get(row.get("_account_id",""), "")
        if sf_acct:
            rec["NameInsuredId"] = sf_acct
        sf_opp = opp_sf_ids.get(row.get("_opp_id",""), "")
        if sf_opp and has_opp_field:
            rec["OpportunityId__c"] = sf_opp
        # Custom fields — only include if they were requested
        for cf in ["Carrier__c","PaymentMethod__c","PaymentFrequency__c"]:
            if row.get(cf):
                rec[cf] = row.get(cf)
        records.append(rec)
    for i in range(0, len(records), LOAD_CHUNK):
        chunk     = records[i:i+LOAD_CHUNK]
        lid_chunk = local_ids[i:i+LOAD_CHUNK]
        ok, fail  = _batch_insert(sf, "InsurancePolicy", chunk)
        for o in ok:
            result.inserted += 1
            result.sf_ids[lid_chunk[o["idx"]]] = o["id"]
        for f in fail:
            result.failed += 1
            result.errors.append(f"InsurancePolicy row {i+f['idx']}: {f['errors']}")
        log_fn(f"  Policies: {result.inserted}/{result.total} inserted", ok=result.failed==0)
    return result


def check_sf_prerequisites(sf, log_fn):
    """Return dict of prerequisite checks."""
    checks = {}
    # InsurancePolicy accessible?
    try:
        sf.query("SELECT Id FROM InsurancePolicy LIMIT 1")
        checks["InsurancePolicy"] = (True, "Object accessible")
    except Exception as e:
        checks["InsurancePolicy"] = (False, str(e)[:120])
    # OpportunityId__c exists on InsurancePolicy?
    try:
        fields = sf.InsurancePolicy.describe()["fields"]
        field_names = [f["name"] for f in fields]
        if "OpportunityId__c" in field_names:
            checks["OpportunityId__c"] = (True, "Custom field exists")
        else:
            checks["OpportunityId__c"] = (False, "Field not found – policies will load without Opp link")
    except Exception as e:
        checks["OpportunityId__c"] = (False, str(e)[:120])
    # ForecastCategory editable?
    try:
        opp_fields = sf.Opportunity.describe()["fields"]
        fc = next((f for f in opp_fields if f["name"]=="ForecastCategoryName"), None)
        if fc and not fc.get("updateable", True):
            checks["ForecastCategory"] = (False, "ForecastCategoryName not updateable — will be omitted")
        else:
            checks["ForecastCategory"] = (True, "OK")
    except Exception:
        checks["ForecastCategory"] = (True, "Could not verify — proceeding")
    return checks


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
for k, v in {
    "generated": False,
    "df_campaigns": None, "df_leads": None, "df_accounts": None,
    "df_contacts": None,  "df_opps":  None, "df_policies": None,
    "sf_connected": False, "sf_instance": None, "sf_org_name": "",
    "load_log": [], "load_results": {}, "load_running": False, "load_done": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🏛️ FSC Insurance Test Data Generator</h1>
    <p>Salesforce Financial Services Cloud · Insurance Version · Sandbox Dataset Builder & Direct Loader</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# THREE-COLUMN LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
config_col, preview_col, sf_col = st.columns([1, 1.5, 1], gap="large")

# ═════════════════════════════════════════════════════════════════════════════
# LEFT — CONFIGURATION
# ═════════════════════════════════════════════════════════════════════════════
with config_col:
    st.markdown("### ⚙️ Dataset Parameters")

    with st.expander("🗺️  Geographic Scope", expanded=True):
        region = st.selectbox("Region",
            ["All 50 States","Pacific Northwest","Mountain West","Sunbelt","Northeast",
             "Southeast","Midwest","Southwest","West","Custom"])
        custom_states = []
        if region == "Custom":
            custom_states = st.multiselect("Select States", sorted(US_CITIES.keys()), default=["WA","OR","CA"])
        state_pool = custom_states if region == "Custom" else states_for_region(region)
        if state_pool:
            st.caption(f"📍 {len(state_pool)} states · {', '.join(sorted(state_pool)[:8])}{'…' if len(state_pool)>8 else ''}")

    with st.expander("📣  Campaigns", expanded=True):
        num_campaigns = st.slider("Number of Campaigns", 1, 10, 2)
        st.caption("Campaign names (one per line):")
        names_text = st.text_area("Campaign Names",
            value="Q1 2026 Home & Auto Bundle Drive\nQ2 2026 Life Insurance Awareness Campaign",
            height=90, label_visibility="collapsed")
        campaign_names_list = [n.strip() for n in names_text.strip().split("\n") if n.strip()]
        c1, c2 = st.columns(2)
        campaign_type   = c1.selectbox("Type",   ["Email","Direct Mail","Webinar","Event","Social","Other"])
        campaign_status = c2.selectbox("Status", ["In Progress","Planned","Completed","Aborted"])
        budget_range    = st.slider("Budget ($K)", 1, 500, (10,50))
        revenue_range   = st.slider("Expected Revenue ($K)", 10, 5000, (100,500))
        leads_per_campaign = st.slider("Leads per Campaign", 5, 500, 20)

    with st.expander("🏢  Accounts & Contacts", expanded=True):
        num_accounts = st.slider("Number of Accounts", 10, 1000, 100)
        contacts_per_account = st.slider("Contacts per Account", 1, 5, 2)
        sel_industries    = st.multiselect("Industries", INDUSTRIES,
            default=["Insurance","Financial Services","Healthcare","Real Estate","Manufacturing"])
        sel_acct_types    = st.multiselect("Account Types",   ACCOUNT_TYPES,   default=ACCOUNT_TYPES)
        sel_acct_sources  = st.multiselect("Account Sources", ACCOUNT_SOURCES, default=ACCOUNT_SOURCES)
        sel_contact_titles= st.multiselect("Contact Titles",  CONTACT_TITLES,  default=CONTACT_TITLES)

    with st.expander("💼  Opportunities", expanded=True):
        closed_won_pct     = st.slider("% Closed Won", 0, 100, 50)
        opp_amount_range   = st.slider("Amount Range ($K)", 5, 2000, (25,300))
        closed_months_back = st.slider("Closed Won: months back", 1, 36, 18)
        open_months_fwd    = st.slider("Open: months ahead",    1, 24,  9)
        sel_opp_types      = st.multiselect("Opp Types", OPP_TYPES, default=OPP_TYPES)

    with st.expander("📋  Insurance Policies", expanded=True):
        sel_policy_types = st.multiselect("Policy Types", POLICY_TYPES,
            default=["Homeowners","Auto","Life","Commercial Property","General Liability","Workers Compensation","Umbrella"])
        sel_carriers       = st.multiselect("Carriers",          CARRIERS[:10],    default=CARRIERS[:10])
        premium_pct_range  = st.slider("Premium % of Opp Amount", 1, 20, (3,8))
        sel_payment_methods= st.multiselect("Payment Methods",   PAYMENT_METHODS,  default=PAYMENT_METHODS)
        sel_payment_freqs  = st.multiselect("Payment Frequencies",PAYMENT_FREQS,   default=PAYMENT_FREQS)

    with st.expander("🎲  Advanced", expanded=False):
        seed_val = st.number_input("Random Seed (0 = truly random)", min_value=0, max_value=99999, value=0)

    st.markdown("---")
    generate_btn = st.button("⚡  Generate Dataset", type="primary", use_container_width=True)

# ═════════════════════════════════════════════════════════════════════════════
# GENERATION LOGIC
# ═════════════════════════════════════════════════════════════════════════════
if generate_btn:
    errors = []
    if not state_pool:        errors.append("Select at least one state.")
    if not sel_industries:    errors.append("Select at least one Industry.")
    if not sel_policy_types:  errors.append("Select at least one Policy Type.")
    if not sel_carriers:      errors.append("Select at least one Carrier.")
    if not sel_payment_methods: errors.append("Select at least one Payment Method.")
    if not sel_payment_freqs:   errors.append("Select at least one Payment Frequency.")

    if errors:
        with preview_col:
            for e in errors:
                st.error(f"⚠️ {e}")
    else:
        rng_seed = seed_val if seed_val > 0 else random.randint(1,99999)
        random.seed(rng_seed)
        with preview_col:
            with st.spinner("Generating…"):
                df_camp  = generate_campaigns(num_campaigns, campaign_names_list, campaign_type,
                                              campaign_status, budget_range, revenue_range)
                df_leads = generate_leads(num_campaigns*leads_per_campaign, df_camp, state_pool,
                                          LEAD_STATUSES, LEAD_SOURCES, sel_industries)
                df_accts = generate_accounts(num_accounts, state_pool, sel_industries,
                                             sel_acct_types, sel_acct_sources)
                df_cont  = generate_contacts(df_accts, contacts_per_account, sel_contact_titles)
                df_opps  = generate_opportunities(df_accts, closed_won_pct, sel_opp_types,
                                                  opp_amount_range, closed_months_back, open_months_fwd)
                df_pols  = generate_policies(df_opps, df_accts, sel_policy_types, sel_carriers,
                                             sel_payment_methods, sel_payment_freqs, premium_pct_range)

        st.session_state.update({
            "df_campaigns": df_camp, "df_leads": df_leads, "df_accounts": df_accts,
            "df_contacts": df_cont, "df_opps": df_opps, "df_policies": df_pols,
            "generated": True, "_seed_used": rng_seed,
            "load_log": [], "load_results": {}, "load_running": False, "load_done": False,
        })
        st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# MIDDLE — PREVIEW & DOWNLOAD
# ═════════════════════════════════════════════════════════════════════════════
with preview_col:
    if not st.session_state.generated:
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem;color:#888;
             border:2px dashed #dce7f5;border-radius:12px;margin-top:1rem;">
            <div style="font-size:3rem;">🏛️</div>
            <div style="font-size:1.2rem;font-weight:600;margin-top:1rem;color:#2563a8;">Ready to Generate</div>
            <div style="margin-top:0.5rem;">Configure parameters on the left,<br>then click <strong>Generate Dataset</strong>.</div>
        </div>""", unsafe_allow_html=True)
    else:
        df_camp  = st.session_state.df_campaigns
        df_leads = st.session_state.df_leads
        df_accts = st.session_state.df_accounts
        df_cont  = st.session_state.df_contacts
        df_opps  = st.session_state.df_opps
        df_pols  = st.session_state.df_policies
        cwc = int(df_opps["_is_won"].sum()) if "_is_won" in df_opps.columns else 0
        seed_used = st.session_state.get("_seed_used","?")

        st.markdown(
            f"""<div class="metric-row">
            {metric_html(len(df_camp), "Campaigns")}
            {metric_html(len(df_leads),"Leads")}
            {metric_html(len(df_accts),"Accounts")}
            {metric_html(len(df_cont), "Contacts")}
            {metric_html(len(df_opps), "Opps")}
            {metric_html(cwc,          "Closed Won")}
            {metric_html(len(df_pols), "Policies")}
            </div>""", unsafe_allow_html=True)

        st.markdown(
            f'<div class="success-box">✅ Generated · Seed <code>{seed_used}</code> · '
            f'{df_accts["BillingState"].nunique()} states</div>', unsafe_allow_html=True)

        # Downloads
        st.markdown("#### 📥 Download")
        all_dfs = {
            "01_Campaigns.csv": df_camp, "02_Leads.csv": df_leads,
            "03_Accounts.csv": df_accts, "04_Contacts.csv": df_cont,
            "05_Opportunities.csv": df_opps, "06_InsurancePolicies.csv": df_pols,
        }
        dc1, dc2 = st.columns([1.3,1])
        with dc1:
            st.download_button("⬇️  Download All (ZIP)", data=build_zip(all_dfs),
                file_name=f"fsc_test_data_seed{seed_used}.zip",
                mime="application/zip", use_container_width=True, type="primary")
        with dc2:
            sel_file = st.selectbox("Individual file:", list(all_dfs.keys()), label_visibility="collapsed")
        if sel_file:
            st.download_button(f"⬇️  {sel_file}", data=df_to_csv_bytes(all_dfs[sel_file]),
                file_name=sel_file, mime="text/csv", use_container_width=True)

        st.markdown("---")
        # Preview tabs
        st.markdown("#### 🔍 Preview")
        tabs = st.tabs(["📣 Campaigns","👤 Leads","🏢 Accounts","👥 Contacts","💼 Opps","📋 Policies"])

        def preview_tab(tab, df, extra_metrics=None):
            xdf = df[[c for c in df.columns if not c.startswith("_")]]
            with tab:
                cols = st.columns(3 + (len(extra_metrics) if extra_metrics else 0))
                cols[0].metric("Rows",    f"{len(xdf):,}")
                cols[1].metric("Columns", len(xdf.columns))
                if "BillingState" in xdf.columns:
                    cols[2].metric("States", xdf["BillingState"].nunique())
                elif "State" in xdf.columns:
                    cols[2].metric("States", xdf["State"].nunique())
                else:
                    cols[2].metric("IDs", xdf["Id"].nunique())
                if extra_metrics:
                    for j,(lbl,val) in enumerate(extra_metrics):
                        cols[3+j].metric(lbl, val)
                st.dataframe(xdf.head(8), use_container_width=True, hide_index=True)

        preview_tab(tabs[0], df_camp)
        preview_tab(tabs[1], df_leads)
        preview_tab(tabs[2], df_accts)
        preview_tab(tabs[3], df_cont)

        with tabs[4]:
            xdf = df_opps[[c for c in df_opps.columns if not c.startswith("_")]]
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Total",      f"{len(xdf):,}")
            c2.metric("Closed Won", f"{cwc:,}")
            c3.metric("Pipeline",   f"{len(xdf)-cwc:,}")
            c4.metric("Value",      f"${df_opps['Amount'].sum():,.0f}")
            st.dataframe(xdf.head(8), use_container_width=True, hide_index=True)

        with tabs[5]:
            c1,c2,c3,c4 = st.columns(4)
            prem = df_pols["PremiumAmount"].sum() if len(df_pols) else 0
            c1.metric("Policies",    f"{len(df_pols):,}")
            c2.metric("Total Prem",  f"${prem:,.0f}")
            c3.metric("Avg Premium", f"${prem/max(len(df_pols),1):,.0f}")
            c4.metric("Types",       df_pols["PolicyType"].nunique() if len(df_pols) else 0)
            xdf = df_pols[[c for c in df_pols.columns if not c.startswith("_")]]
            st.dataframe(xdf.head(8), use_container_width=True, hide_index=True)

        # Geo chart
        st.markdown("---")
        st.markdown("#### 🗺️ Geographic Distribution")
        sc = df_accts["BillingState"].value_counts().reset_index()
        sc.columns = ["State","Accounts"]
        g1, g2 = st.columns(2)
        with g1:
            st.dataframe(sc.head(12), use_container_width=True, hide_index=True)
        with g2:
            st.bar_chart(sc.set_index("State").head(20), height=260, color="#2563a8")

# ═════════════════════════════════════════════════════════════════════════════
# RIGHT — SALESFORCE CONNECTION & LOADER
# ═════════════════════════════════════════════════════════════════════════════
with sf_col:
    st.markdown("### ☁️  Salesforce Loader")

    # ── CONNECTION PANEL ──────────────────────────────────────────────────
    with st.expander("🔌  Connection", expanded=not st.session_state.sf_connected):
        with st.form("sf_connect_form"):
            st.markdown("**Salesforce Credentials**")
            st.caption("Credentials are used only for this session and never stored.")
            instance_url   = st.text_input("Instance URL",    placeholder="https://myorg.sandbox.my.salesforce.com")
            sf_username    = st.text_input("Username",        placeholder="user@example.com.sandbox")
            sf_password    = st.text_input("Password",        type="password")
            sf_token       = st.text_input("Security Token",  type="password",
                                           help="Append your token if IP is not whitelisted. Found in: My Settings > Personal > Reset My Security Token")
            is_sandbox     = st.checkbox("Sandbox / Test Org", value=True)
            connect_btn    = st.form_submit_button("🔗  Connect to Salesforce", use_container_width=True, type="primary")

        if connect_btn:
            if not sf_username or not sf_password:
                st.error("Username and password are required.")
            else:
                with st.spinner("Connecting…"):
                    try:
                        sf = sf_connect(instance_url, sf_username, sf_password, sf_token, is_sandbox)
                        org_info = sf.query("SELECT Name, OrganizationType FROM Organization LIMIT 1")
                        org_name = org_info["records"][0].get("Name","Unknown") if org_info["records"] else "Unknown"
                        org_type = org_info["records"][0].get("OrganizationType","") if org_info["records"] else ""
                        st.session_state.sf_connected = True
                        st.session_state.sf_instance  = sf
                        st.session_state.sf_org_name  = f"{org_name} ({org_type})"
                        st.session_state.sf_username   = sf_username
                        st.rerun()
                    except Exception as e:
                        st.error(f"Connection failed: {e}")

    # ── CONNECTION STATUS ─────────────────────────────────────────────────
    if st.session_state.sf_connected:
        st.markdown(
            f'<div class="sf-connected">✅ Connected · <strong>{st.session_state.sf_org_name}</strong><br>'
            f'<small>{st.session_state.get("sf_username","")}</small></div>',
            unsafe_allow_html=True)
        if st.button("🔌 Disconnect", use_container_width=True):
            st.session_state.sf_connected = False
            st.session_state.sf_instance  = None
            st.rerun()
    else:
        st.markdown('<div class="sf-disconnected">⚪ Not connected — enter credentials above.</div>',
                    unsafe_allow_html=True)

    # ── PREREQUISITE CHECK ────────────────────────────────────────────────
    if st.session_state.sf_connected:
        with st.expander("🔍  Prerequisite Check", expanded=False):
            if st.button("Run Checks", use_container_width=True):
                with st.spinner("Checking org…"):
                    checks = check_sf_prerequisites(
                        st.session_state.sf_instance,
                        lambda msg, ok=True: None
                    )
                for name, (passed, msg) in checks.items():
                    icon = "✅" if passed else "⚠️"
                    st.markdown(f"{icon} **{name}**: {msg}")

    # ── LOAD OPTIONS ──────────────────────────────────────────────────────
    if st.session_state.sf_connected and st.session_state.generated:
        st.markdown("---")
        st.markdown("#### 📤 Load Options")

        with st.expander("⚙️  Load Settings", expanded=True):
            load_campaigns_chk  = st.checkbox("Load Campaigns",         value=True)
            load_leads_chk      = st.checkbox("Load Leads",             value=True)
            load_accounts_chk   = st.checkbox("Load Accounts",          value=True)
            load_contacts_chk   = st.checkbox("Load Contacts",          value=True)
            load_opps_chk       = st.checkbox("Load Opportunities",      value=True)
            load_policies_chk   = st.checkbox("Load Insurance Policies", value=True)
            st.markdown("---")
            include_opp_field   = st.checkbox("InsurancePolicy has OpportunityId__c",  value=True,
                help="Uncheck if the custom Opportunity lookup hasn't been created yet.")
            include_custom_fields = st.checkbox("Include Carrier / Payment custom fields", value=True,
                help="Uncheck if Carrier__c, PaymentMethod__c, PaymentFrequency__c don't exist in your org.")

        # Warn if nothing selected
        any_selected = any([load_campaigns_chk, load_leads_chk, load_accounts_chk,
                            load_contacts_chk, load_opps_chk, load_policies_chk])

        if not any_selected:
            st.markdown('<div class="warn-box">⚠️ No objects selected for load.</div>', unsafe_allow_html=True)

        total_records = sum([
            len(st.session_state.df_campaigns)  if load_campaigns_chk else 0,
            len(st.session_state.df_leads)       if load_leads_chk else 0,
            len(st.session_state.df_accounts)    if load_accounts_chk else 0,
            len(st.session_state.df_contacts)    if load_contacts_chk else 0,
            len(st.session_state.df_opps)        if load_opps_chk else 0,
            len(st.session_state.df_policies)    if load_policies_chk else 0,
        ])
        st.markdown(
            f'<div class="warn-box">⚠️ This will insert <strong>{total_records:,} records</strong> '
            f'into <strong>{st.session_state.sf_org_name}</strong>. '
            f'Only run against sandbox orgs.</div>', unsafe_allow_html=True)

        load_btn = st.button(
            f"🚀  Load {total_records:,} Records to Salesforce",
            type="primary", use_container_width=True,
            disabled=st.session_state.load_running or not any_selected)

        # ── EXECUTE LOAD ──────────────────────────────────────────────────
        if load_btn and not st.session_state.load_running:
            st.session_state.load_running = True
            st.session_state.load_done    = False
            st.session_state.load_log     = []
            st.session_state.load_results = {}

            log = st.session_state.load_log

            def log_fn(msg, ok=True):
                ts   = datetime.now().strftime("%H:%M:%S")
                cls  = "log-success" if ok else "log-error"
                log.append(f'<span class="{cls}">[{ts}]</span> {msg}')

            sf   = st.session_state.sf_instance
            camp = st.session_state.df_campaigns
            leads= st.session_state.df_leads
            accts= st.session_state.df_accounts
            cont = st.session_state.df_contacts
            opps = st.session_state.df_opps
            pols = st.session_state.df_policies

            campaign_ids_map = {}
            account_ids_map  = {}
            opp_ids_map      = {}

            try:
                # 1. Campaigns
                if load_campaigns_chk:
                    log_fn("━━━ Loading Campaigns…", ok=True)
                    res = load_campaigns(sf, camp, log_fn)
                    campaign_ids_map = res.sf_ids
                    st.session_state.load_results["Campaign"] = res

                # 2. Leads
                if load_leads_chk:
                    log_fn("━━━ Loading Leads…", ok=True)
                    res = load_leads(sf, leads, campaign_ids_map, log_fn)
                    st.session_state.load_results["Lead"] = res

                # 3. Accounts
                if load_accounts_chk:
                    log_fn("━━━ Loading Accounts…", ok=True)
                    res = load_accounts(sf, accts, log_fn)
                    account_ids_map = res.sf_ids
                    st.session_state.load_results["Account"] = res

                # 4. Contacts
                if load_contacts_chk:
                    log_fn("━━━ Loading Contacts…", ok=True)
                    res = load_contacts(sf, cont, account_ids_map, log_fn)
                    st.session_state.load_results["Contact"] = res

                # 5. Opportunities
                if load_opps_chk:
                    log_fn("━━━ Loading Opportunities…", ok=True)
                    res = load_opportunities(sf, opps, account_ids_map, log_fn)
                    opp_ids_map = res.sf_ids
                    st.session_state.load_results["Opportunity"] = res

                # 6. Insurance Policies
                if load_policies_chk:
                    log_fn("━━━ Loading Insurance Policies…", ok=True)
                    res = load_policies(sf, pols, account_ids_map, opp_ids_map,
                                        include_opp_field, log_fn)
                    st.session_state.load_results["InsurancePolicy"] = res

                log_fn("━━━ Load complete ✓", ok=True)

            except Exception as e:
                log_fn(f"FATAL ERROR: {e}", ok=False)

            st.session_state.load_running = False
            st.session_state.load_done    = True
            st.rerun()

    elif st.session_state.sf_connected and not st.session_state.generated:
        st.markdown("""
        <div style="text-align:center;padding:2rem 1rem;color:#888;
             border:2px dashed #dce7f5;border-radius:8px;margin-top:1rem;">
            <div style="font-size:2rem;">⚡</div>
            <div style="margin-top:0.5rem;font-size:0.9rem;">Generate a dataset first,<br>then load it here.</div>
        </div>""", unsafe_allow_html=True)

    # ── LOAD LOG & RESULTS ────────────────────────────────────────────────
    if st.session_state.load_log:
        st.markdown("---")
        st.markdown("#### 📋 Load Log")

        log_html = "\n".join(st.session_state.load_log)
        st.markdown(
            f'<div class="load-log">{log_html}</div>',
            unsafe_allow_html=True)

        if st.session_state.load_done and st.session_state.load_results:
            st.markdown("#### 📊 Load Summary")
            summary_rows = []
            all_errors   = []
            for obj, res in st.session_state.load_results.items():
                status = "✅ Success" if res.failed == 0 else f"⚠️ {res.failed} failed"
                summary_rows.append({"Object": obj, "Total": res.total,
                    "Inserted": res.inserted, "Failed": res.failed, "Status": status})
                all_errors.extend([f"[{obj}] {e}" for e in res.errors])
            st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

            if all_errors:
                with st.expander(f"⚠️  {len(all_errors)} Errors", expanded=True):
                    for e in all_errors[:50]:
                        st.markdown(f'<div class="error-box">{e}</div>', unsafe_allow_html=True)
                    if len(all_errors) > 50:
                        st.caption(f"…and {len(all_errors)-50} more.")
            else:
                st.markdown('<div class="success-box">✅ All records loaded successfully with no errors.</div>',
                            unsafe_allow_html=True)

            # Quick SOQL verification links
            with st.expander("🔎 Verify in Salesforce"):
                st.caption("Run these in Developer Console → Query Editor:")
                for obj in st.session_state.load_results:
                    st.code(f"SELECT COUNT() FROM {obj}", language="sql")

    # ── ROLLBACK ──────────────────────────────────────────────────────────
    if st.session_state.load_done and st.session_state.load_results and st.session_state.sf_connected:
        st.markdown("---")
        with st.expander("🗑️  Rollback / Delete Loaded Records"):
            st.markdown('<div class="warn-box">⚠️ This will <strong>permanently delete</strong> all records inserted in the last load from Salesforce. This cannot be undone.</div>', unsafe_allow_html=True)
            confirm_delete = st.checkbox("I understand — delete all loaded records")
            if st.button("🗑️  Delete Loaded Records", disabled=not confirm_delete, use_container_width=True):
                sf = st.session_state.sf_instance
                # Delete in reverse dependency order
                delete_order = ["InsurancePolicy","Opportunity","Contact","Account","Lead","Campaign"]
                rollback_log = []
                for obj in delete_order:
                    res = st.session_state.load_results.get(obj)
                    if not res or not res.sf_ids:
                        continue
                    ids = list(res.sf_ids.values())
                    deleted = 0
                    errors  = []
                    try:
                        import requests
                        sf_obj = getattr(sf, obj, None)
                        if sf_obj is None:
                            continue
                        for i in range(0, len(ids), LOAD_CHUNK):
                            chunk = ids[i:i+LOAD_CHUNK]
                            endpoint = f"{sf.base_url}composite/sobjects?ids={','.join(chunk)}&allOrNone=false"
                            headers  = {"Authorization": f"Bearer {sf.session_id}"}
                            resp     = requests.delete(endpoint, headers=headers)
                            results  = resp.json()
                            for r in results:
                                if r.get("success"):
                                    deleted += 1
                                else:
                                    errs = "; ".join(e.get("message","?") for e in r.get("errors",[]))
                                    errors.append(errs)
                        rollback_log.append(f"✅ {obj}: deleted {deleted}, failed {len(errors)}")
                    except Exception as e:
                        rollback_log.append(f"❌ {obj}: {e}")
                for line in rollback_log:
                    st.markdown(line)
                st.session_state.load_done    = False
                st.session_state.load_results = {}
                st.session_state.load_log     = []
