from PIL import Image
import numpy as np
import pattern_noise as pn
import math


def clamp(num, min_value, max_value):
   return max(min(num, max_value), min_value)
def convert_image(image):
    # Convertir la imagen en un array de NumPy
    image_array = np.array(image)

    # Crear una nueva imagen con las mismas dimensiones que la original
    new_image = Image.new(image.mode, image.size)

    # Obtener las dimensiones de la imagen
    width, height = image.size

    # Recorrer todos los píxeles de la imagen original
    for x in range(width):
        for y in range(height):
            # Obtener el valor del píxel en la imagen original
            pixel_value = tuple(image_array[y, x])

            # Aplicar el valor del píxel a la nueva imagen usando putpixel
            new_image.putpixel((x, y), pixel_value)

    return new_image
    

def convert_image_size(image,sizex,sizey):
    # Convertir la imagen en un array de NumPy
    image_array = np.array(image)

    # Crear una nueva imagen con las mismas dimensiones que la original
    new_image = Image.new(image.mode, image.size)

    # Obtener las dimensiones de la imagen
    width, height = sizex,sizey

    # Recorrer todos los píxeles de la imagen original
    for x in range(width):
        for y in range(height):
            # Obtener el valor del píxel en la imagen original
            pixel_value = tuple(image_array[y, x])

            # Aplicar el valor del píxel a la nueva imagen usando putpixel
            new_image.putpixel((x, y), pixel_value)

    return new_image

def convert_image_pattern(image,xpattern,ypattern):
    # Convertir la imagen en un array de NumPy
    image_array = np.array(image)

    # Crear una nueva imagen con las mismas dimensiones que la original
    new_image = Image.new(image.mode, (len(xpattern),len(ypattern)))

    # Obtener las dimensiones de la imagen
    width, height = image.size

    # Recorrer todos los píxeles de la imagen original
    lastX = 0
    for x in range(len(xpattern)):
        
        lastY = 0
        for y in range(len(ypattern)):
            # Obtener el valor del píxel en la imagen original
            if (x == (len(xpattern)-1)):
                pixel_value = tuple(image_array[clamp(lastY,0,height-1), clamp(width-1,0,width-1)])
            elif (y == (len(ypattern)-1)):
                pixel_value = tuple(image_array[clamp(height-1,0,height-1), clamp(lastX,0,width-1)])
            else:
                pixel_value = tuple(image_array[clamp(lastY,0,height-1), clamp(lastX,0,width-1)])
            lastY += ypattern[y]
#            print(x,y," : ",lastX,lastY)
            # Aplicar el valor del píxel a la nueva imagen usando putpixel
            new_image.putpixel((x, y), pixel_value)
        
        lastX += xpattern[x]

    return new_image    
    

def simplify_palette(image,tolerance):
    # Convertir la imagen en un array de NumPy
    image_array = np.array(image)

    # Crear una nueva imagen con las mismas dimensiones que la original
    mode = str(image.mode)
    new_image = Image.new(image.mode, image.size)
    
    palette_image = Image.new(image.mode, (50,50))

    # Obtener las dimensiones de la imagen
    width, height = image.size

    # Recorrer todos los píxeles de la imagen original
    palette = []
    a = 255
    
    if (mode == "RGB"):
        for x in range(width):
            for y in range(height):
                # Obtener el valor del píxel en la imagen original
                 r,g,b = image_array[y, x]
                 color_ = [r,g,b,a]
                 if color_ not in palette:
                     outColor, indexColor = pn.identify_color(palette,color_,tolerance)
                     if (outColor):
                         color_ = palette[indexColor]
                     else:
                         palette.append(color_)
                         lx,ly = pn.square_value(len(palette)-1,50)
                         palette_image.putpixel((lx, ly), (color_[0],color_[1],color_[2]))
                 new_image.putpixel((x, y), (color_[0],color_[1],color_[2]))
    if (mode == "RGBA"):
        for x in range(width):
            for y in range(height):
                # Obtener el valor del píxel en la imagen original
                 r,g,b,a = image_array[y, x]
                 color_ = [r,g,b,a]
                 if color_ not in palette:
                     outColor, indexColor = pn.identify_color(palette,color_,tolerance)
                     if (outColor):
                         color_ = palette[indexColor]
                     else:
                         palette.append(color_)
                         lx,ly = pn.square_value(len(palette)-1,50)
                         palette_image.putpixel((lx, ly), (color_[0],color_[1],color_[2]))
                 new_image.putpixel((x, y), (color_[0],color_[1],color_[2]))
     
    palette_image.save("palette.png")
    return new_image
# Abrir la imagen original
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
#new_image.save("nueva_imagen.png")
#processImage("electrical.png",2,False).save("new_item.png")