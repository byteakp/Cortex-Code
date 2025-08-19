import torch
from diffusers import FluxPipeline
import os
from rich.console import Console

console = Console()

class ImageGenerator:
    def __init__(self):
        self.pipe = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        try:
            console.log(f"[cyan]Initializing image generation pipeline on device: {self.device}...[/cyan]")
            self.pipe = FluxPipeline.from_pretrained(
                "black-forest-labs/FLUX.1-schnell",
                torch_dtype=torch.bfloat16
            )
            self.pipe.to(self.device)
            console.log("[green]Image generation pipeline initialized successfully.[/green]")
        except Exception as e:
            console.log(f"[bold red]Error initializing image pipeline: {e}[/bold red]")
            console.log("[yellow]Image generation will be skipped.[/yellow]")
            self.pipe = None

    def generate_image_from_thought(self, thought: str, session_id: int, attempt: int) -> str | None:
        if not self.pipe:
            return None

        prompt = f"Digital art, abstract visualization of an AI's thought process: '{thought}'. Minimalistic, nodes, connections, logic flow."

        try:
            console.log(f"[cyan]Generating image for attempt {attempt}...[/cyan]")
            image = self.pipe(
                prompt=prompt,
                num_inference_steps=4,
                guidance_scale=0.0,
            ).images[0]

            if not os.path.exists("outputs/images"):
                os.makedirs("outputs/images")

            file_path = f"outputs/images/session_{session_id}_attempt_{attempt}.png"
            image.save(file_path)
            console.log(f"[green]Image saved to {file_path}[/green]")
            return file_path
        except Exception as e:
            console.log(f"[bold red]Failed to generate image: {e}[/bold red]")
            return None