import docker
import tempfile
import os
from rich.console import Console

console = Console()


class CodeSandbox:
    """
    A class for running Python code in a secure Docker container.

    This class uses the Docker SDK to create and manage containers, allowing
    the execution of user-provided code in an isolated environment with resource limits.
    """

    def __init__(self, image_name="python_sandbox"):
        """
        Initializes the CodeSandbox with the specified Docker image.

        Args:
            image_name (str): The name of the Docker image to use for the sandbox.
                               Defaults to "python_sandbox".

        Raises:
            SystemExit: If Docker is not running or configured correctly.
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
        Runs the given code with test cases in a secure Docker container.

        The code and test cases are combined into a single Python script,
        which is then executed inside the container. The container's output
        (stdout and stderr) and exit code are captured and returned.

        Args:
            code (str): The Python code to execute.
            test_cases (str): The test cases to run against the code.

        Returns:
            dict: A dictionary containing the execution result:
                - "success" (bool): True if the code ran successfully (exit code 0 and no stderr), False otherwise.
                - "stdout" (str): The standard output from the container.
                - "stderr" (str): The standard error from the container.
        """
        full_code = f"{code}\n\n# Test cases\n{test_cases}"

        # Create a temporary directory to store the script.
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, "script.py")

            # Write the combined code and test cases to the script file.
            with open(script_path, "w") as f:
                f.write(full_code)

            try:
                # Run the code in a Docker container.
                container = self.client.containers.run(
                    self.image_name,
                    command=["python", "script.py"],
                    volumes={os.path.abspath(temp_dir): {'bind': '/app', 'mode': 'ro'}},
                    working_dir="/app",
                    detach=True,
                    mem_limit="256m",  # Limit memory usage
                    cpu_shares=512,  # Limit CPU usage (relative weight)
                )

                # Wait for the container to finish, with a timeout.
                result = container.wait(timeout=15)
                exit_code = result['StatusCode']

                # Get the output from the container.
                stdout = container.logs(stdout=True, stderr=False).decode('utf-8').strip()
                stderr = container.logs(stdout=False, stderr=True).decode('utf-8').strip()

                # Remove the container.
                container.remove()

                # Determine if the execution was successful.
                is_success = exit_code == 0 and not stderr

                # Return the results.
                return {"success": is_success, "stdout": stdout, "stderr": stderr}

            except docker.errors.ContainerError as e:
                # Handle Docker container errors.
                return {"success": False, "stdout": "", "stderr": str(e)}
            except Exception as e:  # Catch timeouts and other exceptions
                # Handle exceptions during container execution, especially timeouts.
                # Ensure the container is stopped and removed if an error occurs.
                if 'container' in locals() and container:
                    container.stop()
                    container.remove()
                return {"success": False, "stdout": "", "stderr": f"Execution timed out or failed: {e}"}