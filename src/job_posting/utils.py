import re
import streamlit as st
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