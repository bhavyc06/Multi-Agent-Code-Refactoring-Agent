import requests, json, os
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
from pydantic import BaseModel

# === MCP helper ===
class MCPClient:
    def __init__(self, base):
        self.base = base.rstrip('/')
    def call(self, tool, payload):
        resp = requests.post(f"{self.base}/{tool}", json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

# MCP endpoints
FS  = MCPClient("http://mcp_fs:3901")
SH  = MCPClient("http://mcp_shell:3902")
SEC = MCPClient("http://mcp_semgrep:3903")

# === Local LLM via Ollama ===
LLM_ENDPOINT = os.environ.get("OLLAMA_URL", "http://ollama:11434")
LOCAL_MODEL = "codellama:7b-instruct-q4_0"
local_llm = LLM(
    model=LOCAL_MODEL,
    base_url=LLM_ENDPOINT,
    api_key="ollama"  # dummy, not used by Ollama
)

# === Utility wrappers exposed to agents ===
def read_file(path: str) -> str:
    return FS.call("read_file", {"path": path})

def write_file(path: str, content: str) -> str:
    return FS.call("write_file", {"path": path, "content": content})

def run_command(cmd: str) -> str:
    return SH.call("execute_command", {"command": cmd})

def semgrep_scan(path=".") -> str:
    return SEC.call("scan_code", {"path": path})

# Register wrappers as CrewAI Tools
from crewai_tools import tool

@tool(read_file)
def fs_read_file(path: str) -> str: ...

@tool(write_file)
def fs_write_file(path: str, content: str) -> str: ...

@tool(run_command)
def shell_exec(cmd: str) -> str: ...

@tool(semgrep_scan)
def sec_scan(path="."): ...

# === Agents ===
summarizer = Agent(
    role="Code Summarizer",
    goal="Understand the provided code and summarize its behaviour and structure.",
    backstory="A meticulous software archeologist.",
    tools=[fs_read_file],
    llm=local_llm,
    verbose=True,
)

analyzer = Agent(
    role="Vulnerability & Logic Analyzer",
    goal="Identify vulnerabilities and logic errors via static and dynamic analysis.",
    backstory="A security‑minded QA specialist.",
    tools=[fs_read_file, shell_exec, sec_scan],
    llm=local_llm,
    verbose=True,
)

strategist = Agent(
    role="Improvement Strategist",
    goal="Suggest concrete improvements based on identified issues.",
    backstory="A senior software architect.",
    llm=local_llm,
    verbose=True,
)

rewriter = Agent(
    role="Code Rewriter",
    goal="Apply improvements and output revised, working code.",
    backstory="A diligent refactoring bot.",
    tools=[fs_read_file, fs_write_file, shell_exec, sec_scan],
    llm=local_llm,
    verbose=True,
)

# === Crew builder ===
def build_crew(code_path: str):
    task1 = Task(
        description=(
            "Read the code at {code_path} and provide a concise summary "
            "of its purpose and structure."),
        expected_output="Summary text.",
        agent=summarizer,
    )
    task2 = Task(
        description=(
            "Using static scan and tests, list security issues or logic bugs in the code."),
        expected_output="List of issues with line numbers.",
        agent=analyzer,
    )
    task3 = Task(
        description="Propose changes to fix all reported issues.",
        expected_output="Improvement plan.",
        agent=strategist,
    )
    task4 = Task(
        description=(
            "Implement the improvements and overwrite the original file at {code_path}. "
            "Run tests afterwards to ensure success."),
        expected_output="Refactored code (diff).",
        agent=rewriter,
    )

    return Crew(
        agents=[summarizer, analyzer, strategist, rewriter],
        tasks=[task1, task2, task3, task4],
        process=Process.sequential,
        verbose=2,
        metadata={"code_path": code_path},  # auto‑format tasks
    )
