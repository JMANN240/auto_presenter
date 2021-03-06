import sqlite3
import io
from PIL import Image
from base64 import b64encode, b64decode

class ImageDatabase:
    def __init__(self, filename):
        self.filename = filename

    def row_dictionary(self, db_row):
        return {key: value for key, value in zip(db_row.keys(), db_row)}

    def reset_table(self):
        with sqlite3.connect(self.filename) as connection:
            cursor = connection.cursor()
            cursor.execute('''DROP TABLE IF EXISTS images''')
            cursor.execute('''CREATE TABLE images (name TEXT UNIQUE NOT NULL, image BYTES NOT NULL, description TEXT)''')

    def save_row(self, name, img_bytes, description=""):
        with sqlite3.connect(self.filename) as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO images VALUES (?, ?, ?)", (name.lower(), img_bytes.decode("utf-8"), description))
            connection.commit()
    
    def load_row(self, name):
        with sqlite3.connect(self.filename) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM images WHERE name=?', (name,))
            db_row = cursor.fetchone()
            return self.row_dictionary(db_row)
        
    def load_all_rows(self):
        with sqlite3.connect(self.filename) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM images')
            return [self.row_dictionary(db_row) for db_row in cursor.fetchall()]
    
    def delete_row(self, name):
        with sqlite3.connect(self.filename) as connection:
            cursor = connection.cursor()
            cursor.execute('DELETE FROM images WHERE name=?', (name,))
            connection.commit()

    def save_pil_image(self, name, image, description=""):
        stream = io.BytesIO()
        image.save(stream, format="PNG")
        img_bytes = b64encode(stream.getvalue())
        self.save_row(name, img_bytes, description)
            
    def load_pil_image(self, name):
        return Image.open(io.BytesIO(b64decode(self.load_row(name)['image'])))

if (__name__ == '__main__'):
    imagesDB = ImageDatabase('database.db')
    imagesDB.reset_table()
    camera = Image.open("static/camera.png").convert("RGBA")
    imagesDB.save_pil_image("MCP1", camera, "The MCP1 Security Camera is the optimal solution for all of your security needs. With a 180 degree field of view and IP capabilities this is the best camera for the modern business owner.")
    keypad = Image.open("static/keypad.png").convert("RGBA")
    imagesDB.save_pil_image("KP3000", keypad, "The KP3000 has comfortable silicone pads and includes extra symbols for extra security. This is made of titanium and is impossible to break.")