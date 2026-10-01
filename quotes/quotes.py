import pandas as pd
import random
from pathlib import Path
from PIL import ImageFont, ImageDraw, Image
from matplotlib import font_manager

#put the correct directories here
QUOTES_DIR = Path(__file__).resolve().parent
directory_img = QUOTES_DIR / "images" / "background.png"
directory_output = QUOTES_DIR / "images" / "quote.png"
quote_directory = QUOTES_DIR / "quotes.csv"

quotes=pd.read_csv(quote_directory)
quote,name=[quotes["Quote"],quotes["name"]]

def text_wrap(text, font, max_width):
 
        lines = []
        
        # If the text width is smaller than the image width, then no need to split
        # just add it to the line list and return
        if font.getsize(text)[0]  <= max_width:
            lines.append(text)
        else:
            #split the line by spaces to get words
            words = text.split(' ')
            i = 0
            # append every word to a line while its width is shorter than the image width
            while i < len(words):
                line = ''
                while i < len(words) and font.getsize(line + words[i])[0] <= max_width:
                    line = line + words[i]+ " "
                    i += 1
                if not line:
                    line = words[i]
                    i += 1
                lines.append(line)
        return lines

def make_image(size=80):
    index=random.randint(0,len(name)-1)
    string=f'"{quote[index].capitalize()}"~{name[index].title()}'
    with Image.open(directory_img) as img:
        w, h = img.size
        font = font_manager.FontProperties(family='sans-serif', style='italic', weight='ultralight')
        file = font_manager.findfont(font)        
        font = ImageFont.truetype(file, size)
        # Call draw Method to add 2D graphics in an image
        I1 = ImageDraw.Draw(img)          
        lines = text_wrap(string, font, w*0.8)      
        
        for i,line in enumerate(lines):
            textwidth, textheight = I1.textsize(line, font=font)
            distance=90
            dy=0.5*(len(lines)-1)*distance  
            I1.text((w/2-textwidth/2,h/2-textheight/2+i*distance-dy), line.center(len(line)),font=font, fill=(0, 0, 0))
              
        #img.show()
        img.save(directory_output)
make_image()
