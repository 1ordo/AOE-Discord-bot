import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import textwrap
from langdetect import detect
from database import database #database.py
import discord
import re
import os
from PIL import ImageFilter
class resources:
    def extract_message_and_channel_id(input_str):
        # Regular expression pattern to match the last two integers in the Discord message URL
        pattern = r'https:\/\/discord\.com\/channels\/\d+\/(\d+)\/(\d+)'
        match = re.search(pattern, input_str)

        if match:
            channel_id = int(match.group(1))
            message_id = int(match.group(2))
            return message_id, channel_id
        elif input_str.isdigit():
            return int(input_str), None
        else:
            return None, None

    def generate_image(guild_id, message, avatar_url, user_id):
        # Define the folder path for saving images (relative path)
        #background_color = (0, 128, 0, 200)  # Green color with transparency
        background_color = (4, 59, 16,150)  # Black color with transparency
                
                
        
        folder_path = os.path.join("welcome_images")
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Path for saving the image
        image_save_path = os.path.join(folder_path, f"{guild_id}_{user_id}.png")  # Save a unique image per user

        # Load the base background image (this should be pre-existing or generated only once for the guild)
        base_image_path = os.path.join(folder_path, f"{guild_id}.png")
        if not os.path.exists(base_image_path):
            # Create a new base image if it doesn't exist
            base_background_image = Image.new("RGBA", (2333, 1200), (0, 0, 0, 0))
            base_background_image.save(base_image_path)
        else:
            # Load the pre-existing base image
            base_background_image = Image.open(base_image_path).convert("RGBA")

        # Create a new image from the base for this user
        background_image = base_background_image.copy()

        # Download the avatar image
        avatar_response = requests.get(avatar_url)
        avatar_image = Image.open(BytesIO(avatar_response.content)).convert("RGBA")

        # Resize the avatar to fit the image size
        avatar_size = min(background_image.size[0], background_image.size[1]) // 3
        avatar_image = avatar_image.resize((avatar_size, avatar_size))

        # Create a circular mask for the avatar
        mask = Image.new("L", (avatar_size, avatar_size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
        
        

        circle_size = avatar_size + 10  
        circle = Image.new("RGBA", (circle_size, circle_size), (87,205,120,200))  # White circle
        circle_mask = Image.new("L", (circle_size, circle_size), 0)
        circle_draw = ImageDraw.Draw(circle_mask)
        circle_draw.ellipse((0, 0, circle_size, circle_size), fill=255)
        circle.putalpha(circle_mask)  # Add mask to the circle
        circle = circle.filter(ImageFilter.GaussianBlur(radius=2))
        
        

        # Adjust the position to be more on top
        start_x = (background_image.size[0] - circle_size) // 2
        start_y = (background_image.size[1] - circle_size) // 3  # Move up by reducing the divisor
        start_y = int(start_y)  # Ensure start_y is an integer
        background_image.paste(circle, (start_x, start_y), circle)

        avatar_with_mask = Image.new("RGBA", (avatar_size, avatar_size))
        avatar_with_mask.paste(avatar_image, (0, 0), mask)

        start_x = (background_image.size[0] - avatar_size) // 2
        start_y = (background_image.size[1] - avatar_size) // 3  # Move up by reducing the divisor
        start_y = int(start_y)  # Ensure start_y is an integer
        background_image.paste(avatar_with_mask, (start_x, start_y), avatar_with_mask)

        # Draw text (message) onto the image
        draw = ImageDraw.Draw(background_image)

        # Define font scaling based on image size
        scaling_factor = min(background_image.size) / 1000  # Adjust scaling factor
        max_font_size = int(55 * scaling_factor)
        min_font_size = int(35 * scaling_factor)

        # Set initial font size
        font_path = os.path.join('resources', 'good_font.ttf')  # Path to your font file


        message = remove_emojis(message)
        font_size = max_font_size
        font = ImageFont.truetype(font_path, font_size)

        # Split the message into multiple lines if necessary
        wrapped_lines = []
        max_width = background_image.size[0] * 0.8

        # Reduce font size if the message is too long and wrap it
        while True:
            # Wrap the message text to fit within the image
            wrapped_message = textwrap.fill(message, width=int(max_width // font_size * 2))
            lines = wrapped_message.splitlines()
            fits = all(draw.textbbox((0, 0), line, font)[2] < max_width for line in lines)

            if fits:
                wrapped_lines = lines
                break

            font_size -= 10  # Reduce the font size if the text is too wide
            if font_size < min_font_size:  # Minimum size to avoid too small text
                font_size = min_font_size
                break
            font = ImageFont.truetype(font_path, font_size)

        # Calculate the starting Y position for drawing text
        message_y = start_y + avatar_size + 20
        line_height = draw.textbbox((0, 0), "A", font)[3] - draw.textbbox((0, 0), "A", font)[1]  # Height of one line of text

        # Add spacing between lines
        line_spacing = int(20 * scaling_factor)  # Adjust spacing based on image size
        padding_x = int(20 * scaling_factor)
        padding_y = int(10 * scaling_factor)
        border_radius = int(15 * scaling_factor)
        # Draw each line centered on the image
        for line in wrapped_lines:
            # Measure the size of the text
            message_bbox = draw.textbbox((0, 0), line, font=font)
            text_width = message_bbox[2] - message_bbox[0]
            text_height = message_bbox[3] - message_bbox[1]

            # Calculate the X position to center the text
            message_x = (background_image.size[0] - text_width) // 2

            # Calculate the bounding box at the drawing position
            message_bbox = draw.textbbox((message_x, message_y), line, font=font)

            # Expand the bounding box by padding
            bbox_left = message_bbox[0] - padding_x
            bbox_top = message_bbox[1] - padding_y
            bbox_right = message_bbox[2] + padding_x
            bbox_bottom = message_bbox[3] + padding_y

            # Create a new transparent image to draw the rounded rectangle
            rectangle_image = Image.new('RGBA', background_image.size, (0, 0, 0, 0))
            rectangle_draw = ImageDraw.Draw(rectangle_image)

            # Draw the rounded rectangle on the transparent image
            rectangle_draw.rounded_rectangle(
                [bbox_left, bbox_top, bbox_right, bbox_bottom],
                radius=border_radius,
                fill=background_color
            )

            # Composite the rectangle image over the background image
            background_image = Image.alpha_composite(background_image, rectangle_image)

            # Draw the text over the background image
            draw = ImageDraw.Draw(background_image)
            draw.text((message_x, message_y), line, fill="white", font=font)

            # Update the y position for the next line
            message_y = bbox_bottom + line_spacing
        # Save the generated image with a unique name for the user
        background_image.save(image_save_path)

        # Return the path to the generated image for further use
        return image_save_path



def remove_emojis(text):
            emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
            return emoji_pattern.sub(r'', text)        
#try:
#    generate_image(background_url, member_name,message, avatar_url)
#except Exception as e:
#    print("An error occurred:", e)
resource = resources()