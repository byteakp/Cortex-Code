# file: tui.py

import os
from dotenv import load_dotenv
import pyperclip 

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Header, Footer, Static, RichLog, Button, Input, Tree, Select, LoadingIndicator, TextArea
from textual.screen import Screen

from rich.panel import Panel
from rich.syntax import Syntax

from agent.agent import SelfCorrectingAgent
from database.database import init_db

# Load environment variables for the agent
load_dotenv()
init_db()

class CodeBlock(Container):
    """A widget to display a block of code with a copy button."""
    def __init__(self, code: str, language: str = "python", theme: str = "monokai"):
        super().__init__()
        self.code_content = code
        self.language = language
        self.theme = theme

    def compose(self) -> ComposeResult:
        yield Static(
            Syntax(self.code_content, self.language, theme=self.theme, line_numbers=True, word_wrap=True),
            expand=True,
            id="code-syntax"
        )
        yield Button("📋 Copy Code", id="copy-button", variant="default")

    def on_mount(self) -> None:
        self.border_title = f"🐍 Generated Code"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "copy-button":
            try:
                pyperclip.copy(self.code_content)
                event.button.label = "✅ Copied!"
                self.set_timer(2.0, lambda: self.reset_button_label(event.button))
            except pyperclip.PyperclipException:
                event.button.label = "❌ Copy Failed"
                self.set_timer(2.0, lambda: self.reset_button_label(event.button))

    def reset_button_label(self, button: Button) -> None:
        if button.is_mounted:
            button.label = "📋 Copy Code"


class AgentScreen(Screen):
    CSS_PATH = "tui.css"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("n", "new_task", "New Task"),
    ]

    def __init__(self, problem: str, test_cases: str, model: str):
        super().__init__()
        self.problem = problem
        self.test_cases = test_cases
        self.llm_model = model
        self.max_attempts = int(os.getenv("MAX_CORRECTION_ATTEMPTS", 5))
        self.is_finished = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            with VerticalScroll(id="left-panel") as vs:
                vs.can_focus = True
                yield Static(Panel(self.problem, title="[bold cyan]Problem Statement[/bold cyan]"), id="problem-statement")
                with Container(id="new-task-container"):
                    yield Button("Start New Task (n)", id="new-task-button", variant="primary")
                yield LoadingIndicator()
                yield RichLog(id="agent-log", wrap=True, highlight=True)
            with Container(id="right-panel"):
                yield Static("[bold #888]Session History[/bold #888]", id="history-title")
                yield Tree("Agent Run", id="history-tree")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#agent-log").write("[yellow]Agent worker started...[/yellow]")
        self.run_worker(self.run_agent, exclusive=True, thread=True)

    def run_agent(self) -> None:
        agent = SelfCorrectingAgent(model=self.llm_model, max_attempts=self.max_attempts)
        for update in agent.run(self.problem, self.test_cases):
            # 👇 FIX #2: Safely call the UI update method from the worker thread
            self.call_from_thread(self.handle_agent_update, update)

    def handle_agent_update(self, update: dict) -> None:
        log = self.query_one("#agent-log")
        history_tree = self.query_one("#history-tree")
        left_panel = self.query_one("#left-panel")
        loader = self.query_one(LoadingIndicator)
        update_type = update.get('type')
        if update_type == 'start':
            history_tree.root.set_label(f"Session ID: {update.get('session_id')}")
        elif update_type == 'thought':
            loader.display = False
            log.write(Panel(update.get('content'), title="[cyan]🧠 Thinking...[/cyan]"))
        elif update_type == 'code':
            loader.display = False
            code_block = CodeBlock(update.get('content'))
            left_panel.mount(code_block)
            left_panel.scroll_end(animate=True)
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
            if "Thinking..." in update.get('message', ''):
                loader.display = True
            else:
                log.write(f"[yellow]{update.get('message')}[/yellow]")
        elif update_type == 'image':
            log.write(f"🖼️ [dim]Thought visualization saved to: [u]{update.get('path')}[/u][/dim]")
        elif update_type == 'done':
            log.write(Panel(f"🏆 [bold green]Agent Finished![/bold green]\nFinal code saved to: {update.get('saved_path')}", expand=False))
            self.show_new_task_button()
        elif update_type == 'error':
            loader.display = False
            log.write(f"[bold red]ERROR: {update.get('message')}[/bold red]")
            history_tree.root.add_leaf("🚨 Error")
            self.show_new_task_button()

    def show_new_task_button(self) -> None:
        self.is_finished = True
        container = self.query_one("#new-task-container")
        container.styles.display = "block"

    def action_new_task(self) -> None:
        if self.is_finished:
            self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "new-task-button":
            self.app.pop_screen()

class InputScreen(Screen):
    CSS_PATH = "tui.css"

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="input-container"):
            yield Static("[bold]Welcome to the Self-Correcting Code Agent[/bold]", id="title")
            yield Static("Select an LLM Model:")
            yield Select(
                [
                    ("Groq Llama3 70b", "groq/llama3-70b-8192"),
                    ("Mistral Codestral", "codestral-latest"),
                    ("OpenAI GPT-4o", "gpt-4o"),
                ],
                prompt="Choose a model...",
                id="model-select",
                value="groq/llama3-70b-8192",
            )
            yield Static("Enter the programming problem you want to solve:")
            yield Input(
                "Write a Python function `factorial(n)` that returns the factorial of a non-negative integer `n`.",
                id="problem-input"
            )
            yield Static("Enter the test cases (one assert per line):")
            yield TextArea(
                "assert factorial(0) == 1\nassert factorial(5) == 120",
                id="tests-input",
            )
            yield Button("Run Agent", variant="success", id="run-button")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-button":
            problem = self.query_one("#problem-input").value
            tests = self.query_one("#tests-input").text
            model = self.query_one(Select).value
            if not model:
                self.app.bell()
                self.query_one(Select).focus()
                return
            self.app.push_screen(AgentScreen(problem, tests, model))

class AgentApp(App):
    """The main Textual application."""
    # 👇 FIX #1: Use the class itself, not an instance
    SCREENS = {"input": InputScreen}
    CSS_PATH = "tui.css"

    def on_mount(self) -> None:
        self.push_screen("input")
