from typing import List
import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import re
from crewai_tools import SerperDevTool, ScrapeWebsiteTool, FileReadTool
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import streamlit as st
from langchain.schema import AgentAction, AgentFinish
load_dotenv()


scrape_tool = ScrapeWebsiteTool()
serper_dev_tool = SerperDevTool(n_results=2)

# Get the directory where this script is located
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, 'job_description_example.md')
file_read_tool = FileReadTool(
    file_path=file_path,
    description='A tool to read the job description example file.'
)

def streamlit_callback(step_output):
    """Callback to print each step in the Streamlit UI with action + observation support"""

    st.markdown("---")

    # Case 1: AgentAction (structured tool call)
    if isinstance(step_output, AgentAction):
        with st.container(border=True):
            st.markdown("### 🔧 Tool Call")
            st.write(f"**Tool:** {step_output.tool}")
            st.write(f"**Tool Input:** {step_output.tool_input}")
            if step_output.log:
                st.write(f"**Log:** {step_output.log}")

    # Case 2: AgentFinish (final output)
    elif isinstance(step_output, AgentFinish):
        with st.container(border=True):
            st.markdown("### ✅ Final Answer")
            st.write(step_output.return_values)

    # Case 3: Legacy style (action, observation) pairs
    elif isinstance(step_output, (list, tuple)):
        for step in step_output:
            if isinstance(step, tuple) and len(step) == 2:
                action, observation = step

                # Action block
                st.markdown("### 🛠️ Action")
                if isinstance(action, dict):
                    st.markdown(f"**Tool:** {action.get('tool', '')}")
                    st.markdown(f"**Tool Input:** `{action.get('tool_input', '')}`")
                    st.markdown(f"**Log:** {action.get('log', '')}")
                    if "Action" in action:
                        st.markdown(f"**Action:** {action['Action']}")
                else:
                    st.markdown(f"**Action:** {str(action)}")

                # Observation block
                st.markdown("### 👀 Observation")
                if isinstance(observation, str):
                    obs_lines = observation.split('\n')
                    for line in obs_lines:
                        if line.startswith('Title: '):
                            st.markdown(f"**Title:** {line[7:]}")
                        elif line.startswith('Link: '):
                            st.markdown(f"**Link:** {line[6:]}")
                        elif line.startswith('Snippet: '):
                            st.markdown(f"**Snippet:** {line[9:]}")
                        else:
                            st.markdown(line)
                else:
                    st.markdown(str(observation))

            else:
                st.write(step)

    # Case 4: Fallback
    else:
        st.write(step_output)


class StreamToExpander:
    def __init__(self, expander):
        self.expander = expander
        self.buffer = []
        self.colors = ['red', 'green', 'blue', 'orange']
        self.color_index = 0

    def write(self, data):
        cleaned_data = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', data)
        box_chars = ['╭', '╮', '╯', '╰', '─', '│', '├', '┤', '┬', '┴', '┼', '║', '═', '╔', '╗', '╚', '╝', '╠', '╣', '╦',
                     '╩', '╬']
        for char in box_chars:
            cleaned_data = cleaned_data.replace(char, '')

        # Clean up excessive whitespace
        cleaned_data = re.sub(r' {3,}', ' ', cleaned_data)
        cleaned_data = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_data)

        if not cleaned_data.strip():
            return
        # Detect tasks for toast notification
        task_match_object = re.search(r'\"task\"\s*:\s*\"(.*?)\"', cleaned_data, re.IGNORECASE)
        task_match_input = re.search(r'task\s*:\s*([^\n]*)', cleaned_data, re.IGNORECASE)
        task_value = None
        if task_match_object:
            task_value = task_match_object.group(1)
        elif task_match_input:
            task_value = task_match_input.group(1).strip()
        if task_value:
            st.toast("🤖 Task: " + task_value)

        # Highlight chain markers
        if "Entering new CrewAgentExecutor chain" in cleaned_data:
            self.color_index = (self.color_index + 1) % len(self.colors)
            cleaned_data = cleaned_data.replace(
                "Entering new CrewAgentExecutor chain",
                f":{self.colors[self.color_index]}[➡️ Entering new CrewAgentExecutor chain]"
            )
        if "Finished chain." in cleaned_data:
            cleaned_data = cleaned_data.replace(
                "Finished chain.",
                f":{self.colors[self.color_index]}[✅ Finished chain.]"
            )

        # Highlight known roles/agents
        role_markers = [
            "Researcher",
            "Reporting Analyst",
            "City Selection Expert",
            "Local Expert at this city",
            "Amazing Travel Concierge"
        ]
        for role in role_markers:
            if role in cleaned_data:
                cleaned_data = cleaned_data.replace(
                    role, f":{self.colors[self.color_index]}[{role}]"
                )

        self.buffer.append(cleaned_data)
        if "\n" in data:
            self.expander.markdown("".join(self.buffer), unsafe_allow_html=True)
            self.buffer = []

    def flush(self):
        """Prevent attribute errors from CrewAI logger"""
        pass



class ResearchRoleRequirements(BaseModel):
    """Research role requirements model"""
    skills: List[str] = Field(...,
                              description="List of recommended skills for the ideal candidate aligned with the company's culture, ongoing projects, and the specific role's requirements.")
    experience: List[str] = Field(...,
                                  description="List of recommended experience for the ideal candidate aligned with the company's culture, ongoing projects, and the specific role's requirements.")
    qualities: List[str] = Field(...,
                                 description="List of recommended qualities for the ideal candidate aligned with the company's culture, ongoing projects, and the specific role's requirements.")


@CrewBase
class JobPostingCrew:
    """JobPosting crew"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def _get_research_tools(self):
        """Get available tools for research agent"""
        tools = []
        if scrape_tool:
            tools.append(scrape_tool)
        if serper_dev_tool:
            tools.append(serper_dev_tool)
        return tools

    def _get_writer_tools(self):
        """Get available tools for writer agent"""
        tools = []
        if scrape_tool:
            tools.append(scrape_tool)
        if serper_dev_tool:
            tools.append(serper_dev_tool)
        if file_read_tool:
            tools.append(file_read_tool)
        return tools

    def _get_review_tools(self):
        """Get available tools for review agent"""
        tools = []
        if scrape_tool:
            tools.append(scrape_tool)
        if serper_dev_tool:
            tools.append(serper_dev_tool)
        if file_read_tool:
            tools.append(file_read_tool)
        return tools

    @agent
    def research_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['research_agent'],
            tools=self._get_research_tools(),
            verbose=True
        )

    @agent
    def writer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['writer_agent'],
            tools=self._get_writer_tools(),
            verbose=True
        )

    @agent
    def review_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['review_agent'],
            tools=self._get_review_tools(),
            verbose=True
        )

    @task
    def research_company_culture_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_company_culture_task'],
            agent=self.research_agent()
        )

    @task
    def research_role_requirements_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_role_requirements_task'],
            agent=self.research_agent(),
            output_json=ResearchRoleRequirements
        )

    @task
    def draft_job_posting_task(self) -> Task:
        return Task(
            config=self.tasks_config['draft_job_posting_task'],
            agent=self.writer_agent()
        )

    @task
    def review_and_edit_job_posting_task(self) -> Task:
        return Task(
            config=self.tasks_config['review_and_edit_job_posting_task'],
            agent=self.review_agent()
        )

    @task
    def industry_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['industry_analysis_task'],
            agent=self.research_agent()
        )

    @crew
    def crew(self) -> Crew:
        """Creates the JobPostingCrew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=False,
        )