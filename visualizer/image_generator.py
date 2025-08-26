import os
import traceback

import torch
from diffusers import FluxPipeline
from rich.console import Console

console = Console()


class ImageGenerator:
    """
    A class for generating images from text prompts using the FluxPipeline.
    """

    def __init__(self):
        """
        Initializes the ImageGenerator by setting the device and initializing the pipeline.
        """
        self.pipe = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """
        Initializes the image generation pipeline.

        Loads the FluxPipeline from a pre-trained model, sets the data type, and configures the pipeline
        for either CPU or GPU usage. Handles potential errors during pipeline initialization.
        """
        try:
            console.log(
                f"[cyan]Initializing image generation pipeline on device: {self.device}...[/cyan]"
            )

            # Choose a data type with better compatibility
            # float16 for GPU, float32 for CPU
            dtype = torch.float16 if self.device == "cuda" else torch.float32

            self.pipe = FluxPipeline.from_pretrained(
                "black-forest-labs/FLUX.1-schnell", torch_dtype=dtype
            )

            # For GPUs, use model offloading to save VRAM. For CPU, just move the model.
            if self.device == "cuda":
                self.pipe.enable_model_cpu_offload()
            else:
                self.pipe.to(self.device)

            console.log("[green]Image generation pipeline initialized successfully.[/green]")
        except Exception as e:
            console.log(f"[bold red]Error initializing image pipeline: {e}[/bold red]")
            console.log(traceback.format_exc())  # Prints the full error traceback
            console.log("[yellow]Image generation will be skipped.[/yellow]")
            self.pipe = None

    def generate_image_from_thought(self, thought: str, session_id: int, attempt: int) -> str | None:
        """
        Generates an image from a given thought (text prompt).

        Args:
            thought (str): The text prompt to generate the image from.
            session_id (int): The ID of the current session. Used for file naming.
            attempt (int): The attempt number for image generation. Used for file naming.

        Returns:
            str | None: The file path to the generated image, or None if image generation fails.
        """
        if not self.pipe:
            console.log("[yellow]Skipping image generation: pipeline was not initialized.[/yellow]")
            return None

        # Create a more evocative prompt for better visuals
        prompt = (
            "Digital art, an abstract and minimalistic visualization of an AI agent's thought. "
            "Nodes, glowing connections, logic flows, representing the idea: '{thought}'."
        )

        try:
            console.log(f"[cyan]Generating image for attempt {attempt}...[/cyan]")

            # If on GPU, clear cache to free up memory before running
            if self.device == "cuda":
                torch.cuda.empty_cache()

            image = self.pipe(
                prompt=prompt, num_inference_steps=8, guidance_scale=0.0
            ).images[0]

            output_dir = "outputs/images"
            os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn't exist

            # Use os.path.join for a more robust file path
            file_path = os.path.join(output_dir, f"session_{session_id}_attempt_{attempt}.png")
            image.save(file_path)
            console.log(f"[green]Image saved to {file_path}[/green]")
            return file_path
        except Exception as e:
            console.log(f"[bold red]Failed to generate image: {e}[/bold red]")
            console.log(traceback.format_exc())  # Prints the full error traceback
            return None