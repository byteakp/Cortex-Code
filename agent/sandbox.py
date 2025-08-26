import docker
import tempfile
import os
from rich.console import Console

console = Console()


class CodeSandbox:
    """
    A class to execute code snippets in a sandboxed Docker container.
    """

    def __init__(self, image_name="python_sandbox"):
        """
        Initializes the CodeSandbox with a Docker client and image name.

        Args:
            image_name (str, optional): The name of the Docker image to use. Defaults to "python_sandbox".
        """
        self.client = docker.from_env()
        self.image_name = image_name
        self._verify_docker_connection()

    def _verify_docker_connection(self):
        """
        Verifies that Docker is running and accessible. Exits the program if not.
        """
        try:
            self.client.ping()
        except Exception as e:
            console.log("[bold red]Docker is not running or not configured correctly.[/bold red]")
            console.log(f"Error: {e}")
            console.log("Please start Docker and ensure it's accessible.")
            exit(1)

    def run(self, code: str, test_cases: str) -> dict:
        """
        Runs the given code with test cases in a secure Docker container.

        Args:
            code (str): The code to be executed.
            test_cases (str): The test cases to be run against the code.

        Returns:
            dict: A dictionary containing the execution results:
                - success (bool): True if the code executed successfully, False otherwise.
                - stdout (str): The standard output of the code execution.
                - stderr (str): The standard error of the code execution.
        """
        full_code = f"{code}\n\n# Test cases\n{test_cases}"

        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, "script.py")
            self._write_code_to_file(full_code, script_path)

            try:
                container = self.client.containers.run(
                    self.image_name,
                    command=["python", "script.py"],
                    volumes={os.path.abspath(temp_dir): {'bind': '/app', 'mode': 'ro'}},
                    working_dir="/app",
                    detach=True,
                    mem_limit="256m",  # Limit memory usage
                    cpu_shares=512,  # Limit CPU usage (relative weight)
                )

                # Wait for container to finish, with a timeout
                result = container.wait(timeout=15)
                exit_code = result['StatusCode']

                stdout = container.logs(stdout=True, stderr=False).decode('utf-8').strip()
                stderr = container.logs(stdout=False, stderr=True).decode('utf-8').strip()

                container.remove()

                is_success = exit_code == 0 and not stderr
                return {"success": is_success, "stdout": stdout, "stderr": stderr}

            except docker.errors.ContainerError as e:
                return {"success": False, "stdout": "", "stderr": str(e)}
            except Exception as e:  # Catches timeouts and other exceptions
                if 'container' in locals() and 'container' in vars():
                    if isinstance(container, docker.models.containers.Container):
                        container.stop()
                        container.remove()
                return {"success": False, "stdout": "", "stderr": f"Execution timed out or failed: {e}"}

    def _write_code_to_file(self, code: str, script_path: str):
        """
        Writes the given code to a file.

        Args:
            code (str): The code to be written.
            script_path (str): The path to the file.
        """
        with open(script_path, "w") as f:
            f.write(code)