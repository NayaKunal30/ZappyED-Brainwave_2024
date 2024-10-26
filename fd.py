import requests
import io
from PIL import Image, ImageDraw, ImageFont, ImageOps
import os
import random
from huggingface_hub import InferenceClient
from reportlab.pdfgen import canvas
from easygoogletranslate import EasyGoogleTranslate
from langchain_groq import ChatGroq

class TranslateHelper:
    def __init__(self):
        self.translator = EasyGoogleTranslate()
    
    def lang_translate(self, text, target_lang):
        if target_lang == "en":
            return text
        else:
            return self.translator.translate(text, target_lang)

def rounded_corners(image, radius):
    """Apply rounded corners to an image."""
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), image.size], radius, fill=255)
    rounded_image = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    rounded_image.putalpha(mask)
    return rounded_image

def wrap_text(text, font, max_width):
    """Wrap text to fit within the specified width."""
    lines = []
    words = text.split()
    line = []

    for word in words:
        test_line = ' '.join(line + [word])
        line_width, _ = font.getbbox(test_line)[2:4]
        if line and line_width > max_width:
            lines.append(' '.join(line))
            line = [word]
        else:
            line.append(word)

    lines.append(' '.join(line))
    return lines

def GenerateComic(topic, style, target_lang):
    # Initialize the ChatGroq model for text generation
    llm = ChatGroq(
        temperature=0,
        groq_api_key='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',
        model="gemma2-9b-it"
    )

    # Initialize TranslateHelper
    translator = TranslateHelper()

    # Define your prompt based on style
    style_prompts = {
        "Disney Princes": "funny disney with cinderella, snow white or mickey mouse style",
        "Marvel": "funny marvel with avengers, captain america, hulk, thor, iron man or spiderman style",
        "Anime": "funny anime with naruto, zoro, death note, demon slayer, one punch man or dragon ball z style",
        "DC Comics": "funny batman style",
        "Observable Universe": "interesting story about facts of universe"
    }
    
    style_prompt = style_prompts.get(style, "funny story")

    # Add a unique noise for randomness
    noise_value = random.randint(1, 100000)

    # Combine the topic with the style prompt and noise
    prompt = f"in 6 different phrases parts, noise {noise_value}each part divided by a blank line, narrate a story on the topic {topic} like a {style} comic book.noise {noise_value} keep the sentences 100 words long. separate each phrase by a blank line. noise {noise_value} "


    # Use the ChatGroq model to generate the story
    response = llm.invoke(prompt)
    story = response.content

    # Split the story into phrases
    phrases = story.strip().split("\n\n")

    # Directory to save images
    output_dir = os.path.join("D:\\KKCODINGPL\\PROJECTS\\ML PROJECTS\\ZappyED\\templates", f"story_{random.randint(1, 100000)}")
    os.makedirs(output_dir, exist_ok=True)

    # Function to query the Stable Diffusion model for images
    API_URL = "https://api-inference.huggingface.co/models/ntc-ai/SDXL-LoRA-slider.2000s-indie-comic-art-style"
    headers = {"Authorization": f"Bearer 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"}

    def query(payload):
        response = requests.post(API_URL, headers=headers, json=payload)
        return response

    # Path to the comic font
    font_path = "D:\\KKCODINGPL\\PROJECTS\\ML PROJECTS\\ZappyED\\font\\animeace2_reg.ttf"

    # Load background image
    background_path = "D:\\KKCODINGPL\\PROJECTS\\ML PROJECTS\\ZappyED\\bg img.png"
    background_image = Image.open(background_path)

    # Calculate gaps and dimensions
    background_width, background_height = background_image.size
    gap = 20  # Gap between text box and generated image, and between background edges
    double_gap = 2 * gap  # Gap between text box and generated image

    text_box_height = background_height // 4
    generated_image_height = background_height - text_box_height - double_gap - 2 * gap

    # Generate and save images for each phrase with text overlay
    image_paths = []  # To store paths of images
    for i, phrase in enumerate(phrases):
        # Add noise to the image generation prompt
        image_prompt = f"{phrase}, unique id {noise_value}"

        response = query({"inputs": image_prompt})

        # Check if the response was successful
        if response.status_code == 200:
            image_bytes = response.content
            try:
                image = Image.open(io.BytesIO(image_bytes))

                # Apply rounded corners and add a black border
                radius = 20  # Adjust the radius as needed
                image = rounded_corners(image, radius)
                border_color = (0, 0, 0)
                border_width = 5
                image = ImageOps.expand(image, border=border_width, fill=border_color)

                # Resize the image to fit below the text box
                image = image.resize((background_width - 2 * gap, generated_image_height))

                # Create a white box with rounded corners for the text
                text_width = background_width - 2 * gap
                white_box = Image.new("RGBA", (text_width, text_box_height), "orange")  # Transparent
                white_box = rounded_corners(white_box, radius)
                draw = ImageDraw.Draw(white_box)

                # Translate the phrase to the target language for overlay
                translated_phrase = translator.lang_translate(phrase, target_lang)

                # Adjust font size to fit text within the text box
                font_size = 30
                font = ImageFont.truetype(font_path, size=font_size)
                max_text_width = text_width - 20  # Margin for padding
                wrapped_text = wrap_text(translated_phrase, font, max_text_width)

                # Check if the text fits within the text box
                text_height = sum(font.getbbox(line)[3] - font.getbbox(line)[1] for line in wrapped_text) + len(wrapped_text) * 5  # Line height + padding
                if text_height > text_box_height:
                    while text_height > text_box_height and font_size > 10:
                        font_size -= 1
                        font = ImageFont.truetype(font_path, size=font_size)
                        wrapped_text = wrap_text(translated_phrase, font, max_text_width)
                        text_height = sum(font.getbbox(line)[3] - font.getbbox(line)[1] for line in wrapped_text) + len(wrapped_text) * 5

                # Calculate vertical position for the text
                y_text = (text_box_height - text_height) // 2
                for line in wrapped_text:
                    text_bbox = draw.textbbox((0, y_text), line, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    position = ((white_box.width - text_width) // 2, y_text)
                    draw.text(position, line, font=font, fill="black")
                    y_text += text_bbox[3] - text_bbox[1] + 5  # Line height + padding

                # Add a black border to the text box
                white_box = ImageOps.expand(white_box, border=border_width, fill=border_color)

                # Create a new image with the text box at the top and the generated image below
                new_image = Image.new("RGBA", (background_width, background_height), (255, 255, 255, 0))  # Transparent background
                new_image.paste(background_image, (0, 0))  # Paste the background image
                new_image.paste(white_box, (gap, gap), white_box)
                new_image.paste(image, (gap, text_box_height + double_gap + gap), image)

                # Save the combined image
                image_path = os.path.join(output_dir, f"image_{i+1}.png")
                new_image.save(image_path)
                image_paths.append(image_path)  # Add image path to the list
                print(f"Saved image for phrase {i+1}: {image_path}")
            except Exception as e:
                print(f"Failed to process image for phrase {i+1}: {e}")
        else:
            print(f"Request failed with status code {response.status_code}: {response.text}")

    # Create a PDF from the images
    pdf_directory = "D:\\KKCODINGPL\\PROJECTS\\ML PROJECTS\\ZappyED\\comicpdf"
    os.makedirs(pdf_directory, exist_ok=True)

    # Create a unique name for the PDF using a random unique ID
    pdf_path = os.path.join(pdf_directory, f"comic_{random.randint(1, 100000)}.pdf")
    c = canvas.Canvas(pdf_path)
    for image_path in image_paths:
        img = Image.open(image_path)
        width, height = img.size
        c.setPageSize((width, height))
        c.drawImage(image_path, 0, 0, width, height)
        c.showPage()
    c.save()
    print(f"PDF created at {pdf_path}")

# Example usage
language_symbols = {
    "English": "en", "Spanish": "es", "French": "fr", "Hindi": "hi",
    "Arabic": "ar", "Bengali": "bn", "Telugu": "te", "Marathi": "mr",
    "Tamil": "ta", "Urdu": "ur", "Gujarati": "gu", "Kannada": "kn",
    "Odia": "or", "Punjabi": "pa"
}