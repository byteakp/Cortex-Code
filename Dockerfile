
# Use a minimal, secure base image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# This container is for running untrusted code.
# Do not install any extra packages here to minimize attack surface.
# The agent will mount the code to be executed into this container.

CMD ["python"]
