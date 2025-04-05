import pandas as pd
from crewai.tools import tool

@tool("query_mapping")
def query_mapping(mdf_number: str):
    """
    This function takes a rebate name as input and returns the corresponding row(s) from an Excel file containing rebate mappings.

    Parameters:
    mdf_number (str): The name of the rebate to search for in the Excel file.

    Returns:
    Markdown Table (str): A markdown Table containing the row(s) from the Excel file where the 'Rebates' column matches the provided rebate name (case-insensitive).
    """
    
    file_path = "docs/rebates/mapping.xlsx"
    df = pd.read_excel(file_path, engine='openpyxl')
    
    # Convert 'MDF Number' column to strings to better match the number
    df['MDF Number'] = df['MDF Number'].astype(str)
        
    result = df[df['MDF Number'].apply(lambda x: mdf_number in x)]
    
    return result.to_markdown(index=False) # Convert Data Frame to Markdown for the Agent understand better

@tool("query_net_receipts")
def query_net_receipts(rebate_category: str, date_month: str):
    """
    This function takes a rebate category and a month as input and returns the corresponding row(s) from an Excel file containing net receipts data.

    Parameters:
    rebate_category (str): The category of the rebate to search for in the Excel file.
    date_month (str): The month to filter the data by. Month should not be an abbreviation, it must be the complete month name.

    Returns:
    Markdown Table (str): A markdown Table containing the row(s) from the Excel file where the 'Month' column matches the provided date_month (case-insensitive) and includes only the 'Month' and specified rebate_category columns.
    """
    file_path = "docs/rebates/net_receipts.xlsx"
    df = pd.read_excel(file_path, engine='openpyxl') 
    
    # Filter the DataFrame by the given rebate category and month
    result = df[df["Month"].str.lower() == date_month.lower()][["Month", rebate_category]]
    return result.to_markdown(index=False) # Convert Data Frame to Markdown for the Agent understand better

@tool("calculate_rebate_value")
def calculate_rebate_value(net_receipt_category_value, invoice_percentage):
    """
    This function calculates (invoice_percentage * net_receipt_category_value) the rebate value based on the given percentage value and net receipts.

    Parameters:
    net_receipt_category_value (float): The net receipt value for the Category.
    invoice_percentage (float): The percentage value to be used in the calculation, don't adapt the value
    
    Returns:
    Float: Return Rebate Value.
    """
    
    value = float(net_receipt_category_value)
    percentage =  float(invoice_percentage)
    return percentage * value

@tool("validate_rebate_value")
def validate_rebate_value(rebate_value, invoice_total_value):
    """
    Validates if the rebate value is within an acceptable range compared to the total invoice value.

    Parameters:
    rebate_value (float): The calculated rebate amount.
    invoice_total_value (float): The total invoice amount.

    Returns:
    str: "Valid" if rebate_value is reasonable, otherwise "Invalid".
    """
    if not isinstance(rebate_value, (int, float)) or not isinstance(invoice_total_value, (int, float)):
        return "Invalid: Input values must be numeric."

    if 0 <= rebate_value <= invoice_total_value * 0.5:  # Example threshold (50% of total invoice)
        return "Valid"
    else:
        return "Invalid"

@tool("query_snowflake")
def query_snowflake(asin: str):
    """
    This function retrieves the EAN code associated with a given ASIN from the Snowflake Excel file.
    The column name in the Snowflake Excel file for EAN is "EAN_UPC".

    Parameters:
    asin (str): The ASIN number to look up.

    Returns:
    str: The EAN code found in the Excel file or an appropriate message.
    """
    file_path = "docs/events/snowflake.xlsx"

    try:
        # Load the Excel file safely
        df = pd.read_excel(file_path, engine='openpyxl')

        # Debug: Print column names to check if "EAN_UPC" exists
        print("Columns in Snowflake file:", df.columns.tolist())

        # Ensure the expected columns exist
        required_columns = {"ASIN", "EAN_UPC"}  # Ensure these exist
        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            return f"❌ Missing columns in Snowflake file: {', '.join(missing_columns)}"

        # Drop rows where ASIN is NaN to avoid .str.lower() errors
        df = df.dropna(subset=['ASIN'])

        # Perform case-insensitive lookup
        result = df[df['ASIN'].str.lower() == asin.lower()]

        if not result.empty:
            return str(result.iloc[0]['EAN_UPC'])  # Convert to string for consistency
        else:
            return f"⚠️ No EAN found for ASIN: {asin}"

    except FileNotFoundError:
        return "❌ Error: Snowflake Excel file not found."
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"


@tool("query_tipps")
def query_tipps(ean: str):
    """
    Retrieves the promo discount associated with a given EAN from the TIPPS Excel file.
    """

    file_path = "docs/events/tipps.xlsx"

    try:
        # Load the Excel file safely
        df = pd.read_excel(file_path, engine='openpyxl')

        # Ensure required columns exist
        required_columns = {"Consumer Unit EAN/UPC Code", "PROMO DISCOUNT £"}
        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            return f"❌ Missing columns in TIPPS file: {', '.join(missing_columns)}"

        # Normalize the EAN column:
        df['Consumer Unit EAN/UPC Code'] = (
            df['Consumer Unit EAN/UPC Code']
            .astype(str)   # Convert to string
            .str.strip()   # Remove extra spaces
            .str.replace(r'\.0$', '', regex=True)  # Remove .0 if it exists
        )

        # Normalize the input EAN
        ean = str(ean).strip()

        # Perform exact match
        result = df[df['Consumer Unit EAN/UPC Code'] == ean]

        if not result.empty:
            # Take the first valid promo discount
            promo_discount = result.iloc[0]['PROMO DISCOUNT £']

            # Handle NaN values
            if pd.isna(promo_discount):
                print(f"Promo discount is missing (NaN) for EAN {ean}")
                return "Missing Promo Discount"

            promo_discount = float(promo_discount)  # Convert to float for consistency
            return promo_discount

        else:
            return f"No promo discount found for EAN: {ean}"

    except FileNotFoundError:
        return "Error: TIPPS Excel file not found."
    except Exception as e:
        return f"Unexpected error: {str(e)}"

    
@tool("query_mapping_events")
def query_mapping_events(invoice_data):
    """
    Extracts MDF number from the invoice data and retrieves
    the corresponding Event Description and Event ID from the mapping file.
    
    Args:
        invoice_data (dict): A dictionary containing invoice details,
                             including the MDF number.
    
    Returns:
        dict: A dictionary containing the MDF number, Event Description,
              and Event ID, or an error message if the MDF number is not found.
    """
    # Extract MDF number from invoice data
    mdf_number = invoice_data.get('mdf_number')
    
    if not mdf_number:
        return {"error": "MDF number not found in invoice data."}

    # Load the mapping file
    mapping_file_path = 'docs/events/mapping_events.xlsx'
    try:
        mapping_df = pd.read_excel(mapping_file_path)
    except Exception as e:
        return {"error": f"Failed to read mapping file: {str(e)}"}

    # Search for the MDF number in the mapping DataFrame
    event_info = mapping_df.loc[mapping_df['Agreement ID'] == mdf_number]

    if event_info.empty:
        return {"error": f"No mapping found for MDF number: {mdf_number}"}

    # Assuming the columns in the mapping file are named 'Event Description' and 'Event ID'
    return {
        "mdf_number": mdf_number,
        "event_description": event_info['Event Description'].values[0],
        "event_id": event_info['Event ID'].values[0]
    }