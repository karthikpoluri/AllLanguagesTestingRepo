##confidence score

# Confidence Score Generation Prompt Template
confidence_score_prompt = """
You are an objective scoring system for evaluating AI-extracted document analysis.

INPUT:
- SOW Document: {SOW_DOCUMENT}
- Original Extraction Prompt: {ORIGINAL_PROMPT}
- Generated Output: {GENERATED_OUTPUT}

SCORING METHODOLOGY:
- Total Score Range: 0-100 points
- Decimal precision: 1 decimal place

SCORING CRITERIA:
1. Content Relevance (25 points)
   - Exact match to SOW section: 0-10 points
   - Comprehensive coverage: 0-10 points
   - Contextual alignment: 0-5 points

2. Information Accuracy (25 points)
   - Factual precision: 0-10 points 
   - No misinterpretations: 0-10 points
   - Technical correctness: 0-5 points

3. Comprehensiveness (20 points)
   - Critical elements inclusion: 0-10 points
   - Depth of information: 0-6 points
   - Logical structure: 0-4 points

4. Language Clarity (15 points)
   - Professional terminology: 0-5 points
   - Grammatical quality: 0-5 points
   - Readability: 0-5 points

5. Contextual Understanding (15 points)
   - Industry-specific nuances: 0-6 points
   - Implied meaning capture: 0-5 points
   - Strategic insights: 0-4 points

Provide a JSON response:
{{
    "total_score": [calculated score],
    "category_breakdown": {{
        "content_relevance": [subscore],
        "information_accuracy": [subscore],
        "comprehensiveness": [subscore],
        "language_clarity": [subscore],
        "contextual_understanding": [subscore]
    }},
    "confidence_level": "[Low/Medium/High]",
    "key_observations": "[Brief insights]"
}}
"""

# Initialize Azure OpenAI LLM
llm = AzureChatOpenAI(
    temperature=0,
    model_name="gpt-4o",
    azure_deployment="gpt-4o",
    model_kwargs={"seed": 1},
    openai_api_version="2024-08-01-preview",
    openai_api_type="azure",
    openai_api_key=os.getenv("OPENAI_KEY"),
    azure_endpoint=os.getenv("OPENAI_BASE")
)

# Function to read content from PDF
def read_pdf_content(file_path):
    pdf_reader = PdfReader(file_path)
    pages = [f"Page {i+1}:\n{page.extract_text().strip()}\n" for i, page in enumerate(pdf_reader.pages) if page.extract_text()]
    return "\n".join(pages)

def generate_confidence_score(sow_content, original_prompt, generated_output, seed=1):
    confidence_prompt = ChatPromptTemplate.from_template(confidence_score_prompt + f" Seed: {seed}")
    chain = confidence_prompt | llm
    return chain.invoke({"SOW_DOCUMENT": sow_content, "ORIGINAL_PROMPT": original_prompt, "GENERATED_OUTPUT": generated_output}).content

# Function to format confidence score output
def format_confidence_score(confidence_data):
    return f"""
Total Score: {confidence_data['total_score']} / 100

Category Breakdown:
• Content Relevance: {confidence_data['category_breakdown']['content_relevance']} / 25
• Information Accuracy: {confidence_data['category_breakdown']['information_accuracy']} / 25
• Comprehensiveness: {confidence_data['category_breakdown']['comprehensiveness']} / 20
• Language Clarity: {confidence_data['category_breakdown']['language_clarity']} / 15
• Contextual Understanding: {confidence_data['category_breakdown']['contextual_understanding']} / 15

Confidence Level: {confidence_data['confidence_level']}

Key Observations:
{confidence_data['key_observations']}
"""