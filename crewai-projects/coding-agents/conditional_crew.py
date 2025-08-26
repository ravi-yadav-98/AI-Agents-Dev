from crewai import Agent, Task, Crew, Process
from dotenv import load_dotenv
load_dotenv()

from typing import List
from pydantic import BaseModel
from crewai.tasks.conditional_task import ConditionalTask
from crewai.tasks.task_output import TaskOutput
from crewai_tools import SerperDevTool

# Define a function to assess whether the data needs to be augmented
def should_fetch_more_data(output: TaskOutput) -> bool:
    return len(output.pydantic.events) < 8  # Condition to trigger task

# Create agents for different roles
data_collector = Agent(
    role="Data Collector",
    goal="Retrieve event data using Serper tool",
    backstory="You have a knack for finding the most exciting events happening around.",
    verbose=True,
    tools=[SerperDevTool()],
)

data_analyzer = Agent(
    role="Data Analyzer",
    goal="Analyze the collected data",
    backstory="You're known for your analytical skills, making sense of complex datasets.",
    verbose=True,
)

summary_creator = Agent(
    role="Summary Creator",
    goal="Produce a concise summary from the event data",
    backstory="You're a skilled writer, able to summarize information clearly and effectively.",
    verbose=True,
)


class EventsData(BaseModel):
    events: List[str]

# Define the tasks
fetch_task = Task(
    description="Collect event data for New York City using Serper tool",
    expected_output="A list of 8 exciting events happening in NYC this week",
    agent=data_collector,
    output_pydantic=EventsData,
)

verify_data_task = ConditionalTask(
    description="""
        Ensure that sufficient event data has been collected.
        If fewer than 8 events are found, gather more using the Serper tool.
        """,
    expected_output="An updated list of at least 8 events happening in NYC this week",
    condition=should_fetch_more_data,
    agent=data_analyzer,
)

summary_task = Task(
    description="Summarize the collected events data for NYC",
    expected_output="summary_generated",
    agent=summary_creator,
)

# Assemble the crew with the defined agents and tasks
crew = Crew(
    agents=[data_collector, data_analyzer, summary_creator],
    tasks=[fetch_task, verify_data_task, summary_task],
    verbose=True,
    planning=True  # Retain the planning feature
)


if __name__ == "__main__":
    # Execute the tasks with the crew
    result = crew.kickoff()
    print("results", result)