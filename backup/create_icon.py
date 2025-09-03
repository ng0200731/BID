# -*- coding: utf-8 -*-
"""
Create a simple app icon for the executable
Generates a basic icon with app initials
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    import os
    
    def create_app_icon():
        """Create a simple app icon"""
        
        # Create a 256x256 image with blue background
        size = 256
        img = Image.new('RGB', (size, size), color='#007bff')
        draw = ImageDraw.Draw(img)
        
        # Try to use a system font, fallback to default
        try:
            font = ImageFont.truetype("arial.ttf", 120)
        except:
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 120)
            except:
                font = ImageFont.load_default()
        
        # Draw "BID" text in white
        text = "BID"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        
        draw.text((x, y), text, fill='white', font=font)
        
        # Add a border
        draw.rectangle([0, 0, size-1, size-1], outline='#0056b3', width=8)
        
        # Save as ICO file
        img.save('app_icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
        print("✅ Created app icon: app_icon.ico")
        
        return True
        
    if __name__ == '__main__':
        create_app_icon()
        
except ImportError:
    print("⚠️ PIL/Pillow not available. Skipping icon creation.")
    print("💡 You can manually create app_icon.ico or remove icon reference from spec file.")
