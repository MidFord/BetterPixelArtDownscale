from PIL import Image
import pattern_noise as pn
import math


def clamp(num, min_value, max_value):
   return max(min(num, max_value), min_value)
def convert_image(image):
    new_image = Image.new(image.mode, image.size)
    width, height = image.size
    for x in range(width):
        for y in range(height):
            pixel_value = image.getpixel(x,y)
            new_image.putpixel((x, y), pixel_value)
    return new_image
    

def convert_image_size(image,width,height):
    new_image = Image.new(image.mode, image.size)
    for x in range(width):
        for y in range(height):
            pixel_value = image.getpixel((x, y))
            new_image.putpixel((x, y), pixel_value)
    return new_image

def convert_image_pattern(image,xpattern,ypattern):
    new_image = Image.new(image.mode, (len(xpattern),len(ypattern)))
    width, height = image.size
    lastX = 0
    for x in range(len(xpattern)):
        lastY = 0
        for y in range(len(ypattern)):
            if (x == (len(xpattern)-1)):
                pixel_value = image.getpixel(( clamp(width-1,0,width-1), clamp(lastY,0,height-1)))
            elif (y == (len(ypattern)-1)):
                pixel_value = image.getpixel(( clamp(lastX,0,width-1), clamp(height-1,0,height-1)))
            else:
                pixel_value = image.getpixel(( clamp(lastX,0,width-1), clamp(lastY,0,height-1)))
            lastY += ypattern[y]
            new_image.putpixel((x, y), pixel_value)
        lastX += xpattern[x]
    return new_image    

def simplify(value, times):
  return round(value*times)/times

def SimplifyColors(imagen, simplifier=8):
  simplyimage = Image.new(imagen.mode,(imagen.width,imagen.height),(0,0,0,0))
  for y in range(simplyimage.height):
    for x in range(simplyimage.width):
      r,g,b,a = imagen.getpixel((x,y))
      r = round(simplify(r/255,simplifier)*255)
      g = round(simplify(g/255,simplifier)*255)
      b= round(simplify(b/255,simplifier)*255)
      simplyimage.putpixel((x,y),(r,g,b,a))
  return imagen

def processImage(pathto,scaleMultiplierX,scaleMultiplierY,simplify=False,simplifyPixel=8):
    image = Image.open(pathto)
    width, height = image.size
    newWidth = math.floor(width/scaleMultiplierX)
    newHeight = math.floor(height/scaleMultiplierY)
    dividerx = width/newWidth
    dividery = height/newHeight
    new_image = 0
    if (dividerx < 1.5 or dividery < 1.5):
        new_image = convert_image_size(image,newWidth, newHeight)
    else:
        xPattern = pn.create_pattern(width,newWidth)
        yPattern = pn.create_pattern(height,newHeight)
        new_image = convert_image_pattern(image,xPattern,yPattern)
        if simplify:
            new_image = SimplifyColors(new_image,simplifyPixel)
    return new_image
