from PIL import Image

img = Image.open("grass_0.png")
img = img.resize((370, 80))
img.save("grass_0.png")
