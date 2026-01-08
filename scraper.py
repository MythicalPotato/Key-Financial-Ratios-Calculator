import requests
import pandas as pd
from datetime import datetime
import os
import numpy as np

# --- USER CONFIGURATION ---
#Ticker Prompt
print("Please enter the list of tickers you want to analyze (separated by commas):")
user_input = input("Tickers: ")
TICKERS = [ticker.strip().upper() for ticker in user_input.split(",") if ticker.strip()]
# TICKERS = ['AAPL', 'MSFT', 'GOOGL']  # Example default tickers

#Time Period Prompt
print("Please input the number of years of data to analyze:")
user_years = input("Years: ")
AMT_YEARS = int(user_years)
# AMT_YEARS = 5  # Example default years

# --- CONFIGURATION ---
# IMPORTANT: Change this to your real email or valid user agent per SEC guidelines
# SEC EDGAR requires a declarative User-Agent including a contact email.
# Generic or empty User-Agents may result in 403 Forbidden errors.
HEADERS = {'User-Agent': 'ValidUser/1.0 (valid.email@example.com)'}

# --- MANUAL SPLITS FOR SPECIFIC TICKERS ---
# Use this dictionary to manually specify stock splits that 
# may not be auto-detected correctly.
# Format: 'TICKER': {YEAR: SPLIT_RATIO}
# --- UPDATED MANUAL SPLIT INPUT LOGIC ---

print("Optional: Input Stock Splits Manually? (y/n):")
user_split_input = input().strip().lower()

MANUAL_SPLITS = {
    # Predefined splits can be added here
    # Example:  'AAPL': {2020: 4.0}
    'TSLA': {2022: 3.0, 2020: 5.0},
}

if user_split_input == 'y':
    # Removed MANUAL_SPLITS = {} to preserve existing hardcoded splits
    while True:
        print("\nEnter ticker symbol (or type 'done' to finish):")
        ticker = input().strip().upper()
        if ticker == 'DONE':
            break
        
        try:
            print(f"Enter year of split for {ticker}:")
            year_input = input().strip()
            year = int(year_input)
            
            print(f"Enter split ratio for {ticker} in {year} (e.g., 2.0 for 2-for-1):")
            ratio_input = input().strip()
            ratio = float(ratio_input)
            
            # Update existing or create new entry
            if ticker not in MANUAL_SPLITS:
                MANUAL_SPLITS[ticker] = {}
            MANUAL_SPLITS[ticker][year] = ratio
            print(f"Added: {ticker} {year} split of {ratio}x")
            
        except ValueError:
            print("Invalid input. Please enter numbers for Year and Ratio.")



# --- MAPPINGS ---

# Maps standard financial labels to multiple possible XBRL tags used by the SEC.
# This accounts for variations in GAAP reporting across different companies and industries,
# ensuring the parser can find the correct data even if naming conventions differ.
# Format: 'Standard Metric Name': ['TagOption1', 'TagOption2', ...]
is_map = {
    'Net Sales / Revenue': [
        'RevenuesNetOfInterestExpense',         
        'RevenueNetOfInterestExpense',          
        'TotalRevenuesNetOfInterestExpense',  
        'NetRevenues',                          
        'RevenueFromContractWithCustomerExcludingAssessedTax', 
        'Revenues', 
        'OperatingRevenue', 
        'SalesRevenueNet', 
        'SalesRevenueGoodsNet',
        'NonInterestIncome',
        'NonInterestRevenues',
        'InterestIncomeExpenseNet',                      
        'InterestAndDividendIncomeOperating',   
        ],
    'COGS': [
        'CostOfGoodsAndServicesSold', 
        'CostOfRevenue', 
        'CostOfGoodsSold', 
        'CostOfSales'
        ],
    'Operating Income': [
        'OperatingIncomeLoss',
        'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest',
        'IncomeLossFromContinuingOperationsBeforeIncomeTaxes',
        'IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments',
        ],
    'Net Income': [
        'NetIncomeLoss', 
        'ProfitLoss', 
        'NetIncomeLossAvailableToCommonStockholdersBasic'
        ],
    'Diluted Shares Outstanding': [
        'WeightedAverageNumberOfDilutedSharesOutstanding',
        'WeightedAverageNumberOfSharesOutstandingBasicAndDiluted',
        'WeightedAverageNumberOfDilutedSharesOutstandingContinuingOperations',
        'EntityCommonStockSharesOutstanding', 
        'CommonStockSharesOutstanding'       
        ],
    'Preferred Dividends': [
        'DividendsPreferredStock', 
        'PreferredStockDividendsAndOtherAdjustments', 
        'DividendsPreferredStockCash'
        ],
    'Earnings Per Share (Diluted)': [
        'EarningsPerShareDiluted', 
        'EarningsPerShareBasicAndDiluted', 
        'IncomeLossFromContinuingOperationsPerDilutedShare'
        ],
    'Stock Split Ratio': [
        'StockholdersEquityNoteStockSplitConversionRatio', 
        'CommonStockStockSplit', 
        'StockSplitConversionRatio', 
        'StockDividendSplitRatio', 
        'SplitRatio'
        ],
}

bs_map = {
    'Current Assets': ['AssetsCurrent'],
    'Accounts Receivable': [
        'FinancingReceivablesNet',             
        'LoansAndLeasesReceivableNet',         
        'LoansReceivableNet',
        'CardMemberLoansNet',                  
        'CardMemberReceivablesNet',            
        'LoansAndCardMemberReceivablesNet',    
        'CreditCardReceivables',
        'ReceivablesFromBrokerDealersAndClearingOrganizations', 
        'AccountsReceivableNetCurrent', 
        'ReceivablesNetCurrent',
        'TradeAndOtherReceivablesNet',
        'AccountsReceivableNet',
        'ReceivablesNet',
        ],
    'Current Liabilities': ['LiabilitiesCurrent'],
    'Total Assets': ['Assets', 'AssetsNet'],
    'Total Shareholders Equity': [
        'StockholdersEquity', 
        'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest',
        'PartnersCapital',
        'PartnersCapitalIncludingPortionAttributableToNoncontrollingInterest',
        'PartnersCapitalAccount'
        ],
}

cf_map = {
    'Cash Dividends Paid': ['PaymentsOfDividendsCommonStock', 'PaymentsOfDividends'], 
    'Cash Flow from Operations': [
        'NetCashProvidedByUsedInOperatingActivities', 
        'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations'
        ],
}

#Combined Master Map
MASTER_MAP = is_map | bs_map | cf_map

# --- FUNCTIONS ---

def get_cik(ticker):
    # Fetch CIK for a given ticker symbol
    url = "https://www.sec.gov/files/company_tickers.json"
    r = requests.get(url, headers=HEADERS)
    data = r.json()
    for entry in data.values():
        if entry['ticker'] == ticker.upper():
            return str(entry['cik_str']).zfill(10)
    raise ValueError(f"Ticker {ticker} not found.")

def get_data(cik):
    # Fetch company facts JSON data from SEC EDGAR
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        print(f"Error fetching data: Status {r.status_code}")
        return {}
    return r.json()

def parse_statement(raw_data, tag_map):
    # Parse the raw SEC data into a structured DataFrame
    if 'facts' not in raw_data: return pd.DataFrame()
    us_gaap = raw_data['facts']['us-gaap']
    rows = []

    for label, tags in tag_map.items():
        for tag in tags:
            if tag in us_gaap:
                units_dict = us_gaap[tag]['units']
                for unit_name, records in units_dict.items():
                    sorted_records = sorted(records, key=lambda x: (x.get('fy') or 0, x.get('end') or '0000-00-00'), reverse=True)
                    
                    for record in sorted_records:
                        if record.get('form') in ['10-K', '10-K/A']:
                            segment = record.get('segment', 'Total')
                            allow = False
                            
                            if segment == 'Total': 
                                allow = True
                            elif label in ['Diluted Shares Outstanding', 'Accounts Receivable', 'Net Sales / Revenue']:
                                allow = True
                            
                            if allow:
                                is_valid = True
                                if 'start' in record and 'end' in record:
                                    try:
                                        s = datetime.strptime(record['start'], '%Y-%m-%d')
                                        e = datetime.strptime(record['end'], '%Y-%m-%d')
                                        # Filter for data covering ~1 year to isolate annual (10-K) figures from quarterly (10-Q) filings.
                                        if (e - s).days < 360: is_valid = False
                                    except: pass
                                
                                if is_valid:
                                    safe_year = record.get('fy') or 0
                                    
                                    rows.append({
                                        'Metric': label,
                                        'Year': safe_year,
                                        'Value': record['val'],
                                        'Segment': segment,
                                        'Tag': tag 
                                    })

    unique_data = {}
    deferred_metrics = ['Diluted Shares Outstanding']
    deferred_rows = []

    for row in rows:
        if row['Metric'] in deferred_metrics:
            deferred_rows.append(row)
            continue

        key = (row['Metric'], row['Year'], row['Segment'])
        if key not in unique_data:
            unique_data[key] = row
        else:
            if unique_data[key]['Value'] == 0 and row['Value'] != 0:
                unique_data[key] = row
            
    final_rows = list(unique_data.values()) + deferred_rows
    df = pd.DataFrame(final_rows)
    
    if df.empty: return pd.DataFrame()

    df = consolidate_shares(df)

    current_year = pd.Timestamp.now().year
    
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce').fillna(0).astype(int)
    
    df = df[df['Year'] >= (current_year - (AMT_YEARS + 2))]

    df = df.sort_values('Value', ascending=False)
    return df.pivot_table(index='Year', columns='Metric', values='Value', aggfunc='first').sort_index(ascending=False)

def consolidate_shares(df):
    # Diluted shares are handled separately to avoid 'double-counting' sub-segments. 
    # We prioritize the 'Total' company tag; if unavailable, we sum reported segments 
    # to reconstruct the full share count required for accurate EPS calculations.
    share_metric = 'Diluted Shares Outstanding'
    shares_df = df[df['Metric'] == share_metric].copy()
    other_df = df[df['Metric'] != share_metric]
    
    if shares_df.empty:
        return df

    final_rows = []
    
    for year, group in shares_df.groupby('Year'):

        if 'Segment' in group.columns:
            consolidated = group[group['Segment'].isin(['Total', None, ''])]
        else:
            consolidated = group
        
        use_total = False
        if not consolidated.empty:
            total_val = consolidated.iloc[0]['Value']
            if total_val > 0:
                final_rows.append(consolidated.iloc[0].to_dict())
                use_total = True
        
        if not use_total:
            total_val = group['Value'].sum()
            if total_val > 0:
                new_record = group.iloc[0].to_dict()
                new_record['Value'] = total_val
                new_record['Segment'] = 'Total'
                final_rows.append(new_record)

    shares_final_df = pd.DataFrame(final_rows)
    return pd.concat([other_df, shares_final_df], ignore_index=True)

def drop_duplicates(rows):
    # Drop duplicate entries, prioritizing non-zero values
    unique_data = {}
    for row in rows:
        seg = row.get('Segment', 'Total')
        key = (row['Metric'], row['Year'], seg)
        if key not in unique_data:
            unique_data[key] = row
        else:
            if unique_data[key]['Value'] == 0 and row['Value'] != 0:
                unique_data[key] = row
                
    return list(unique_data.values())

def stocksplit_check(df, ticker):
    required_cols = ['Net Income', 'Preferred Dividends', 'Diluted Shares Outstanding', 'Earnings Per Share (Diluted)']
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0.0

    df = df.sort_index(ascending=False)
    years = df.index.tolist()
    
    for i in range(len(years) - 1):
        curr_year = years[i]
        prev_year = years[i+1]
        if (curr_year - prev_year) != 1: continue

        # 1. CHECK MANUAL OVERRIDE FIRST
        manual_ratio = MANUAL_SPLITS.get(ticker, {}).get(curr_year)
        
        # 2. AUTO-DETECT LOGIC (CLIFF CHECK)
        curr_shares = df.loc[curr_year, 'Diluted Shares Outstanding']
        prev_shares = df.loc[prev_year, 'Diluted Shares Outstanding']
        
        detected_ratio = 1.0
        if curr_shares > 0 and prev_shares > 0:
            actual_jump = curr_shares / prev_shares
            if actual_jump > 1.4:
                detected_ratio = float(round(actual_jump))

        # USE MANUAL IF EXISTS, ELSE USE DETECTED
        # A 1.4x threshold differentiates formal stock splits (e.g., 3-for-2 or 2-for-1)
        # from standard share dilution or small issuances, which rarely exceed 40% annually. 
        # Ratios are rounded to the nearest integer to align with standard split conventions.
        final_ratio = manual_ratio if manual_ratio else (detected_ratio if detected_ratio > 1.4 else 1.0)

        if final_ratio > 1.1:
            print(f"  [SPLIT] Applying {final_ratio}x fix for {ticker} in {curr_year} and prior.")
            mask_older = df.index <= prev_year
            df.loc[mask_older, 'Diluted Shares Outstanding'] *= final_ratio
            
            # Recalculate EPS for the affected years
            df.loc[mask_older, 'Earnings Per Share (Diluted)'] = (
                (df.loc[mask_older, 'Net Income'] - df.loc[mask_older, 'Preferred Dividends']) / 
                df.loc[mask_older, 'Diluted Shares Outstanding']
            )

    # Final safety fill for missing EPS
    mask_missing = (df['Earnings Per Share (Diluted)'] == 0) | (df['Earnings Per Share (Diluted)'].isna())
    df.loc[mask_missing, 'Earnings Per Share (Diluted)'] = (
        (df.loc[mask_missing, 'Net Income'] - df.loc[mask_missing, 'Preferred Dividends']) / 
        df.loc[mask_missing, 'Diluted Shares Outstanding']
    )

    return df

def make_calculations(df):
    all_expected_metrics = list(is_map.keys()) + list(bs_map.keys()) + list(cf_map.keys())
    for metric in all_expected_metrics:
        if metric not in df.columns:
            df[metric] = 0.0

    # Calculate Total Liabilities
    df = df.fillna(0)
    df['Total Liabilities'] = df['Total Assets'] - df['Total Shareholders Equity']
    
    # EPS is handled in stocksplit, but ensuring safe division here
    mask_diluted = df['Earnings Per Share (Diluted)'] == 0
    df.loc[mask_diluted, 'Earnings Per Share (Diluted)'] = df['Net Income'] / df['Diluted Shares Outstanding'].replace(0, np.nan)

    # --- RATIO CALCULATIONS ---
    
    df['Current Ratio'] = df['Current Assets'] / df['Current Liabilities']
    
    avg_assets = (df['Total Assets'].shift(-1) + df['Total Assets']) / 2
    avg_equity = (df['Total Shareholders Equity'].shift(-1) + df['Total Shareholders Equity']) / 2
    
    df['Return on Assets (ROA)'] = df['Net Income'] / avg_assets
    df['Return on Equity (ROE)'] = df['Net Income'] / avg_equity
    df['Return on Sales (ROS)'] = df['Net Income'] / df['Net Sales / Revenue']
    
    df['Average Collection Period (Days Sales Outstanding)'] = (df['Accounts Receivable'] / df['Net Sales / Revenue']) * 365
    df['Debt-to-Equity Ratio'] = df['Total Liabilities'] / df['Total Shareholders Equity']
    df['Asset Turnover'] = df['Net Sales / Revenue'] / avg_assets
    df['Dividend Payout Ratio'] = df['Cash Dividends Paid'] / df['Net Income']
    
    df['Gross Profit Margin'] = (df['Net Sales / Revenue'] - df['COGS']) / df['Net Sales / Revenue']
    df['Operating Margin'] = df['Operating Income'] / df['Net Sales / Revenue']
    df['Operating Cash Flow Ratio'] = df['Cash Flow from Operations'] / df['Current Liabilities']
    
    return df

def scale_data(df): 
   # Uses 'Net Sales / Revenue' as a benchmark for the company's financial magnitude. 
   # This ensures the entire report uses a consistent scale (Millions vs. Thousands), 
   # making the final Excel output readable while maintaining relative proportions.
    df_scaled = df.copy()
    max_val = df_scaled['Net Sales / Revenue'].max() if 'Net Sales / Revenue' in df_scaled.columns else 0

    if max_val > 1_000_000_000:
        scale = 1_000_000
        suffix = "Millions"
    elif max_val > 1_000_000:
        scale = 1_000
        suffix = "Thousands"
    else:
        scale = 1
        suffix = "N/A"
    
    exclude_cols = ['Earnings Per Share (Diluted)']
    raw_metric_cols = list(MASTER_MAP.keys()) + ['Total Liabilities']
    cols_to_scale = [col for col in df_scaled.columns if col in raw_metric_cols and col not in exclude_cols]
    
    df_scaled[cols_to_scale] = df_scaled[cols_to_scale] / scale
    return df_scaled , suffix

# --- MAIN EXECUTION ---

if __name__ == "__main__":
    print("\nEnter a name for the output folder (Press Enter for default 'Financial_Reports'):")
    user_folder = input().strip()
    
    # Use default if user types nothing
    folder_name = user_folder if user_folder else "Financial_Reports"
    
    # Create the folder
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"Created new folder: {folder_name}")
    else:
        print(f"Using existing folder: {folder_name}")
    
    for TICKER in TICKERS:
        print(f"\n--- PROCESSING {TICKER} ---")
        try:
            print(f"1. Getting CIK...")
            cik = get_cik(TICKER)
            print(f"2. Fetching SEC data...")
            raw_data = get_data(cik)
            print("3. Parsing Statements...")   
            df_rawdata = parse_statement(raw_data, MASTER_MAP)
            
            print("4. Checking for Stock Splits...")
            df_rawdata = stocksplit_check(df_rawdata, TICKER) 
            
            print("5. Calculating Ratios...")
            df_ratios = make_calculations(df_rawdata)
            df_final_scaled, suffix_msg = scale_data(df_ratios)

            final_columns = [
                'Net Sales / Revenue', 'Net Income', 'Cash Flow from Operations', 'Total Assets',
                'Earnings Per Share (Diluted)', 'Gross Profit Margin', 'Operating Margin',
                'Return on Sales (ROS)', 'Return on Assets (ROA)', 'Return on Equity (ROE)',
                'Dividend Payout Ratio', 'Current Ratio', 'Debt-to-Equity Ratio',
                'Asset Turnover', 'Average Collection Period (Days Sales Outstanding)'
            ]

            df_final = df_final_scaled[final_columns]
            filename = os.path.join(folder_name, f"{TICKER}_KeyRatios({suffix_msg})({AMT_YEARS}Y).xlsx")
            writer = pd.ExcelWriter(filename, engine='openpyxl')
            df_final.to_excel(writer, sheet_name='Key Ratios')
            writer.close()
            print(f"Success! Saved: {filename}")

        except Exception as e:
            print(f"SKIP - Fatal Error for {TICKER}: {e}")
            continue