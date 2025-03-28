import fitz  # PyMuPDF
from groq import Groq
from typing import Tuple
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
import base64
import re

class FinancialAnalyzer:
    def __init__(self, api_key: str):
        """Initialize with Groq API key"""
        self.client = Groq(api_key=api_key)
        self.model_name = "llama3-70b-8192"  # Groq's fastest model
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        doc = fitz.open(pdf_path)
        return "".join(page.get_text("text") for page in doc)
    
    def _generate_with_groq(self, prompt: str) -> str:
        """Helper method for Groq API calls"""
        try:
            completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
                temperature=0.3  # More deterministic output
            )
            return completion.choices[0].message.content
        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")

    def analyze_financials(self, company: str, report_text: str) -> Tuple[str, str, str]:
        """Analyze financials using Groq"""
        # Truncate very long documents to fit context window
        truncated_text = report_text[:15000]  # Groq's context limit
        
        # Technical analysis prompt
        tech_prompt = f"""Analyze these financial statements for {company}:
        {truncated_text}
        
        Provide:
        1. Key financial indicators
        2. Red flags and concerning trends
        3. Technical summary in bullet points"""
        
        # Layman's story prompt
        story_prompt = f"""Convert this financial analysis into simple story:
        {self._generate_with_groq(tech_prompt)}
        
        Requirements:
        - Compare projected vs actual performance
        - Use simple analogies (no jargon)
        - Structure as a narrative story"""
        
        # Conclusion prompt
        conclusion_prompt = f"""Based on this analysis:
        {self._generate_with_groq(story_prompt)}
        
        Provide:
        1. Clear conclusion on truthfulness
        2. Investment recommendation
        3. Key supporting factors"""
        
        return (
            self._generate_with_groq(tech_prompt),
            self._generate_with_groq(story_prompt),
            self._generate_with_groq(conclusion_prompt)
        )

    def generate_educational_explanation(self, term: str) -> str:
        """Explain financial terms simply"""
        prompt = f"""Explain '{term}' in simple terms:
        - Use everyday analogies
        - Max 3 sentences
        - No technical jargon
        - Explain why it matters"""
        return self._generate_with_groq(prompt)

    def _extract_financial_data(self, text: str) -> dict:
        """Helper to extract numerical data from text"""
        data = {}
        # Extract key metrics using regex
        patterns = {
            'revenue': r"Revenue.*?(\d[\d,\.]+)",
            'profit': r"Net Profit.*?(\d[\d,\.]+)",
            'assets': r"Total Assets.*?(\d[\d,\.]+)",
            'growth': r"Growth Rate.*?(\d[\d,\.]+)%"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data[key] = float(match.group(1).replace(',', ''))
        return data

    def generate_visualizations(self, analysis_text: str) -> dict:
        """Generate base64 encoded chart images"""
        data = self._extract_financial_data(analysis_text)
        if not data:
            return None
            
        visuals = {}
        df = pd.DataFrame(list(data.items()), columns=['Metric', 'Value'])
        
        # Revenue vs Profit Chart
        plt.figure(figsize=(10, 5))
        df[df['Metric'].isin(['revenue', 'profit'])].plot(
            kind='bar', 
            x='Metric',
            title='Revenue vs Profit',
            color=['#4CAF50', '#2196F3']
        )
        visuals['revenue_profit'] = self._fig_to_base64()
        
        # Growth Radar Chart
        if 'growth' in data:
            plt.figure(figsize=(8, 8))
            categories = ['Revenue Growth', 'Profit Growth', 'Asset Growth']
            values = [data.get('growth', 0)] * 3
            plt.polar(values, categories)
            visuals['growth'] = self._fig_to_base64()
            
        return visuals
    
    def _fig_to_base64(self) -> str:
        """Convert matplotlib figure to base64"""
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        plt.close()
        return base64.b64encode(buffer.getvalue()).decode('utf-8')