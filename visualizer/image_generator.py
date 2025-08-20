import torch
from diffusers import FluxPipeline
import os
from rich.console import Console
import traceback  # Import the traceback module for detailed error logging

console = Console()

class ImageGenerator:
    def __init__(self):
        self.pipe = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        try:
            console.log(f"[cyan]Initializing image generation pipeline on device: {self.device}...[/cyan]")

            # Choose a data type with better compatibility
            # float16 for GPU, float32 for CPU
            dtype = torch.float16 if self.device == "cuda" else torch.float32

            self.pipe = FluxPipeline.from_pretrained(
                "black-forest-labs/FLUX.1-schnell",
                torch_dtype=dtype
            )

            # For GPUs, use model offloading to save VRAM. For CPU, just move the model.
            if self.device == "cuda":
                self.pipe.enable_model_cpu_offload()
            else:
                self.pipe.to(self.device)

            console.log("[green]Image generation pipeline initialized successfully.[/green]")
        except Exception as e:
            console.log(f"[bold red]Error initializing image pipeline: {e}[/bold red]")
            # This will print the full, detailed error to the console
            console.log(traceback.format_exc())
            console.log("[yellow]Image generation will be skipped.[/yellow]")
            self.pipe = None

    def generate_image_from_thought(self, thought: str, session_id: int, attempt: int) -> str | None:
        if not self.pipe:
            console.log("[yellow]Skipping image generation: pipeline was not initialized.[/yellow]")
            return None

        # Create a more evocative prompt for better visuals
        prompt = f"Digital art, an abstract and minimalistic visualization of an AI agent's thought. Nodes, glowing connections, logic flows, representing the idea: '{thought}'."

        try:
            console.log(f"[cyan]Generating image for attempt {attempt}...[/cyan]")
            
            # If on GPU, clear cache to free up memory before running
            if self.device == "cuda":
                torch.cuda.empty_cache()

            image = self.pipe(
                prompt=prompt,
                num_inference_steps=8,  # Slightly increased for better quality
                guidance_scale=0.0,
            ).images[0]

            output_dir = "outputs/images"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Use os.path.join for a more robust file path
            file_path = os.path.join(output_dir, f"session_{session_id}_attempt_{attempt}.png")
            image.save(file_path)
            console.log(f"[green]Image saved to {file_path}[/green]")
            return file_path
        except Exception as e:
            console.log(f"[bold red]Failed to generate image: {e}[/bold red]")
            # This will print the full, detailed error to the console
            console.log(traceback.format_exc())
            return None
