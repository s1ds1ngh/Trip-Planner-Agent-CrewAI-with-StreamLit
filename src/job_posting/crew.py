from typing import List
import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool, ScrapeWebsiteTool, FileReadTool
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# Initialize tools
scrape_tool = ScrapeWebsiteTool()
serper_dev_tool = SerperDevTool(n_results=3)

# Get the directory where this script is located
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, 'job_description_example.md')
file_read_tool = FileReadTool(
    file_path=file_path,
    description='A tool to read the job description example file for reference formatting and structure.'
)

class CompanyCultureReport(BaseModel):
    """Company culture research output model"""
    mission_vision: str = Field(..., description="Company mission, vision, and core values")
    culture_highlights: str = Field(..., description="Key culture and work environment highlights")
    recent_achievements: str = Field(..., description="Recent achievements or notable projects")
    benefits_perks: str = Field(..., description="Employee benefits and perks")
    unique_selling_points: str = Field(..., description="Key selling points for attracting candidates")

class RoleRequirements(BaseModel):
    """Role requirements research output model"""
    technical_skills: List[str] = Field(..., description="Essential technical skills required")
    experience_level: str = Field(..., description="Required experience level and background")
    soft_skills: List[str] = Field(..., description="Important soft skills and qualities")
    preferred_qualifications: List[str] = Field(..., description="Nice-to-have qualifications")
    salary_range: str = Field(..., description="Market-based salary range")

@CrewBase
class JobPostingCrew:
    """JobPosting crew for creating professional job descriptions"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def research_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['research_agent'],
            tools=[scrape_tool, serper_dev_tool],
            verbose=True,
            max_iter=3
        )

    @agent
    def writer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['writer_agent'],
            tools=[scrape_tool, serper_dev_tool, file_read_tool],
            verbose=True,
            max_iter=3
        )

    @agent
    def review_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['review_agent'],
            tools=[scrape_tool, serper_dev_tool, file_read_tool],
            verbose=True,
            max_iter=3
        )

    @task
    def research_company_culture_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_company_culture_task'],
            agent=self.research_agent(),
            output_json=CompanyCultureReport
        )

    @task
    def research_role_requirements_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_role_requirements_task'],
            agent=self.research_agent(),
            output_json=RoleRequirements,
            context=[self.research_company_culture_task()]
        )

    @task
    def draft_job_posting_task(self) -> Task:
        return Task(
            config=self.tasks_config['draft_job_posting_task'],
            agent=self.writer_agent(),
            context=[self.research_company_culture_task(), self.research_role_requirements_task()]
        )

    @task
    def review_and_edit_job_posting_task(self) -> Task:
        return Task(
            config=self.tasks_config['review_and_edit_job_posting_task'],
            agent=self.review_agent(),
            context=[self.research_company_culture_task(), self.research_role_requirements_task(), self.draft_job_posting_task()],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the JobPostingCrew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )