import torch
from diffusers import FluxPipeline
import os
from rich.console import Console
import traceback

console = Console()

class ImageGenerator:
    """
    Generates images from text prompts using the Flux diffusion model.
    """
    def __init__(self):
        """
        Initializes the image generation pipeline.
        Selects the appropriate device (CUDA if available, otherwise CPU) and data type.
        """
        self.pipe = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """
        Initializes the FluxPipeline. Handles exceptions during initialization.
        """
        try:
            console.log(f"[cyan]Initializing image generation pipeline on device: {self.device}...[/cyan]")
            dtype = torch.float16 if self.device == "cuda" else torch.float32
            self.pipe = FluxPipeline.from_pretrained(
                "black-forest-labs/FLUX.1-schnell",
                torch_dtype=dtype
            )
            if self.device == "cuda":
                self.pipe.enable_model_cpu_offload()
            else:
                self.pipe.to(self.device)
            console.log("[green]Image generation pipeline initialized successfully.[/green]")
        except Exception as e:
            console.log(f"[bold red]Error initializing image pipeline: {e}[/bold red]")
            console.log(traceback.format_exc())
            console.log("[yellow]Image generation will be skipped.[/yellow]")
            self.pipe = None

    def generate_image_from_thought(self, thought: str, session_id: int, attempt: int) -> str | None:
        """
        Generates an image from a given text prompt and saves it to the 'outputs/images' directory.

        Args:
            thought: The text prompt to generate the image from.
            session_id: The ID of the current session.
            attempt: The attempt number for the current image generation.

        Returns:
            The file path of the generated image, or None if generation failed.
        """
        if not self.pipe:
            console.log("[yellow]Skipping image generation: pipeline was not initialized.[/yellow]")
            return None

        prompt = f"Digital art, an abstract and minimalistic visualization of an AI agent's thought. Nodes, glowing connections, logic flows, representing the idea: '{thought}'."

        try:
            console.log(f"[cyan]Generating image for attempt {attempt}...[/cyan]")
            if self.device == "cuda":
                torch.cuda.empty_cache()
            image = self.pipe(
                prompt=prompt,
                num_inference_steps=8,
                guidance_scale=0.0,
            ).images[0]
            os.makedirs("outputs/images", exist_ok=True)
            file_path = os.path.join("outputs/images", f"session_{session_id}_attempt_{attempt}.png")
            image.save(file_path)
            console.log(f"[green]Image saved to {file_path}[/green]")
            return file_path
        except Exception as e:
            console.log(f"[bold red]Failed to generate image: {e}[/bold red]")
            console.log(traceback.format_exc())
            return None