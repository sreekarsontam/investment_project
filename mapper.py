company_to_ticker = {

    "Reliance": "RELIANCE.NS",

    "Reliance Industries": "RELIANCE.NS",

    "TCS": "TCS.NS",

    "Tata Consultancy Services": "TCS.NS",

    "Infosys": "INFY.NS"

}

def get_ticker(company):
    return company_to_ticker.get(company)