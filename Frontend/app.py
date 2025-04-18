# frontend/app.py
import os
import streamlit as st
import requests

API_URL = os.getenv("API_URL", "http://api:8000")

st.set_page_config(page_title="AI Refactorer", layout="wide")
st.title("🔧 AI Code Refactorer")

code = st.text_area("Paste your Python code here", height=300)
filename = st.text_input("Filename (for saving)", "snippet.py")

if st.button("🚀 Refactor"):
    if not code.strip():
        st.warning("Please paste some code first!")
    else:
        with st.spinner("Running agents…"):
            resp = requests.post(
                f"{API_URL}/refactor",
                json={"code": code, "filename": filename},
                timeout=120
            )
        if resp.status_code != 200:
            st.error(f"Error: {resp.text}")
        else:
            data = resp.json()
            st.success("Done! Session: " + data["session"])

            st.subheader("1️⃣ Summary")
            st.code(data.get("task1","<no summary>"))

            st.subheader("2️⃣ Issues Found")
            st.text(data.get("task2","<no issues>"))

            st.subheader("3️⃣ Improvement Plan")
            st.text(data.get("task3","<no plan>"))

            st.subheader("4️⃣ Refactored Code")
            st.code(data.get("task4","<no code>"), language="diff")

            st.subheader("📜 Agent Logs")
            st.text_area("Logs", data.get("logs",""), height=200)
