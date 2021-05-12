from PIL import Image, ImageDraw, ImageFont
import numpy as np
import math
from image_db import ImageDatabase

def drawWrappedText(image, text, bbox, font):
    draw = ImageDraw.Draw(image)
    line = ""
    test_line = ""
    offset = 0
    for word in text.split(" "):
        test_line += word + " "
        if (draw.textlength(test_line, font=font) > bbox[2]):
            draw.text((bbox[0], bbox[1] + offset), line, font=font, fill=(0,0,0))
            offset += draw.textsize(text, font=font)[1]
            if (offset + draw.textsize(text, font=font)[1] > bbox[3]):
                break
            test_line = word + " "
        line = test_line
    draw.text((bbox[0], bbox[1] + offset), line, font=font, fill=(0,0,0))

class Overlay:
    def __init__(self):
        self.overlays = []
        self.components = {}
        self.font = ImageFont.truetype("C:\Windows\Fonts\Arial.ttf", 24)
    
    def clear(self):
        self.overlays = []
        self.components = {}

    def image(self, name, database, position, size):
        if (name not in self.components.keys()):
            row = database.load_row(name)
            self.components[name] = [row['description'], 1]
        else:
            self.components[name][1]+=1
        self.last_image_position = position
        self.overlays.append(OverlayImage(name, database, position, size))
    
    def arrow(self, end_position):
        self.overlays.append(OverlayArrow(self.last_image_position, end_position))
    
    def draw(self, base):
        temp = base.copy()
        base = Image.new(mode="RGB", size=(temp.size[0], 2*(temp.size[1])), color=(255,255,255))
        base.paste(temp, (0,0))
        for overlay in self.overlays:
            overlay.draw(base)
        for i, component in enumerate(self.components.items()):
            drawWrappedText(base, f"{component[1][1]}x {component[0]}: {component[1][0]}", (int(i*temp.size[0]/len(self.components.items())), temp.size[1], int(temp.size[0]/len(self.components.items())), temp.size[1]), self.font)
        return base

class OverlayImage:
    def __init__(self, name, database, position, size):
        self.position = position
        image = database.load_pil_image(name).convert("RGBA")
        self.image = image.resize((int(size), int(size*(image.size[1]/image.size[0]))))

    def draw(self, base):
        base.paste(self.image, (int(self.position[0]-self.image.size[0]/2), int(self.position[1]-self.image.size[1]/2)), self.image)

class OverlayArrow:
    def __init__(self, start_position, end_position):
        self.start_position = start_position
        self.end_position = end_position

    def draw(self, base):
        draw = ImageDraw.Draw(base)
        draw.line([self.start_position, self.end_position], fill=(255,0,0), width=2)
        vec = np.array(self.end_position) - np.array(self.start_position)
        dist = np.linalg.norm(vec)
        unit_vec = vec / dist
        dot = np.dot(unit_vec, [1,0])
        angle = np.arccos(dot)
        draw.line([self.end_position, tuple(np.array(self.end_position) + -0.125*dist*np.array((math.cos(angle-0.4), math.sin(angle-0.4))))], fill=(255,0,0), width=2)
        draw.line([self.end_position, tuple(np.array(self.end_position) + -0.125*dist*np.array((math.cos(angle+0.4), math.sin(angle+0.4))))], fill=(255,0,0), width=2)

if __name__ == '__main__':
    img = Image.open("test.png")
    imdb = ImageDatabase("database.db")
    overlay = Overlay()
    overlay.image("camera", imdb, (500, 250), 100)
    overlay.arrow((400, 400))
    overlay.image("camera", imdb, (350, 250), 50)
    overlay.arrow((400, 400))
    overlay.image("keypad", imdb, (100, 100), 100)
    overlay.arrow((400, 400))
    overlay.arrow((300, 500))
    overlay.draw(img).show()