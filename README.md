*** PROJECT NAME: ***

    KeyRatiosCalculator

*** SUMMARY: ***

This project scrapes the Securities and Exchange Commission (SEC) website for a company’s financial data, then uses that information to create an Excel spreadsheet of financial ratios.

*** OUTLINE: ***

The project includes various functions that ensure data accuracy, validation, and formatting. Using data from a company’s 10-K reports found on the SEC & EDGAR website, it turns this messy data into a clean and concise Excel spreadsheet. The user specifies a ticker symbol (ex. AAPL) and a timeframe in years for which the program will acquire data and calculate the ratios. Using the user input, the program does the following:

1. Gets the CIK number (10-digit unique identifier the SEC uses) for the stock from the SEC website
2. Uses the CIK number to scrape a .JSON file from the SEC website
3. Parses the .JSON file into a DataFrame
4. Checks for stock splits to clarify historical Earnings Per Share (EPS) data
5. Calculates the financial ratios that are outlined in the program
6. Makes a new Excel file that includes the key data points as well as the ratios
7. Saves that file to a new folder called “Financial_Reports” or a name of your choice

*** USER INSTRUCTIONS: ***

Steps for proper usage:

1. Run the file through a code editor or your command prompt
2. Fill out the prompts as they appear EXACTLY as prompted (This is especially
important when filling out the list of tickers that you want to analyze)
3. OPTIONAL: Input stock split data. A robust stock split checker is already included in the code.
4. If you are given a “Success!”, then the ratios will be saved to the folder you specified or a new one that it created.
5. OPTIONAL: Download and run the attached Microsoft Excel script to format your data for readability.

*** Possible Error Notes: ***

403 Forbidden error:
    Locate the HEADERS variable and change it to your email address so that it appears as follows:
    
	HEADERS = {'User-Agent': 'ValidUser/1.0 (youremail@example.com)'}

inf values: 

Indicates a division by zero error (e.g., zero debt). This is preserved to show missing underlying data. If this variable appears under one of the ratios in your spreadsheet, then you should calculate the given ratio for that year/ticker based on the actual SEC filing. Add a Bug Fix comment to this page as seen in the README.

Ratio Values of “0”:
	
Indicates the numerator was zero in the SEC filing. If this occurs in one value of one column, I recommend verifying the ratio through the actual SEC filing. 

If a full column of ratios appears as “0”:
    
1. The data is correct. This is common with the Average Collection Period because certain companies (such as Financial Companies) do not hold any Accounts Receivable balance.
2. There is a bug (verify through the SEC filing), make a Bug Fix comment

EPS Dropoff / Missed Stock Splits:

Indicates that you have neglected to add or incorrectly added a stock split to the data. 

1. Ensure that you have added ALL of the stock splits that a company has gone through over your desired period of time.
2. Input the splits manually, as shown in personalization
3. There is a bug (verify through the SEC filing), make a Bug Fix comment

*** PERSONALIZATION: ***

If you wish to input the variables through a code editor, then you can edit the following variables in the following lines:

Tickers: 

1. Remove the ticker user prompt present before the TICKERS variable
2. Locate and edit the TICKERS variable by filling in your variables as shown in the comment below it

Years:

1. Remove the year user prompt present before the AMT_YEARS variable
2. Locate and edit the AMT_YEARS variable by filling in your variables as shown in the comment below it

Stock Splits:

1. Remove the stock splits user prompt present before and after the MANUAL_SPITS variable
2. Locate and edit the MANUAL_SPLITS variable by filling in your variables as shown in the comment below it

*** BUG FIXES / CONTRIBUTIONS ***

If you encounter a bug or wish to add to the program, please comment with the following information:

*** For Bug Fixes: ***

    Ticker (the ticker where the bug was encountered)
    Optional: Line/Function (a line or function where the bug could be)
    Detailed Explanation of the Problem (Does the information not match the SEC website? Did the program fail to run on a specific ticker symbol?)
    
*** For Additions: ***

    Code (proposed lines to add or remove)
    Line (where you want to add the code in the program)
    Why (What improvement does this make to the program? How much will the edit improve the user experience?)
