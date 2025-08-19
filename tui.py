import os
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Header, Footer, Static, RichLog, Button, Input, Tree
from textual.worker import work
from textual.screen import Screen
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from agent.agent import SelfCorrectingAgent
from database.database import init_db

# Load environment variables for the agent
load_dotenv()
init_db()

class AgentScreen(Screen):
    """The main screen where the agent operates."""
    CSS_PATH = "tui.css"
    
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, problem: str, test_cases: str):
        super().__init__()
        self.problem = problem
        self.test_cases = test_cases
        self.llm_model = os.getenv("LLM_MODEL")
        self.max_attempts = int(os.getenv("MAX_CORRECTION_ATTEMPTS", 5))

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            with VerticalScroll(id="left-panel"):
                yield Static(Panel(self.problem, title="[bold cyan]Problem Statement[/bold cyan]"), id="problem-statement")
                yield RichLog(id="agent-log", wrap=True, highlight=True)
            with Container(id="right-panel"):
                yield Static("[bold #888]Session History[/bold #888]", id="history-title")
                yield Tree("Agent Run", id="history-tree")
        yield Footer()

    def on_mount(self) -> None:
        """Start the agent worker when the screen is mounted."""
        self.query_one(RichLog).write("[yellow]Agent worker started...[/yellow]")
        self.run_agent()

    @work(exclusive=True, thread=True)
    def run_agent(self) -> None:
        """Runs the agent in a separate thread."""
        agent = SelfCorrectingAgent(model=self.llm_model, max_attempts=self.max_attempts)
        
        # The agent's run method is now a generator
        for update in agent.run(self.problem, self.test_cases):
            self.app.call_from_thread(self.handle_agent_update, update)

    def handle_agent_update(self, update: dict) -> None:
        """Handles updates from the agent and refreshes the UI."""
        log = self.query_one("#agent-log")
        history_tree = self.query_one("#history-tree")
        
        update_type = update.get('type')
        
        if update_type == 'start':
            history_tree.root.set_label(f"Session ID: {update.get('session_id')}")
            
        elif update_type == 'thought':
            log.write(Panel(update.get('content'), title="[cyan]🧠 Thinking...[/cyan]"))
        
        elif update_type == 'code':
            log.write(Panel(Syntax(update.get('content'), "python", theme="monokai", line_numbers=True), title="[magenta]🐍 Generated Code[/magenta]"))

        elif update_type == 'result':
            result = update.get('data', {})
            if result.get('success'):
                log.write(Panel("✅ [bold green]Execution Succeeded[/bold green]", expand=False))
                history_tree.root.add_leaf("✅ Success")
            else:
                error_msg = f"[bold]STDOUT:[/bold]\n{result.get('stdout')}\n\n[bold]STDERR:[/bold]\n{result.get('stderr')}"
                log.write(Panel(error_msg, title="[bold red]❌ Execution Failed[/bold red]"))
                history_tree.root.add_leaf("❌ Failure")

        elif update_type == 'status':
            log.write(f"[yellow]{update.get('message')}[/yellow]")
        
        elif update_type == 'image':
            log.write(f"🖼️ [dim]Thought visualization saved to: [u]{update.get('path')}[/u][/dim]")

        elif update_type == 'done':
            log.write(Panel(f"🏆 [bold green]Agent Finished![/bold green]\nFinal code saved to: {update.get('saved_path')}", expand=False))
        
        elif update_type == 'error':
            log.write(f"[bold red]ERROR: {update.get('message')}[/bold red]")
            history_tree.root.add_leaf("🚨 Error")


class InputScreen(Screen):
    """The initial screen for user input."""
    CSS_PATH = "tui.css"

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="input-container"):
            yield Static("[bold]Welcome to the Self-Correcting Code Agent[/bold]", id="title")
            yield Static("Enter the programming problem you want to solve:")
            yield Input(
                "Write a Python function `factorial(n)` that returns the factorial of a non-negative integer `n`.",
                id="problem-input"
            )
            yield Static("Enter the test cases (one assert per line):")
            yield Input(
                "assert factorial(0) == 1\nassert factorial(5) == 120",
                id="tests-input",
            )
            yield Button("Run Agent", variant="success", id="run-button")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle the run button press."""
        if event.button.id == "run-button":
            problem = self.query_one("#problem-input").value
            tests = self.query_one("#tests-input").value
            self.app.push_screen(AgentScreen(problem, tests))


class AgentApp(App):
    """The main Textual application."""
    SCREENS = {"input": InputScreen()}
    CSS_PATH = "tui.css"

    def on_mount(self) -> None:
        self.push_screen("input")