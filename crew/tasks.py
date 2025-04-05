from crewai import Task
from textwrap import dedent

def amazon_invoice_matching_rebate(agent):
    return Task(
        description=dedent(
            """
            Your task is to Analyze invoice document to calculate and validate rebate values. 
            
            ### Invoice Document
            {invoice}
            
            ### Task Details:
            - Scope:
                - Extract key information from Invoice Document including percentages, totals, and dates
                - Map invoice data to rebate categories using MDF numbers
                - Calculate expected rebate values using net receipts data
                - Validate invoice amounts against calculated rebate values

            - Tools to Use:
                - query_mapping: For finding rebate categories
                - query_net_receipts: For retrieving net receipt values
                - calculate_rebate_value: For computing rebate amounts
                
            ### Required Steps:
            1. *Invoice Analysis*:
                - Identify percentage value under the "line description" column of the table of the Invoice Document.
                - Extract Month, and MDF number
                - Extract Invoice Total below the column Invoice Total in the document
                - Locate invoice number from the Invoice Document

            2. *Rebate Mapping* (use tool query_mapping):
                - Use MDF number to find corresponding Rebate Name (Column A) on column name Rebates
                - Identify category on the Column name Category from mapping (Column C)

            3. *Data Retrieval* (use query_net_receipts and calculate_rebate_value):
                - Get net receipt value using Category and Invoice Month
                - Calculate rebate value (Percentage * Net Receipt), don't change the percentage found in the Invoice Document

            4. *Validation*:
                - Compare calculated rebate value with invoice total
                - Determine match status (Fully/Partially/Not Matched)

            5. *Reporting*:
                - Compile all extracted values
                - Format final output with validation status
            """
        ),
        expected_output="""
            A structured report containing:
            - Invoice metadata (number, total, month)
            - MDF reference information
            - Rebate calculation details
            - Validation status assessment

            *Required Format*:
            json
           
            invoice_number: Extracted invoice number from Invoice Document,
            mdf_number: MDF reference from document from Invoice Document,
            invoice_total: Total amount from invoice from Invoice Document,
            invoice_month: Month from net receipts period write the name of the month from Invoice Document,
            rebate_name: Mapped rebate name from sheet from Mapping,
            category: Category from mapping data from Mapping,
            rebate_value: Calculated rebate amount from tool calculate_rebate_value,
            match_status: Fully/Partially/Not Matched
            
        """,
        agent=agent
    )

def amazon_invoice_matching_event(agent):
    return Task(
        description=dedent(
            """
            Your task is to analyze events invoice document to create a structured report based on ASINs, EAN codes, and promo discounts.

            ### Invoice Document
            {invoice}

            ### Task Details:
            - Scope:
                - Extract ASIN numbers, rebate per unit, and line totals from the Invoice Document.
                - Lookup EAN codes for ASINs in snowflake.
                - Lookup promo discounts for EAN codes in tipps.
                - Compare rebate per unit with promo discount and determine match status.
                - Extract MDF number from the invoice and search for its corresponding Event Description and Event ID in mapping.

            - Tools to Use:
                - query_snowflake: For finding EAN codes based on ASINs
                - query_tipps: For retrieving promo discounts based on EAN codes
                - query_mapping_events: For finding Event Description and Event ID based on Agreement ID

            ### Required Steps:
            1. *Invoice Analysis*:
                - Identify ASIN numbers, rebate per unit, and line totals from the invoice.
                - Create a table with three columns: ASIN, Rebate Per Unit, Line Total.

            2. *EAN Lookup* (use tool query_snowflake):
                - For each ASIN, find the corresponding EAN and add a new column to the table.

            3. *Promo Discount Lookup* (use tool query_tipps):
                - For each EAN, find the corresponding tipps promo discount and add this as a new column.

            4. *Comparison*:
                - Compare values in the Rebate Per Unit column to the Promo Discount column.
                - Add a new column called Result: output "matched" if they are equal, "not matched" otherwise.

            5. *Agreement ID Extraction*:
                - Extract the MDF number from the invoice.
                - Search for it in the mapping.
                - If a match is found, retrieve the corresponding Event Description and Event ID.

            ### Expected Output:
            A structured report containing:
            - ASIN, Rebate Per Unit, Line Total, EAN, Promo Discount, Result
            - Agreement ID, Event Description, Event ID

            *Required Format*:
            json

            - invoice_data: A list of dictionaries containing:
              - asin: ASIN number,
              - rebate_per_unit: Rebate per unit amount,
              - line_total: Total amount for the line,
              - ean: Corresponding EAN code,
              - promo_discount: Promo discount amount,
              - result: "matched" or "not matched"
            - agreement_id: Extracted MDF number as Agreement ID,
            - event_description: Corresponding Event Description from mapping,
            - event_id: Corresponding Event ID from mapping
            """
        ),
        expected_output="""
            A structured report containing:
            - invoice_data: List of dictionaries with ASIN, Rebate Per Unit, Line Total, EAN, Promo Discount, Result
            - agreement_id: MDF number from invoice,
            - event_description: Event Description from mapping,
            - event_id: Event ID from mapping

            *Required Format*:
            json
        """,
        agent=agent
    )