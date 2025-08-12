import os
import re
import json
import gradio as gr
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

load_dotenv()

# Check if the API key is set
if os.getenv("OPENAI_API_KEY") is None:
    raise ValueError("OPENAI_API_KEY environment variable not set!")

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

# --- DATA STRUCTURES ---

@dataclass
class JobRequirements:
    """Defines the requirements for different job roles"""
    role: str
    required_skills: List[str]
    optional_skills: List[str]
    experience_levels: Dict[str, str]  # skill -> description
    
# Job configurations
JOB_CONFIGS = {
    "data_scientist": JobRequirements(
        role="Data Scientist",
        required_skills=["python", "machine_learning", "statistics", "sql"],
        optional_skills=["pandas", "numpy", "tensorflow", "pytorch", "r", "tableau"],
        experience_levels={
            "python": "Python programming experience",
            "machine_learning": "Machine Learning algorithms and frameworks",
            "statistics": "Statistical analysis and modeling",
            "sql": "Database querying with SQL",
            "pandas": "Data manipulation with Pandas",
            "numpy": "Numerical computing with NumPy"
        }
    ),
    "software_engineer": JobRequirements(
        role="Software Engineer",
        required_skills=["programming", "algorithms", "system_design"],
        optional_skills=["java", "python", "javascript", "docker", "kubernetes", "aws"],
        experience_levels={
            "programming": "General programming experience",
            "algorithms": "Data structures and algorithms",
            "system_design": "System architecture and design",
            "java": "Java development experience",
            "python": "Python programming experience"
        }
    ),
    "product_manager": JobRequirements(
        role="Product Manager",
        required_skills=["product_strategy", "stakeholder_management", "analytics"],
        optional_skills=["agile", "scrum", "jira", "figma", "sql"],
        experience_levels={
            "product_strategy": "Product strategy and roadmap planning",
            "stakeholder_management": "Managing cross-functional teams",
            "analytics": "Data analysis and metrics interpretation"
        }
    )
}

@dataclass
class UserProfile:
    """Stores user information throughout the conversation"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    current_ctc: Optional[str] = None
    expected_ctc: Optional[str] = None
    total_experience: Optional[str] = None
    current_company: Optional[str] = None
    current_role: Optional[str] = None
    location: Optional[str] = None
    notice_period: Optional[str] = None
    skills_experience: Dict[str, str] = None
    resume_text: Optional[str] = None
    additional_info: Optional[str] = None
    job_role: str = "data_scientist"
    
    def __post_init__(self):
        if self.skills_experience is None:
            self.skills_experience = {}

# --- ENHANCED AGENT DEFINITIONS ---

def create_agents():
    """Creates specialized agents for the job application process"""
    
    conversation_agent = Agent(
        role='Conversation Manager',
        goal='Guide users through a natural, engaging conversation to collect all necessary job application information while maintaining a friendly and professional tone.',
        backstory=(
            "You are an experienced HR professional and conversation expert who knows how to make candidates "
            "feel comfortable while efficiently gathering all necessary information. You understand the importance "
            "of creating a positive first impression and building rapport with potential hires."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    skill_evaluator = Agent(
        role='Technical Skills Evaluator',
        goal='Assess candidate technical skills based on their stated experience and provide intelligent follow-up questions when needed.',
        backstory=(
            "You are a senior technical interviewer with deep expertise across multiple domains. "
            "You can quickly assess a candidate's technical background and ask probing questions "
            "to understand their true skill level. You're known for your fair but thorough evaluations."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    resume_processor = Agent(
        role='Resume Intelligence Specialist',
        goal='Extract, analyze, and cross-reference information from resumes with stated qualifications to identify strengths and potential concerns.',
        backstory=(
            "You are an expert at parsing resumes and extracting meaningful insights. You can spot "
            "inconsistencies, identify key achievements, and understand how a candidate's background "
            "aligns with job requirements. Your analysis helps hiring teams make informed decisions."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    application_synthesizer = Agent(
        role='Application Synthesis Specialist',
        goal='Create comprehensive, well-structured job applications that present candidates in the best possible light while maintaining accuracy.',
        backstory=(
            "You are a master at crafting compelling job applications. You know how to highlight "
            "a candidate's strengths, address potential weaknesses, and present information in a "
            "way that resonates with hiring managers. Your applications have a high success rate."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    return conversation_agent, skill_evaluator, resume_processor, application_synthesizer

# --- CONVERSATION STATE MANAGEMENT ---

class ConversationManager:
    def __init__(self):
        self.reset_state()
    
    def reset_state(self):
        """Resets the conversation state for a new session"""
        self.user_profile = UserProfile()
        self.current_stage = "welcome"
        self.current_skill_index = 0
        self.conversation_history = []
        self.validation_attempts = {}
    
    def is_valid_email(self, email: str) -> bool:
        """Validates email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def is_valid_phone(self, phone: str) -> bool:
        """Validates phone number format"""
        # Remove all non-digit characters
        clean_phone = re.sub(r'\D', '', phone)
        return len(clean_phone) >= 10
    
    def get_next_skill(self) -> Optional[str]:
        """Gets the next skill to ask about"""
        job_config = JOB_CONFIGS[self.user_profile.job_role]
        all_skills = job_config.required_skills + job_config.optional_skills
        
        if self.current_skill_index < len(all_skills):
            return all_skills[self.current_skill_index]
        return None
    
    def is_skill_required(self, skill: str) -> bool:
        """Checks if a skill is required for the current job role"""
        job_config = JOB_CONFIGS[self.user_profile.job_role]
        return skill in job_config.required_skills

# Global conversation manager
conv_manager = ConversationManager()

# --- ENHANCED CONVERSATION FLOW ---

def get_welcome_message() -> str:
    """Returns a personalized welcome message"""
    return (
        "🎯 **Welcome to SmartApply!** 🎯\n\n"
        "I'm your AI-powered job application assistant. I'll help you apply for positions "
        "by having a natural conversation and automatically filling out your application.\n\n"
        "**Available Positions:**\n"
        "• Data Scientist 🔬\n"
        "• Software Engineer 💻\n"
        "• Product Manager 📊\n\n"
        "Which position interests you? (Just type the role name)"
    )

def process_job_selection(message: str) -> tuple[str, str]:
    """Processes job role selection"""
    message_lower = message.lower()
    
    if "data" in message_lower or "scientist" in message_lower:
        conv_manager.user_profile.job_role = "data_scientist"
        role_name = "Data Scientist"
    elif "software" in message_lower or "engineer" in message_lower:
        conv_manager.user_profile.job_role = "software_engineer"
        role_name = "Software Engineer"
    elif "product" in message_lower or "manager" in message_lower:
        conv_manager.user_profile.job_role = "product_manager"
        role_name = "Product Manager"
    else:
        return ("I didn't catch that. Please choose from:\n• Data Scientist\n• Software Engineer\n• Product Manager", "job_selection")
    
    response = (
        f"Excellent choice! I'll help you apply for the **{role_name}** position. 🚀\n\n"
        "Let's start with some basic information. What's your full name?"
    )
    return response, "get_name"

def validate_and_store_field(field_name: str, value: str) -> tuple[str, str, bool]:
    """Validates and stores user input for different fields"""
    if field_name == "email":
        if not conv_manager.is_valid_email(value):
            attempts = conv_manager.validation_attempts.get("email", 0) + 1
            conv_manager.validation_attempts["email"] = attempts
            
            if attempts >= 3:
                return "Let's skip the email validation for now. We'll continue with the application.", "get_phone", True
            return "That doesn't look like a valid email address. Please provide a valid email (e.g., john@example.com):", "get_email", False
        
        conv_manager.user_profile.email = value
        return f"Perfect! 📧 Got your email as {value}.\n\nWhat's your phone number?", "get_phone", True
    
    elif field_name == "phone":
        if not conv_manager.is_valid_phone(value):
            return "Please provide a valid phone number (at least 10 digits):", "get_phone", False
        
        conv_manager.user_profile.phone = value
        return "Great! 📱 Now, what's your current CTC (Cost to Company)? You can mention it in LPA or specific amount.", "get_current_ctc", True
    
    elif field_name == "name":
        if len(value.strip()) < 2:
            return "Please provide your full name:", "get_name", False
        
        conv_manager.user_profile.name = value.strip().title()
        return f"Nice to meet you, {conv_manager.user_profile.name}! 👋\n\nWhat's your email address?", "get_email", True
    
    return "Validation not implemented for this field", field_name, False

def get_skill_question(skill: str) -> str:
    """Generates appropriate question for each skill"""
    job_config = JOB_CONFIGS[conv_manager.user_profile.job_role]
    skill_description = job_config.experience_levels.get(skill, skill.replace("_", " ").title())
    is_required = conv_manager.is_skill_required(skill)
    
    required_text = " (Required)" if is_required else " (Optional)"
    
    questions = {
        "python": f"How many years of experience do you have with Python programming?{required_text}",
        "machine_learning": f"What's your experience level with Machine Learning?{required_text} (years or beginner/intermediate/advanced)",
        "sql": f"How would you rate your SQL experience?{required_text} (years or skill level)",
        "statistics": f"What's your background in Statistics and statistical modeling?{required_text}",
        "programming": f"What's your overall programming experience?{required_text} (years and primary languages)",
        "algorithms": f"How comfortable are you with Data Structures and Algorithms?{required_text}",
        "system_design": f"What's your experience with System Design and Architecture?{required_text}",
        "product_strategy": f"How many years of experience do you have in Product Strategy and Planning?{required_text}",
        "stakeholder_management": f"What's your experience managing stakeholders and cross-functional teams?{required_text}",
        "analytics": f"How comfortable are you with data analysis and metrics interpretation?{required_text}"
    }
    
    return questions.get(skill, f"What's your experience with {skill_description}?{required_text}")

async def chatbot_logic(message, history):
    """Enhanced conversation logic with better flow and validation"""
    global conv_manager
    
    # Handle reset commands
    if message.lower() in ['restart', 'start over', 'reset', 'new application']:
        conv_manager.reset_state()
        yield get_welcome_message()
        conv_manager.current_stage = "job_selection"
        return
    
    # Handle initial greeting
    if conv_manager.current_stage == "welcome" or (not history and message.lower() in ['hi', 'hello', 'hey', 'start']):
        conv_manager.current_stage = "job_selection"
        yield get_welcome_message()
        return
    
    # Job selection
    if conv_manager.current_stage == "job_selection":
        response, next_stage = process_job_selection(message)
        conv_manager.current_stage = next_stage
        yield response
        return
    
    # Basic information collection
    basic_info_stages = {
        "get_name": ("name", "current_ctc"),
        "get_email": ("email", "phone"), 
        "get_phone": ("phone", "current_ctc"),
        "get_current_ctc": ("current_ctc", "expected_ctc"),
        "get_expected_ctc": ("expected_ctc", "total_experience"),
        "get_total_experience": ("total_experience", "current_company"),
        "get_current_company": ("current_company", "current_role"),
        "get_current_role": ("current_role", "location"),
        "get_location": ("location", "notice_period"),
        "get_notice_period": ("notice_period", "skills_assessment")
    }
    
    if conv_manager.current_stage in basic_info_stages:
        field_name, next_stage = basic_info_stages[conv_manager.current_stage]
        
        if field_name in ["name", "email", "phone"]:
            response, new_stage, success = validate_and_store_field(field_name, message)
            conv_manager.current_stage = new_stage
            yield response
            return
        
        # Store other basic information
        setattr(conv_manager.user_profile, field_name, message)
        
        # Generate next question
        next_questions = {
            "current_ctc": "What's your expected CTC?",
            "expected_ctc": "How many years of total work experience do you have?",
            "total_experience": "What's your current company name?",
            "current_company": "What's your current job title/role?",
            "current_role": "Which city/location are you based in?",
            "location": "What's your notice period?",
            "notice_period": f"Perfect! Now let's assess your technical skills for the {JOB_CONFIGS[conv_manager.user_profile.job_role].role} role. 🔧"
        }
        
        conv_manager.current_stage = next_stage
        if next_stage == "skills_assessment":
            yield next_questions[field_name]
            # Start skills assessment
            skill = conv_manager.get_next_skill()
            if skill:
                yield get_skill_question(skill)
        else:
            yield next_questions[field_name]
        return
    
    # Skills assessment
    if conv_manager.current_stage == "skills_assessment":
        current_skill = conv_manager.get_next_skill()
        if current_skill:
            conv_manager.user_profile.skills_experience[current_skill] = message
            conv_manager.current_skill_index += 1
            
            next_skill = conv_manager.get_next_skill()
            if next_skill:
                yield f"Great! Noted your {current_skill.replace('_', ' ')} experience. 📝"
                yield get_skill_question(next_skill)
            else:
                conv_manager.current_stage = "get_resume"
                yield "Excellent! That covers all the technical skills. 🎯"
                yield ("Now, please paste your resume here, or if you don't have it handy, "
                      "just type 'skip' and we'll proceed with the information you've provided.")
        return
    
    # Resume collection
    if conv_manager.current_stage == "get_resume":
        if message.lower() not in ['skip', 'n/a', 'none']:
            conv_manager.user_profile.resume_text = message
        
        conv_manager.current_stage = "additional_info"
        yield ("Thanks! Is there anything else you'd like to add that might be relevant "
              "for this application? (Or type 'done' to proceed)")
        return
    
    # Additional information
    if conv_manager.current_stage == "additional_info":
        if message.lower() not in ['done', 'no', 'nothing', 'skip']:
            conv_manager.user_profile.additional_info = message
        
        conv_manager.current_stage = "processing"
        
        # Process with CrewAI
        try:
            yield "🚀 **Processing your application...**"
            yield "My AI team is now analyzing your profile and creating your job application. This may take a moment..."
            
            result = process_with_crew()
            yield "✅ **Application Complete!**"
            yield str(result)
            yield "\n---\n💡 **Want to apply for another position?** Just type 'restart' to begin a new application!"
        except Exception as e:
            yield f"❌ Sorry, there was an error processing your application: {str(e)}"
            yield "Please try again or contact support."
        
        return
        
        return

def process_with_crew():
    """Enhanced CrewAI processing with better task coordination"""
    conversation_agent, skill_evaluator, resume_processor, application_synthesizer = create_agents()
    
    # Prepare user data
    user_data = asdict(conv_manager.user_profile)
    job_config = JOB_CONFIGS[conv_manager.user_profile.job_role]
    
    # Task 1: Skill Assessment
    skill_assessment_task = Task(
        description=(
            f"Analyze the candidate's technical skills for the {job_config.role} position. "
            f"Required skills: {', '.join(job_config.required_skills)}. "
            f"Optional skills: {', '.join(job_config.optional_skills)}. "
            f"Candidate's stated experience: {json.dumps(user_data['skills_experience'], indent=2)}"
        ),
        expected_output=(
            "A detailed technical assessment including: "
            "1. Skill ratings (1-5 scale) for each mentioned skill "
            "2. Identification of strengths and areas for development "
            "3. Overall technical fit assessment for the role "
            "4. Recommendations for skill development if needed"
        ),
        agent=skill_evaluator
    )
    
    # Task 2: Resume Analysis (if provided)
    resume_analysis_task = Task(
        description=(
            f"Analyze the provided resume and cross-reference with stated qualifications. "
            f"Resume text: {user_data.get('resume_text', 'No resume provided')}. "
            f"Stated experience: {json.dumps(user_data, indent=2)}"
        ),
        expected_output=(
            "Resume analysis including: "
            "1. Key achievements and experiences extracted "
            "2. Consistency check with stated information "
            "3. Notable accomplishments that strengthen the application "
            "4. Any gaps or areas that need clarification"
        ),
        agent=resume_processor
    )
    
    # Task 3: Application Synthesis
    application_synthesis_task = Task(
        description=(
            "Create a comprehensive job application using all gathered information. "
            "Present the candidate in the best possible light while maintaining accuracy."
        ),
        expected_output=(
            "A complete, professionally formatted job application in markdown including: "
            "1. Executive Summary highlighting key strengths "
            "2. All personal and professional details "
            "3. Technical skills assessment summary "
            "4. Experience highlights "
            "5. Application status and next steps "
            "6. Professional presentation that showcases the candidate effectively"
        ),
        agent=application_synthesizer,
        context=[skill_assessment_task, resume_analysis_task]
    )
    
    # Create and run the crew
    crew = Crew(
        agents=[skill_evaluator, resume_processor, application_synthesizer],
        tasks=[skill_assessment_task, resume_analysis_task, application_synthesis_task],
        process=Process.sequential,
        verbose=True
    )
    
    result = crew.kickoff()
    
    # Reset for next user
    conv_manager.reset_state()
    
    return result

# --- ENHANCED GRADIO INTERFACE ---

def create_gradio_interface():
    """Creates an enhanced Gradio interface with better styling"""
    
    # Custom CSS for better appearance
    css = """
    .gradio-container {
        max-width: 1200px !important;
        margin: auto !important;
    }
    .chat-message {
        border-radius: 10px !important;
    }
    .message.user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }
    .message.bot {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
        color: white !important;
    }
    """
    
    # Custom theme
    theme = gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="purple",
        neutral_hue="slate"
    ).set(
        body_background_fill="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        block_background_fill="rgba(255, 255, 255, 0.95)",
        block_border_width="0px",
        block_shadow="0 8px 32px rgba(0, 0, 0, 0.1)",
        button_primary_background_fill="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        button_primary_text_color="white",
    )
    
    # Create the interface
    demo = gr.ChatInterface(
        fn=chatbot_logic,
        title="🚀 SmartApply - AI Job Application Assistant",
        description=(
            "**Revolutionize your job application process!** 🎯\n\n"
            "Our AI assistant will guide you through a conversational application process, "
            "automatically filling out forms and optimizing your profile for the best results.\n\n"
            "✨ **Features:**\n"
            "• Natural conversation flow\n"
            "• Intelligent skill assessment\n"
            "• Resume analysis and optimization\n"
            "• Multiple job role support\n"
            "• Professional application generation"
        ),
        chatbot=gr.Chatbot(
            height=700,
            show_copy_button=True,
            show_share_button=False,
            avatar_images=(
                "https://cdn-icons-png.flaticon.com/512/3135/3135715.png",  # User
                "https://cdn-icons-png.flaticon.com/512/4712/4712027.png"   # Bot
            ),
            bubble_full_width=False,
            render_markdown=True
        ),
        textbox=gr.Textbox(
            placeholder="Type your message here... (e.g., 'hi' to start)",
            container=False,
            scale=7
        ),
        submit_btn="Send 📤",
        theme=theme,
        css=css,
        examples=[
            "Hi, I want to apply for a job",
            "Data Scientist position",
            "Software Engineer role", 
            "Product Manager position",
            "Restart application"
        ],
        cache_examples=False
    )
    
    return demo

# --- MAIN EXECUTION ---

if __name__ == "__main__":
    print("🚀 Starting SmartApply - AI Job Application Assistant")
    print("=" * 50)
    
    # Initialize the interface
    demo = create_gradio_interface()
    
    # Launch with enhanced settings
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,  # Set to True if you want to create a public link
        debug=False,
        show_error=True,
        quiet=False
    )