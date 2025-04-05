import os
import PyPDF2
from crewai import Crew, Process, LLM

from crew.agents import agent_business_analyst
from crew.tasks import amazon_invoice_matching_rebate
from crew.tools import query_mapping, query_net_receipts, calculate_rebate_value


from dotenv import load_dotenv
load_dotenv()

class Agent():
    def __init__(self):
        deployment = os.getenv("AZURE_DEPLOYMENT")
        kenvue_endpoint =  os.getenv("AZURE_ENDPOINT")
        api_version = os.getenv("OPENAI_API_VERSION")
        api_key = os.getenv("API_KEY")
    
        self.llm = LLM(
            model=f"azure/{deployment}",
            base_url=f"{kenvue_endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}",
            api_key=api_key
        )
      
    def run(self, inputs):
        senior_business_analyst = agent_business_analyst(self.llm, [query_mapping, query_net_receipts, calculate_rebate_value])
        task_amazon_invoice_matching_rebate = amazon_invoice_matching_rebate(senior_business_analyst)
        
        crew = Crew(
            agents=[senior_business_analyst],
            tasks=[task_amazon_invoice_matching_rebate],
            process=Process.sequential,
            verbose=True,
            output_log_file="crew.log"
        )
       
        result = crew.kickoff(inputs=inputs)
        return result
     
def disable_crewai_telemetry():
    """
        This is a fix to remove the telemetry validation, it's not necessary as it only 
        send notification to help the CrewAI team to enhance the library performance
    """
    from crewai.telemetry import Telemetry
    def noop(*args, **kwargs):
        pass
    for attr in dir(Telemetry):
        if callable(getattr(Telemetry, attr)) and not attr.startswith("__"):
            setattr(Telemetry, attr, noop)

def extract_pdf(file_path: str):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        
        # Extract text from each page
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()

    return text

if __name__ == '__main__':
    disable_crewai_telemetry()
    agent = Agent()
    
    files = os.listdir("docs/rebates/")
    pdf_files = [file for file in files if file.endswith('.pdf')]
    
    result_list = []
    for pdf_file in pdf_files: 
        invoice = extract_pdf(f"docs/rebates/{pdf_file}")
        result = agent.run({"invoice":f"{invoice}"})
        result_list.append(result.raw)
    
    print("\n\n####### RESULTS #######\n")
    for r in result_list:
        print(r)