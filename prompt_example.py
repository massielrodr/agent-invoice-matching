import os
import PyPDF2
import pandas as pd

from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate

from dotenv import load_dotenv
load_dotenv()

class AmazonInvoiceMatching:
    def __init__(self, azure_deployment, azure_endpoint, api_version, api_key, temperature, max_retries):
        self.llm = AzureChatOpenAI(
            azure_deployment=azure_deployment,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            api_key=api_key,
            temperature=temperature,
            max_retries=max_retries
        )
        
    def __extract_pdf(self, file_path: str):
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            
            # Extract text from each page
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()
        return text

    def __extract_xlsx(self, file_path: str):
        df = pd.read_excel(file_path, engine='openpyxl')
        data = df.to_dict(orient='records')  # Convert the DataFrame to a dictionary
        
        return data
    
    def __invoke_prompt(self, prompt, mapping):
        prompt_template = PromptTemplate.from_template(f"{prompt}")
            
        chain = prompt_template | self.llm
        return chain.invoke(mapping)

    def match(self, invoice_path: str, mapping_path: str, net_receipts_path: str):
        invoice = self.__extract_pdf(file_path=invoice_path)
        mapping = self.__extract_xlsx(file_path=mapping_path)
        net_receipts = self.__extract_xlsx(file_path=net_receipts_path)
        
        # Prompt to the model
        prompt_01 = self.__invoke_prompt(
            prompt = """
                {invoice}
                Look under the "line description" column of the table of the pdf. Does any row under the "Line Description" column contain a percentage? 
                If yes, then output the percentage number.
            """,
            mapping = { "invoice": f"{invoice}" }
        )
        
        prompt_02 = self.__invoke_prompt(
            prompt = """
                {invoice}
                Extract the following: 
                1. Invoice total
                2. The month from the net receipts period.
                3. The MDF number.
            """,
            mapping = { "invoice": f"{invoice}" }
        )
        
        prompt_03 = self.__invoke_prompt(
            prompt = """
                {mapping}
                In the rebate sheet, use the MDF number referenced in {prompt_02} and search for it on column I. 
                On what row do you find a match? What is the corresponding value in column A for that row? Assign this value as the "Rebate Name".
                What is the corresponding value in column C? Assign this value as the Category.
            """,
            mapping = { "mapping": f"{mapping}", "prompt_02": f"{prompt_02}" }
        )
        
        prompt_04 = self.__invoke_prompt(
            prompt = """
                Use the month identified in {prompt_02} and the category identified in {prompt_03} 
                and extract the value from {net_receipts} that is found at the intersection of the corresponding row and column. Assign this value as the "Net Receipt"
            """,
            mapping = { "net_receipts": f"{net_receipts}", "prompt_03": f"{prompt_03}", "prompt_02": f"{prompt_02}" }
        )
        
        prompt_05 = self.__invoke_prompt(
            prompt = """
                {net_receipts}
                Do the following math: 
                X = Y * Z
                "Y" is the percentage value identified in {prompt_01}
                "Z" is the Net Receipt identified in {prompt_04} 
                Calculate X and assign the value of X as "Rebate Value".
                
                Explain your reasoning
            """,
            mapping = { 
                "net_receipts": f"{net_receipts}", 
                "prompt_01": f"{prompt_01}",
                "prompt_04": f"{prompt_04}"
            }
        )
        
        prompt_06 = self.__invoke_prompt(
            prompt = """
                Compare the rebate value from {prompt_05} to the invoice total from {prompt_02}. 
                If the invoice total is lower than the rebate value, then output that the invoice is partially matched. 
                If it's higher, output that the invoice is not matched. If its plus or minus 500 GBP difference, output that it's fully matched.
            """,
            mapping = { 
                "prompt_05": f"{prompt_05}",
                "prompt_02": f"{prompt_02}"
            }
        )
        
        prompt_07 = self.__invoke_prompt(
            prompt = """
                From {invoice} extract the invoice number it's to the right of "Invoice Number", "Numero Fattura" or similar depending on the language of the invoice).
            """,
            mapping = { "invoice": f"{invoice}" }
        )
        
        result = self.__invoke_prompt(
            prompt = """
                List the following values:
                - Invoice number (from {prompt_07})
                - MDF number (from {prompt_01})
                - Invoice total and Invoice month (from {invoice} it's the month from the net receipts period)
                - Rebate name and Category (from {prompt_03})
                - Rebate value (from {prompt_05})
            """,
            mapping = {
                "prompt_07": f"{prompt_07}",
                "prompt_01": f"{prompt_01}",
                "invoice": f"{invoice}",
                "prompt_03": f"{prompt_03}",
                "prompt_05": f"{prompt_05}",
            }
        )
        return result  
        
if __name__ == '__main__':
    amazon_invoice = AmazonInvoiceMatching(
        azure_deployment = os.getenv("AZURE_DEPLOYMENT"),
        azure_endpoint = os.getenv("AZURE_ENDPOINT"),
        api_version = os.getenv("OPENAI_API_VERSION"),
        api_key = os.getenv("API_KEY"),
        temperature = 0,
        max_retries = 3
    )
    
    files = os.listdir("docs/rebates/")
    pdf_files = [file for file in files if file.endswith('.pdf')]
    
    for pdf_file in pdf_files: 
   
        result = amazon_invoice.match(
            invoice_path=f"docs/rebates/{pdf_file}",
            mapping_path="docs/rebates/mapping.xlsx",
            net_receipts_path="docs/rebates/net_receipts.xlsx"
        )
        print(f"##### {pdf_file} #####")
        print(result.content)
        print(f"\n")