import os
import traceback

import torch
from diffusers import FluxPipeline
from rich.console import Console

console = Console()


class ImageGenerator:
    """
    A class for generating images from textual thoughts using the FluxPipeline.
    """

    def __init__(self):
        """
        Initializes the ImageGenerator with a FluxPipeline, detects the device,
        and initializes the pipeline.
        """
        self.pipe = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """
        Initializes the FluxPipeline for image generation.
        Loads the pretrained model and configures it for the appropriate device (CPU or GPU).
        Handles potential exceptions during pipeline initialization.
        """
        try:
            console.log(f"[cyan]Initializing image generation pipeline on device: {self.device}...[/cyan]")

            # Choose data type based on device for compatibility and performance
            dtype = torch.float16 if self.device == "cuda" else torch.float32

            self.pipe = FluxPipeline.from_pretrained(
                "black-forest-labs/FLUX.1-schnell",
                torch_dtype=dtype,
            )

            # Model offloading for GPU to save VRAM, otherwise move to CPU
            if self.device == "cuda":
                self.pipe.enable_model_cpu_offload()
            else:
                self.pipe.to(self.device)

            console.log("[green]Image generation pipeline initialized successfully.[/green]")
        except Exception as e:
            console.log(f"[bold red]Error initializing image pipeline: {e}[/bold red]")
            # Print detailed traceback for debugging
            console.log(traceback.format_exc())
            console.log("[yellow]Image generation will be skipped.[/yellow]")
            self.pipe = None

    def generate_image_from_thought(self, thought: str, session_id: int, attempt: int) -> str | None:
        """
        Generates an image based on the given thought, session ID, and attempt number.
        Uses the initialized FluxPipeline to create the image and saves it to a file.

        Args:
            thought (str): The thought or concept to visualize in the image.
            session_id (int): The ID of the session for image generation.
            attempt (int): The attempt number for generating the image.

        Returns:
            str | None: The file path of the generated image if successful, otherwise None.
        """
        if not self.pipe:
            console.log("[yellow]Skipping image generation: pipeline was not initialized.[/yellow]")
            return None

        # Construct a more descriptive prompt to improve image quality
        prompt = (
            "Digital art, an abstract and minimalistic visualization of an AI agent's thought. "
            "Nodes, glowing connections, logic flows, representing the idea: '{thought}'."
        )

        try:
            console.log(f"[cyan]Generating image for attempt {attempt}...[/cyan]")

            # Clear CUDA cache on GPU before generation to free memory
            if self.device == "cuda":
                torch.cuda.empty_cache()

            image = self.pipe(
                prompt=prompt,
                num_inference_steps=8,  # Increased steps for better image quality
                guidance_scale=0.0,
            ).images[0]

            output_dir = "outputs/images"
            os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn't exist

            # Create a file path using os.path.join for platform independence
            file_path = os.path.join(output_dir, f"session_{session_id}_attempt_{attempt}.png")
            image.save(file_path)
            console.log(f"[green]Image saved to {file_path}[/green]")
            return file_path
        except Exception as e:
            console.log(f"[bold red]Failed to generate image: {e}[/bold red]")
            # Print detailed traceback for debugging
            console.log(traceback.format_exc())
            return None