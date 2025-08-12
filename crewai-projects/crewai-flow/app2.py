import os
import gradio as gr
import json
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

# To use this code, you need to set your OPENAI_API_KEY as an environment variable.
# For example:
# os.environ["OPENAI_API_KEY"] = "your_api_key_here"

# Check if the API key is set
if os.getenv("OPENAI_API_KEY") is None:
    raise ValueError("OPENAI_API_KEY environment variable not set!")

# Initialize the LLM
# You can replace "gpt-4o" with other models like "gpt-3.5-turbo"
llm = ChatOpenAI(model="gpt-4o")

# --- AGENT DEFINITIONS ---

# Agent 1: Conversational Recruiter Agent
# This agent handles the entire conversation with the user to collect information.
conversational_recruiter_agent = Agent(
    role='Conversational Recruiter',
    goal=(
        "To interactively and dynamically chat with a job applicant to collect all necessary information "
        "for a Data Scientist job application. This includes: full name, email, Current CTC, Expected CTC, "
        "years of experience in Python, Machine Learning, Pandas, and SQL, and the resume text. "
        "You must confirm with the user when you believe you have all the information before finishing."
    ),
    backstory=(
        "You are a highly engaging and intelligent AI recruiter. You can carry on a natural conversation, "
        "understand context, and know exactly what information is needed. You are patient and clear in your questioning. "
        "You must collect every single piece of information before considering your job complete."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm,
)

# Agent 2: Skill Assessment Agent (The "Interviewer")
skill_assessment_agent = Agent(
    role='Technical Interviewer',
    goal="Accurately assess a candidate's skills and experience against the specific requirements of a Data Scientist job.",
    backstory=(
        "You are a seasoned Data Scientist with a knack for asking the right questions to gauge a candidate's true abilities. "
        "You are precise, detail-oriented, and your evaluation is highly respected."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# Agent 3: Resume Analysis Agent (The "Screener")
resume_analyzer_agent = Agent(
    role='HR Analyst',
    goal="Efficiently and accurately extract key information from a candidate's resume.",
    backstory=(
        "You are a meticulous analyst with a keen eye for detail. "
        "You can quickly scan a resume and pull out the most relevant information, saving time for the rest of the hiring team."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# Agent 4: Application Filling Agent (The "Administrator")
application_filler_agent = Agent(
    role='Administrative Assistant',
    goal='Accurately and completely fill out the job application form with the information provided by the other agents.',
    backstory=(
        "You are a highly organized and efficient administrative professional. "
        "You pride yourself on your accuracy and attention to detail, ensuring that all paperwork is completed flawlessly."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm
)


# --- TASK DEFINITIONS ---

# Task for the conversational agent
def create_info_collection_task(chat_history):
    return Task(
        description=(
            "Engage in a conversation with a job applicant. Your goal is to collect the following pieces of information:\n"
            "- Full Name\n"
            "- Email Address\n"
            "- Current CTC (Cost to Company)\n"
            "- Expected CTC\n"
            "- Years of Python Experience\n"
            "- Years of Machine Learning Experience\n"
            "- Years of Pandas Experience\n"
            "- Years of SQL Experience\n"
            "- The full text of their resume (if they don't have one, 'N/A' is acceptable).\n\n"
            "Be conversational and ask questions one by one. Do not overwhelm the user. "
            "Here is the current conversation history, use it to decide what question to ask next:\n"
            f"'''{chat_history}'''\n\n"
            "Once you are confident you have ALL the pieces of information, and only then, "
            "output a final JSON object containing all the collected data. The JSON keys must be: "
            "'name', 'email', 'cctc', 'ectc', 'python_exp', 'ml_exp', 'pandas_exp', 'sql_exp', 'resume'.\n"
            "If you do not have all the information yet, continue the conversation by asking the next logical question."
        ),
        expected_output=(
            "If the conversation is ongoing, the next question to ask the user. "
            "If all information is collected, a single JSON object with all the data."
        ),
        agent=conversational_recruiter_agent
    )

# Tasks for the backend processing crew
def create_backend_tasks(user_info):
    """Creates tasks for the backend agents based on the collected user information."""
    skill_assessment_task = Task(
        description=f"Based on the user's provided information, create a concise summary of their skills and experience. User Info: {user_info}",
        expected_output="A summary of the candidate's skills and experience levels in Python, Machine Learning, Pandas, and SQL.",
        agent=skill_assessment_agent
    )

    resume_analysis_task = Task(
        description=f"Analyze the provided resume text to extract key details like work history, education, and listed skills. User Info and Resume: {user_info}",
        expected_output="A structured summary of the candidate's resume, highlighting key qualifications.",
        agent=resume_analyzer_agent
    )

    fill_application_task = Task(
        description="Using the collected information from the skill assessment and resume analysis, fill out a dummy job application.",
        expected_output="A completed, well-formatted dummy job application in Markdown format. Include all collected details: Name, Email, CCTC, ECTC, Skills Assessment, and Resume Summary.",
        agent=application_filler_agent,
        context=[skill_assessment_task, resume_analysis_task]
    )

    return [skill_assessment_task, resume_analysis_task, fill_application_task]

# --- GRADIO UI AND CONVERSATIONAL LOGIC ---

def chatbot_logic(message, history):
    """Manages the conversation flow and triggers the CrewAI crews."""
    
    # Append the new message to the history for context
    history.append([message, ""])
    chat_history_str = "\n".join([f"User: {h[0]}\nAI: {h[1]}" for h in history])

    # Let the conversational agent decide the next step
    info_collection_task = create_info_collection_task(chat_history_str)
    
    communication_crew = Crew(
        agents=[conversational_recruiter_agent],
        tasks=[info_collection_task],
        process=Process.sequential,
        verbose=0 # Keep the UI clean
    )
    
    agent_response = communication_crew.kickoff()

    # Check if the agent returned a JSON object (signaling completion)
    try:
        # The agent might wrap the JSON in text, so we'll try to find it
        json_start = agent_response.find('{')
        json_end = agent_response.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            json_str = agent_response[json_start:json_end]
            collected_data = json.loads(json_str)
            
            # --- TRIGGER THE BACKEND CREW ---
            yield "Thank you! I have all the information I need. My team will now process your application. This may take a moment..."

            backend_tasks = create_backend_tasks(collected_data)
            backend_crew = Crew(
                agents=[skill_assessment_agent, resume_analyzer_agent, application_filler_agent],
                tasks=backend_tasks,
                process=Process.sequential,
                verbose=2
            )
            final_result = backend_crew.kickoff()
            
            yield final_result
            yield "Your application has been processed. You can start a new application by typing 'hi'."
            
        else:
            # It's a regular conversational turn
            yield agent_response
            
    except json.JSONDecodeError:
        # The response was not JSON, so it's part of the ongoing conversation
        yield agent_response


# --- LAUNCH THE GRADIO APP ---
if __name__ == "__main__":
    theme = gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="sky",
    ).set(
        body_background_fill="#f0f4f8",
        block_background_fill="white",
        block_border_width="1px",
        block_shadow="*shadow_drop_lg",
        input_background_fill="#f9fafb",
        input_border_color="#d1d5db",
        input_shadow="*shadow_inset",
        slider_color="#1e88e5",
    )

    demo = gr.ChatInterface(
        fn=chatbot_logic,
        title="🤖 Agentic Job Application Chatbot",
        description="Welcome! This AI-powered chatbot will guide you through the job application process for a Data Scientist role. Start by saying 'hi'.",
        chatbot=gr.Chatbot(
            height=600,
            show_copy_button=True,
            avatar_images=(None, "https://cdn-icons-png.flaticon.com/512/1698/1698535.png"),
            bubble_full_width=False
        ),
        theme=theme,
        examples=[["hi"]],
        cache_examples=False,
    )

    demo.launch()
