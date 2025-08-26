from crewai import Agent, Task, Crew, Process
from dotenv import load_dotenv
load_dotenv()


# Create an agent with code execution enabled
analysis_agent = Agent(
    role="mathematician",
    goal="Analyze data and provide insights.",
    backstory="You are an experienced mathematician with experience in statistics.",
    verbose=True
)

# Create a task that requires code execution
data_analysis_task = Task(
    description="Analyze the given dataset and calculate the average age of participants. Ages: {ages}",
    agent=analysis_agent,
    expected_output="Provide the dataset first and thent the the average age of the participants."
)


# Create a crew and add the task
analysis_crew = Crew(
    agents=[analysis_agent],
    tasks=[data_analysis_task]
)

# List of datasets to analyze
datasets = [
  { "ages": [25, 30, 35, 40, 45] },
  { "ages": [20, 25, 30, 35, 40] },
  { "ages": [30, 35, 40, 45, 50] }
]




if __name__ == "__main__":
    # Execute the crew for each dataset and print the results
    # result = analysis_crew.kickoff_for_each(inputs=datasets)
    result_1 = analysis_crew.kickoff_async(inputs={"ages": [25, 30, 35, 40, 45]})
    print("----MAIN THREAD CONTINUES----")