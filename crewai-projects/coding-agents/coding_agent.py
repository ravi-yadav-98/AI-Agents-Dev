from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
load_dotenv()
# Create an agent with code execution enabled
coding_agent = Agent(
    role="Python Data Analyst",
    goal="Write and execute Python code to perform calculations",
    backstory="You are an experienced Python developer, skilled at writing efficient code to solve problems.",
    allow_code_execution=True
)

# Define the task with explicit instructions to generate and execute Python code
data_analysis_task = Task(
    description=(
        "Write Python code to calculate the average of the following list of ages: [23, 35, 31, 29, 40]. "
        "Output the result in the format: 'The average age of participants is: <calculated_average_age>'"
    ),
    agent=coding_agent,
    expected_output="The generated code based on the requirments and the average age of participants is: <calculated_average_age>."
)

# Create a crew and add the task
analysis_crew = Crew(
    agents=[coding_agent],
    tasks=[data_analysis_task]
)

if __name__ == "__main__":

    # Execute the crew
    result = analysis_crew.kickoff()

    print(result)
