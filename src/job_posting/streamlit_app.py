import streamlit as st
import sys
from crew import StreamToExpander, JobPostingCrew
import openlit

def main():
    st.set_page_config(page_icon="📊", layout="wide")

    st.subheader("📑 Create Job Posting with CrewAI", divider="rainbow")

    with st.sidebar:
        st.header("⚙️ Configure Run")
        company_domain = st.text_input("🔍 domain", "careers.wbd.com")
        company_description = st.text_input("Description", "Warner Bros. Discovery is a premier global media and entertainment company, offering audiences the world’s most differentiated and complete portfolio of content, brands and franchises across television, film, sports, news, streaming and gaming. We're home to the world’s best storytellers, creating world-class products for consumers")
        hiring_needs = st.text_input("Hiring Needs", "Production Assistant, for a TV production set in Los Angeles in June 2025")
        specific_benefits = st.text_input("benefits", "Weekly Pay, Employee Meals, healthcare")


        st.info("Fill in details and click **Run Crew**")

        submitted = st.button("🚀 Run Crew")

    if submitted:
        with st.status("🤖 **Agents at work...**", state="running", expanded=True) as status:
            with st.container(height=500, border=False):
                sys.stdout = StreamToExpander(st)

                # Initialize and run crew
                poc = JobPostingCrew()
                result = poc.crew().kickoff(
                    inputs={
                        "company_domain": company_domain,
                        "company_description": company_description,
                        "hiring_needs": hiring_needs,
                        "specific_benefits": specific_benefits,
                    }
                )

            status.update(label="✅ Job Posting Ready", state="complete", expanded=False)

        st.subheader("📘 Final Output", divider="rainbow")
        st.markdown(result)

if __name__ == "__main__":
    openlit.init(otlp_endpoint="http://127.0.0.1:4318")
    main()