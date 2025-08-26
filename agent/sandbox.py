import docker
import tempfile
import os
from rich.console import Console

console = Console()

class CodeSandbox:
    """
    Provides a secure sandbox environment for running Python code using Docker.
    """
    def __init__(self, image_name="python_sandbox"):
        """
        Initializes the CodeSandbox with a Docker client and image name.
        Checks if Docker is running and accessible.
        Args:
            image_name (str): The name of the Docker image to use. Defaults to "python_sandbox".
        """
        self.client = docker.from_env()
        self.image_name = image_name
        try:
            self.client.ping()
        except Exception as e:
            console.log("[bold red]Docker is not running or not configured correctly.[/bold red]")
            console.log(f"Error: {e}")
            console.log("Please start Docker and ensure it's accessible.")
            exit(1)

    def run(self, code: str, test_cases: str) -> dict:
        """
        Runs the given code with test cases in a Docker container.

        Args:
            code (str): The Python code to execute.
            test_cases (str): The test cases to run.

        Returns:
            dict: A dictionary containing the execution result, including success status, stdout, and stderr.
        """
        full_code = f"{code}\n\n# Test cases\n{test_cases}"

        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, "script.py")
            with open(script_path, "w") as f:
                f.write(full_code)

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
            except Exception as e:
                # Handle exceptions during container execution, including timeouts.
                if 'container' in locals() and container:
                    container.stop()
                    container.remove()
                return {"success": False, "stdout": "", "stderr": f"Execution timed out or failed: {e}"}