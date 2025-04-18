import os, requests
from crewai import Agent, Task, Crew, Process
from crewai_tools import tool
from langchain_community.chat_models import ChatOllama   # langchain‑community ≥0.0.31


# ────────────────────────── MCP helper ──────────────────────────
class MCPClient:
    def __init__(self, base: str):
        self.base = base.rstrip("/")

    def call(self, endpoint: str, payload: dict):
        r = requests.post(f"{self.base}/{endpoint}", json=payload, timeout=60)
        r.raise_for_status()
        return r.json()


FS  = MCPClient("http://mcp_fs:3901")
SH  = MCPClient("http://mcp_shell:3902")
SCN = MCPClient("http://mcp_scan:3903")


# ────────────────────────── Tool wrappers ───────────────────────
@tool
def read_file(path: str) -> str:
    """Read a file from the shared workspace"""
    return FS.call("read", {"path": path})


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file in the workspace"""
    return FS.call("write", {"path": path, "content": content})


@tool
def run_pytest(workdir: str = ".") -> str:
    """Run pytest in *workdir* and return its output"""
    return SH.call("exec", {"command": "pytest -q", "workdir": workdir})


@tool
def bandit_scan(path: str = ".") -> str:
    """Run Bandit security scan"""
    return SCN.call("scan", {"path": path})


# ────────────────────────── Local Ollama model ──────────────────
OLLAMA_HOST = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
local_llm   = ChatOllama(
    model="codellama:7b-instruct-q4_0",
    base_url=OLLAMA_HOST,
    temperature=0.2,
)


# ────────────────────────── Agents ──────────────────────────────
summarizer = Agent(
    role="Code Summarizer",
    backstory="A meticulous software archeologist who explains code succinctly.",
    goal="Summarise behaviour and structure of the supplied code.",
    llm=local_llm,
    tools=[read_file],
    verbose=True,
)

analyzer = Agent(
    role="Bug & Vulnerability Analyzer",
    backstory="A veteran QA/security engineer with an eye for edge‑cases.",
    goal="Discover logic bugs, failing tests and security issues.",
    llm=local_llm,
    tools=[read_file, run_pytest, bandit_scan],
    verbose=True,
)

strategist = Agent(
    role="Improvement Strategist",
    backstory="A senior architect who provides clear, actionable refactor plans.",
    goal="Propose refactorings that resolve all discovered issues.",
    llm=local_llm,
    verbose=True,
)

rewriter = Agent(
    role="Code Rewriter",
    backstory="A disciplined developer who applies fixes and ensures tests pass.",
    goal="Implement the improvements and make sure tests succeed.",
    llm=local_llm,
    tools=[read_file, write_file, run_pytest],
    verbose=True,
)


# ────────────────────────── Crew factory ────────────────────────
def build(code_path: str) -> Crew:
    """Return a Crew ready to work on *code_path*."""
    t1 = Task(
        description=f"Summarise the file at **{code_path}**.",
        expected_output="Concise paragraph summarising purpose and structure.",
        agent=summarizer,
    )

    t2 = Task(
        description="List every bug, failing test or security issue in the code.",
        expected_output="Bullet list with line numbers and severity.",
        agent=analyzer,
    )

    t3 = Task(
        description="Propose precise code changes or refactors to resolve all issues.",
        expected_output="Step‑by‑step refactor plan.",
        agent=strategist,
    )

    t4 = Task(
        description=(
            f"Apply the approved improvements to **{code_path}**, overwrite the file, "
            "then run pytest. Ensure all tests pass and report the diff."
        ),
        expected_output="Patch/diff of the refactored file plus pytest summary.",
        agent=rewriter,
    )

    return Crew(
        agents=[summarizer, analyzer, strategist, rewriter],
        tasks=[t1, t2, t3, t4],
        process=Process.sequential,
        verbose=2,
        metadata={"code_path": code_path},
    )
