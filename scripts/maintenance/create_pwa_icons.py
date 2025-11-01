#!/usr/bin/env python3
"""
Create PWA icons for the portfolio site
This script creates placeholder icons in required sizes for PWA functionality
"""

import os

from PIL import Image, ImageDraw, ImageFont


def create_icon(size, output_path, text="P"):
    """Create a simple PWA icon with given size"""
    # Create image with dark background
    img = Image.new("RGBA", (size, size), color=(15, 23, 42, 255))  # #0f172a
    draw = ImageDraw.Draw(img)

    # Try to load a font, fallback to default if not available
    try:
        # Use a larger font size proportional to the icon size
        font_size = size // 3
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Get text size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center the text
    x = (size - text_width) // 2
    y = (size - text_height) // 2

    # Draw the text in brand color
    draw.text((x, y), text, font=font, fill=(230, 197, 71, 255))  # #e6c547

    # Add a subtle border
    border_width = max(1, size // 64)
    draw.rectangle(
        [0, 0, size - 1, size - 1], outline=(230, 197, 71, 128), width=border_width
    )

    # Save the image
    img.save(output_path, "PNG")
    print(f"Created {output_path} ({size}x{size})")


def main():
    """Create all required PWA icons"""
    # Ensure the images directory exists
    images_dir = "static/images"
    os.makedirs(images_dir, exist_ok=True)

    # Required PWA icon sizes
    sizes = [
        (192, "favicon-192x192.png"),
        (512, "favicon-512x512.png"),
        (16, "favicon-16x16.png"),
        (32, "favicon-32x32.png"),
        (72, "badge-72x72.png"),  # For notifications badge
        (144, "icon-144x144.png"),  # Additional PWA size
        (180, "icon-180x180.png"),  # Apple touch icon
    ]

    for size, filename in sizes:
        output_path = os.path.join(images_dir, filename)
        create_icon(size, output_path)

    print("\n✅ All PWA icons created successfully!")
    print("Icons created in static/images/:")
    for _, filename in sizes:
        print(f"  - {filename}")


if __name__ == "__main__":
    main()
