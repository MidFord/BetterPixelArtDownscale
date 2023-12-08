from PIL import Image, ImageFilter
import cv2
import numpy as np
#from IPython.display import Image as imh, display
import random
import colorsys
import math
def pillow_to_cv2(imagen_pillow):
    # Convertir la imagen de Pillow a un arreglo NumPy
    imagen_np = np.array(imagen_pillow)

    # Convertir la imagen a formato BGR (OpenCV utiliza BGR en lugar de RGB)
    imagen_bgr = cv2.cvtColor(imagen_np, cv2.COLOR_RGBA2BGR)

    # Convertir la imagen BGR a formato RGBA (OpenCV utiliza BGR en lugar de RGB)
    imagen_cv2 = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGBA)

    return imagen_cv2
def cv2_to_pillow(imagen_cv2):
    # Verificar si la imagen es RGBA
    if imagen_cv2.shape[2] != 4:
        raise ValueError("La imagen no es RGBA.")

    # Convertir la imagen de OpenCV a Pillow
    imagen_pillow = Image.fromarray(cv2.cvtColor(imagen_cv2, cv2.COLOR_BGR2RGBA))

    return imagen_pillow

def rgba_to_rgb(color):
  r,g,b,a = color
  return r, g, b

def rgb_to_hsl(color):
  r,g,b = color
  # Normaliza los valores RGB al rango [0, 1]
  r /= 255.0
  g /= 255.0
  b /= 255.0

  # Convierte RGB a HSL
  h, l, s = colorsys.rgb_to_hsv(r, g, b)

  # Escala los valores de HSL al rango [0, 1]
  h = round(round(h, 2)*359)
  s = math.ceil(round(s, 2)*255)
  l = math.ceil(round(l, 2)*255)

  return h, l, s
def rgba_to_hsl(color):
  r,g,b = rgba_to_rgb(color)
  # Normaliza los valores RGB al rango [0, 1]
  r /= 255.0
  g /= 255.0
  b /= 255.0

  # Convierte RGB a HSL
  h, l, s = colorsys.rgb_to_hsv(r, g, b)

  # Escala los valores de HSL al rango [0, 1]
  h = round(round(h, 2)*359)
  s = math.ceil(round(s, 2)*255)
  l = math.ceil(round(l, 2)*255)

  return h, l, s
def Clamp(value, mini, maxi):
  return max(mini, min(value, maxi))
def getPixelClamped(imagen, x, y):
  if (x >= imagen.width or y >= imagen.height or x < 0 or y <0):
    return imagen.getpixel((Clamp(x,0,imagen.width), Clamp(y,0,imagen.height)))
  else:
    return imagen.getpixel((Clamp(x,0,imagen.width), Clamp(y,0,imagen.height)))
def getPixelZero(imagen, x, y):
  if (x >= imagen.width or y >= imagen.height or x < 0 or y < 0):
    #print("pixel At ("+str(x)+","+str(y)+") exeded range.")
    return 0,0,0,0
  else:
    return imagen.getpixel((Clamp(x,0,imagen.width), Clamp(y,0,imagen.height)))
def TuppleToList(tupple):
  a, b, c = tupple
  return [a,b,c]
def indexByDirection(x ,y):
  if (x == 0 and y == -1):
    return 0
  elif (x == 0 and y == 1):
    return 1
  elif (x == -1 and y == 0):
    return 2
  elif (x == 1 and y == 0):
    return 3
  elif (x == -1 and y == -1):
    return 4
  elif (x == 1 and y == -1):
    return 5
  elif (x == -1 and y == 1):
    return 6
  elif (x == 1 and y == 1):
    return 7
  else:
    return -1
def pixelIsBorder(pixel):
  r,g,b,a = pixel
  return (a > 0)
def IdentifyDirection(imagen, x, y, prefered=(-1,-1), lastdirection=(0,0)):
  xl, yl = lastdirection
  xp, yp = prefered
  directionPrefered = indexByDirection(xp,yp)
  directionLast = indexByDirection(xl, yl)
  collidables = []
  collidables.append([pixelIsBorder(getPixelZero(imagen, x, y-1)),0,-1]) # Top = 0
  collidables.append([pixelIsBorder(getPixelZero(imagen, x, y+1)),0,1]) # Down = 1
  collidables.append([pixelIsBorder(getPixelZero(imagen, x-1, y)),-1,0]) # Left = 2
  collidables.append([pixelIsBorder(getPixelZero(imagen, x+1, y)),1,0]) # Right = 3
  collidables.append([pixelIsBorder(getPixelZero(imagen, x-1, y-1)),-1,-1]) # Top Left = 4
  collidables.append([pixelIsBorder(getPixelZero(imagen, x+1, y-1)),1,-1]) # Top Right = 5
  collidables.append([pixelIsBorder(getPixelZero(imagen, x-1, y+1)),-1,1]) # Down Left = 6
  collidables.append([pixelIsBorder(getPixelZero(imagen, x+1, y+1)),1,1]) # Down Right = 7
  if (directionPrefered != -1 and (directionPrefered < 4)):
    if (collidables[directionPrefered][0]):
      return collidables[directionPrefered][1], collidables[directionPrefered][2]
    collidables.pop(directionPrefered)
  for i in range(len(collidables)):
    collide = collidables[i]
    if (collide[0]):
      return collide[1], collide[2]
  return 0, 0
def identifyBorder(imagen,debugl=False):
  edges = []
  lastdirection = 0, 0
  for y in range(imagen.height):
    for x in range(imagen.width):
      pixel = getPixelZero(imagen,x, y)
      if (pixelIsBorder(pixel)):
        if (debugl):
          print("Edge #"+str(len(edges)+1)+" Detected AT ("+str(x)+","+str(y)+")")
        startX, startY = x, y
        imagen.putpixel((startX,startY),(0,0,0,0))
        current_edge = []
        directionx, directiony = IdentifyDirection(imagen, x ,y, (0,0))
        if (not (directionx == 0 and directiony == 0)):
          while (not (directionx == 0 and directiony == 0)):
            if (debugl):
              print("   Edge #"+str(len(edges)+1)+" AT ("+str(startX)+","+str(startY)+") has direction to ("+str(directionx)+","+str(directiony)+")")
            imagen.putpixel((startX,startY),(0,0,0,0))
            current_edge.append([startX, startY])
            startX += directionx
            startY += directiony
            directionx, directiony = IdentifyDirection(imagen, startX ,startY, (directionx,directiony), (-directionx,-directiony))

          current_edge.append([startX, startY])
          imagen.putpixel((startX,startY),(0,0,0,0))
          edges.append(current_edge)
        else:
            if (debugl):
              print("   Edge #"+str(len(edges)+1)+" AT ("+str(x)+","+str(y)+") not detected direction")
  if (debugl):
    print("\n Ended Succesfully with (",len(edges),") edges finded.")
  return edges

def Magnitude(a, b):
  return math.sqrt((a*a)+(b*b))
def getMagnitudes(values, index):
  output = Magnitude(values[0][index], values[1][index])
  for i in range(len(values)):
    if (i > 1):
      output = Magnitude(output, values[i][index])
  return output
def getPromediate(values, index):
  output = 0
  for value in values:
    output += value[index]
  output /= len(values)
  return output
def getAdditive(values, index):
  output = 0
  for value in values:
    output += value[index]
  return output



def getMagnitudes_(values):
  output = Magnitude(values[0], values[1])
  for i in range(len(values)):
    if (i > 1):
      output = Magnitude(output, values[i])
  return output
def getPromediate_(values):
  output = 0
  for value in values:
    output += value
  output /= len(values)
  return output
def getMaximum(values):
  return max(values,key=lambda x:float(x))
def getMinimum(values):
  return min(values,key=lambda x:float(x))
def getAdditive_(values):
  output = 0
  for value in values:
    output += value
  return output
def colorDiferenceRGB(color, color2, operator="hsl"):
  color = TuppleToList(rgba_to_rgb(color))
  color2 = TuppleToList(rgba_to_rgb(color2))
  rd = abs(color[0]-color2[0])
  gd = abs(color[1]-color2[1])
  bd = abs(color[2]-color2[2])
  alldiff = []
  if ("r" in operator):
    alldiff += [rd]
  if ("g" in operator):
    alldiff += [gd]
  if ("h" in operator):
    alldiff += [bd]
  return alldiff
def colorDiferenceHSL(color, color2, operator="hsl"):
  color = TuppleToList(rgb_to_hsl(rgba_to_rgb(color)))
  color2 = TuppleToList(rgb_to_hsl(rgba_to_rgb(color2)))
  hd = abs(color[0]-color2[0])
  sd = abs(color[1]-color2[1])
  ld = abs(color[2]-color2[2])
  alldiff = []
  if ("h" in operator):
    alldiff += [hd]
  if ("s" in operator):
    alldiff += [sd]
  if ("l" in operator):
    alldiff += [ld]
  return alldiff
def colorDifference(color, color2):
  return getPromediate_(colorDiferenceHSL(color, color2, "hsl"))
def getColorDiferenceAtribute(color, color2, index=0):
  color = TuppleToList(color)
  color2 = TuppleToList(color2)
  return color[index]-color2[index]
def getColorDiferenceAtribute_abs(color, color2, index=0,hasp=False):
  color = TuppleToList(color)
  color2 = TuppleToList(color2)
  if (hasp):
    print("     ",color, color2, " =",color[index]-color2[index])
  return color[index]-color2[index]
def IdentifyEdgeDirection(imagen, x, y, prefered=(-1,-1), lastdirection=(0,0), diffumbral=20, lightumbral=20,debugl=False):
  current_pixel = imagen.getpixel((x, y))
  xl, yl = lastdirection
  xp, yp = prefered
  directionPrefered = indexByDirection(xp,yp)
  directionLast = indexByDirection(xl, yl)
  colordiferences = []
  collidables = []
  collidables.append([pixelIsBorder(getPixelZero(imagen, x, y-1)),colorDifference(current_pixel,getPixelZero(imagen, x, y-1)),0,-1]) # Top = 0
  collidables.append([pixelIsBorder(getPixelZero(imagen, x, y+1)),colorDifference(current_pixel,getPixelZero(imagen, x, y+1)),0,1]) # Down = 1
  collidables.append([pixelIsBorder(getPixelZero(imagen, x-1, y)),colorDifference(current_pixel,getPixelZero(imagen, x-1, y)),-1,0]) # Left = 2
  collidables.append([pixelIsBorder(getPixelZero(imagen, x+1, y)),colorDifference(current_pixel,getPixelZero(imagen, x+1, y)),1,0]) # Right = 3
  collidables.append([pixelIsBorder(getPixelZero(imagen, x-1, y-1)),colorDifference(current_pixel,getPixelZero(imagen, x-1, y-1)),-1,-1]) # Top Left = 4
  collidables.append([pixelIsBorder(getPixelZero(imagen, x+1, y-1)),colorDifference(current_pixel,getPixelZero(imagen, x+1, y-1)),1,-1]) # Top Right = 5
  collidables.append([pixelIsBorder(getPixelZero(imagen, x-1, y+1)),colorDifference(current_pixel,getPixelZero(imagen, x-1, y+1)),-1,1]) # Down Left = 6
  collidables.append([pixelIsBorder(getPixelZero(imagen, x+1, y+1)),colorDifference(current_pixel,getPixelZero(imagen, x+1, y+1)),1,1]) # Down Right = 7


  colordiferences.append(getColorDiferenceAtribute_abs(rgba_to_hsl(current_pixel),rgba_to_hsl(getPixelZero(imagen, x, y-1)),2)) # Top = 0
  colordiferences.append(getColorDiferenceAtribute_abs(rgba_to_hsl(current_pixel),rgba_to_hsl(getPixelZero(imagen, x, y+1)),2)) # Down = 1
  colordiferences.append(getColorDiferenceAtribute_abs(rgba_to_hsl(current_pixel),rgba_to_hsl(getPixelZero(imagen, x-1, y)),2)) # Left = 2
  colordiferences.append(getColorDiferenceAtribute_abs(rgba_to_hsl(current_pixel),rgba_to_hsl(getPixelZero(imagen, x+1, y)),2)) # Right = 3
  colordiferences.append(getColorDiferenceAtribute_abs(rgba_to_hsl(current_pixel),rgba_to_hsl(getPixelZero(imagen, x-1, y-1)),2)) # Top Left = 4
  colordiferences.append(getColorDiferenceAtribute_abs(rgba_to_hsl(current_pixel),rgba_to_hsl(getPixelZero(imagen, x+1, y-1)),2)) # Top Right = 5
  colordiferences.append(getColorDiferenceAtribute_abs(rgba_to_hsl(current_pixel),rgba_to_hsl(getPixelZero(imagen, x-1, y+1)),2)) # Down Left = 6
  colordiferences.append(getColorDiferenceAtribute_abs(rgba_to_hsl(current_pixel),rgba_to_hsl(getPixelZero(imagen, x+1, y+1)),2)) # Down Right = 7
  maximumLightDifference = -getMinimum(colordiferences)
  lightBool = (maximumLightDifference >= lightumbral) and (TuppleToList(rgba_to_hsl(current_pixel))[2] < maximumLightDifference)
  if (debugl):
    print("Light Maximum Difference =",maximumLightDifference, lightumbral)
  if (directionPrefered != -1 and (directionPrefered < 4)):
    if (collidables[directionPrefered][0] and lightBool):
      if (collidables[directionPrefered][1] < diffumbral):
        return collidables[directionPrefered][2], collidables[directionPrefered][3]
    collidables.pop(directionPrefered)
  else:
        if (debugl):
          print("References",collidables[directionPrefered][1], diffumbral, maximumLightDifference)
  for i in range(len(collidables)):
    collide = collidables[i]
    if (collide[0] and lightBool):
      if (collide[1] < diffumbral):
        return collide[2], collide[3]
      else:
        if (debugl):
          print("References",collide[1], diffumbral, maximumLightDifference)
  return 0, 0
def identifyEdge(imagen, diffumbral=20, lightumbral=20,debugl=False):
  #edges_image = Image.new(imagen.mode,(imagen.width,imagen.height),(0,0,0,0))
  edges = []
  lastdirection = 0, 0
  for y in range(imagen.height):
    for x in range(imagen.width):
      pixel = imagen.getpixel((x, y))
      if (pixelIsBorder(pixel)):
        if (debugl):
          print("Edge #"+str(len(edges)+1)+" Detected AT ("+str(x)+","+str(y)+")")
        startX, startY = x, y
        #imagen.putpixel((startX,startY),(0,0,0,0))
        current_edge = []
        directionx, directiony = IdentifyEdgeDirection(imagen, x ,y, (0,0), (0,0), diffumbral,lightumbral,debugl)
        if (not (directionx == 0 and directiony == 0)):
          while (not (directionx == 0 and directiony == 0)):
            if (debugl):
              print("   Edge #"+str(len(edges)+1)+" AT ("+str(startX)+","+str(startY)+") has direction to ("+str(directionx)+","+str(directiony)+")")
            imagen.putpixel((startX,startY),(0,0,0,0))
            current_edge.append([startX, startY])
            startX += directionx
            startY += directiony
            directionx, directiony = IdentifyEdgeDirection(imagen, startX ,startY, (directionx,directiony), (-directionx,-directiony), diffumbral,lightumbral,debugl)

          current_edge.append([startX, startY])
          imagen.putpixel((startX,startY),(0,0,0,0))
          edges.append(current_edge)
        else:
          pass
          #print("   Edge #"+str(len(edges)+1)+" AT ("+str(x)+","+str(y)+") not detected direction")
  print("\n Ended Succesfully with (",len(edges),") edges finded.")
  return edges
def visualizeEdges(imagen, edges):
  edges_image = Image.new(imagen.mode,(imagen.width,imagen.height),(0,0,0,0))
  for i in range(len(edges)):
    edge = edges[i]
    color_value = random.randint(0,255), random.randint(0,255), random.randint(0,255), 255
    for edgeValue in edge:
      edges_image.putpixel((edgeValue[0],edgeValue[1]),color_value)
  return edges_image
def getRoundedPixels(imagen, x, y):
  roundedpixels = []
  roundedpixels.append(TuppleToList(rgb_to_hsl(rgba_to_rgb(getPixelZero(imagen,x-1,y-1)))))
  roundedpixels.append(TuppleToList(rgb_to_hsl(rgba_to_rgb(getPixelZero(imagen,x,y-1)))))
  roundedpixels.append(TuppleToList(rgb_to_hsl(rgba_to_rgb(getPixelZero(imagen,x+1,y-1)))))
  roundedpixels.append(TuppleToList(rgb_to_hsl(rgba_to_rgb(getPixelZero(imagen,x-1,y)))))
  roundedpixels.append(TuppleToList(rgb_to_hsl(rgba_to_rgb(getPixelZero(imagen,x-1,y+1)))))
  roundedpixels.append(TuppleToList(rgb_to_hsl(rgba_to_rgb(getPixelZero(imagen,x,y+1)))))
  roundedpixels.append(TuppleToList(rgb_to_hsl(rgba_to_rgb(getPixelZero(imagen,x+1,y+1)))))
  roundedpixels.append(TuppleToList(rgb_to_hsl(rgba_to_rgb(getPixelZero(imagen,x+1,y)))))
  hue = getMagnitudes(roundedpixels, 0)
  sat = getMagnitudes(roundedpixels, 1)
  lig = getMagnitudes(roundedpixels, 2)
  return [hue, sat, lig]


def getEdges(imagen_path, umbral=1.0,difmod=(1,1,1)):
  imagen = Image.open(imagen_path)
  edges_image = Image.new(imagen.mode,(imagen.width,imagen.height),(0,0,0,0))
  for y in range(imagen.height):
    for x in range(imagen.width):
      r,g,b,a = imagen.getpixel((x,y))
      hslpixel = TuppleToList(rgb_to_hsl(rgba_to_rgb((r,g,b,a))))
      color_rounded = getRoundedPixels(imagen, x, y)
      hm, sm, lm = difmod
      hue_diff = abs(color_rounded[0]-hslpixel[0])
      sat_diff = abs(color_rounded[1]-hslpixel[1])
      lig_diff = abs(color_rounded[2]-hslpixel[2])
      diffmagnitude = (hue_diff*hm)+(sat_diff*sm)+(lig_diff*lm)
      if (diffmagnitude < umbral):
        edges_image.putpixel((x,y),(0,0,0,a))
  return edges_image





def encontrar_bordes_pixel_art(imagen, umbral_bordes=1.0, center_umbral=0.0,sharp_radius=2,factor_nitidez=2, others=(1,0)):
    # Abrir la imagen
    # Cargar la imagen
    #imagen = cv2.imread(imagen_path, cv2.IMREAD_GRAYSCALE)


    #imagen = Image.open(imagen_path)

    # Aplicar el filtro de nitidez
    imagen_nitida = imagen.filter(ImageFilter.UnsharpMask(radius=sharp_radius, percent=factor_nitidez))
    # Aplicar el filtro Canny para encontrar bordes
    #bordes = cv2.Canny(pillow_to_cv2(imagen), umbral_bordes, center_umbral)
    #bordes = cv2.cvtColor(bordes, cv2.COLOR_GRAY2RGBA)
    # Devolver la imagen con los bordes resaltados
    #bordes = cv2_to_pillow(bordes)
    # Convertir la imagen a escala de grises
    imagen_grises = imagen_nitida.convert("RGBA")

    # Aplicar el filtro de bordes personalizado controlando el umbral
    #bordes = imagen_grises.point(lambda p: p > umbral_bordes and 255)


    # Aplicar el filtro de detección de bordes

    oe, of = others
    bordes = imagen_grises.filter(ImageFilter.Kernel((3, 3), (-1*umbral_bordes, -1*umbral_bordes, -1*umbral_bordes, -1*umbral_bordes, 8+center_umbral, -1*umbral_bordes, -1*umbral_bordes, -1*umbral_bordes, -1*umbral_bordes), oe, of))
    #bordes = imagen_grises.filter(ImageFilter.FIND_EDGES)
    bordes = bordes.convert("RGBA")
    for y in range(bordes.height):
      for x in range(bordes.width):
        pixel1 = imagen.getpixel((x,y))
        pixel = bordes.getpixel((x,y))
        r,g,b,a = pixel
        r1,g1,b1,a1 = pixel1
        if (a > 0):
          a = 255
          r,g,b = 0,0,0
          bordes.putpixel((x,y),(r,g,b,a))
        else:
          a = 0
          bordes.putpixel((x,y),(r1,g1,b1,a))

    # Devolver la imagen con los bordes resaltados
    return bordes
def edge_detection_sobel(image_path):
    # Leer la imagen
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # Aplicar el operador Sobel
    sobel_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)

    # Normalizar la magnitud del gradiente al rango [0, 255]
    gradient_magnitude = cv2.normalize(gradient_magnitude, None, 0, 255, cv2.NORM_MINMAX)

    # Convertir a formato RGBA
    rgba_image = cv2.cvtColor(gradient_magnitude.astype(np.uint8), cv2.COLOR_GRAY2RGBA)

    return cv2_to_pillow(rgba_image)
def canny_edge_detection(image_path):
  imagen = Image.open(image_path)
  imagen = imagen.filter(ImageFilter.UnsharpMask(radius=100.0,percent=255))
  gray = imagen.convert("L")
  canny = (-1, -1, -1,
           -1, 8, -1,
           -1, -1, -1)
  lapcian = (0, 1, 0,
           1, -4, 1,
           0, 1, 0)
  sobelx = (-1, 0, 1,
            -2, 0, 2,
            -1, 0, 1)
  gray = gray.filter(ImageFilter.Kernel((3, 3), sobelx, 1, 0))
  return gray
def edge_detection_pixel_art(image_path,threshold=60):
    imagen = Image.open(image_path)
    imagen = imagen.filter(ImageFilter.UnsharpMask(radius=100,percent=30))
    img = pillow_to_cv2(imagen)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Aplica un suavizado gaussiano para reducir el ruido
    #img_blur = cv2.GaussianBlur(img_gray, (1, 1), 0)
    img_blur = img_gray

    # Calcula la diferencia de colores en ambas direcciones
    diff_x = cv2.absdiff(img_blur, np.roll(img_blur, 1, axis=1))
    diff_y = cv2.absdiff(img_blur, np.roll(img_blur, 1, axis=0))

    # Combina las diferencias en ambas direcciones
    edges = cv2.bitwise_or(diff_x, diff_y)

    # Aplica un umbral para resaltar los cambios significativos
    _, edges_binary = cv2.threshold(edges, threshold, 255, cv2.THRESH_BINARY)

    return cv2_to_pillow(cv2.cvtColor(edges_binary.astype(np.uint8), cv2.COLOR_GRAY2RGBA))
def sigmoid(x):
    """
    Función de activación sigmoide.
    """
    return 1 / (1 + math.exp(-x))

def tanh(x):
    """
    Función de activación tangente hiperbólica.
    """
    return math.tanh(x)
def simplify(value, times):
  return round(value*times)/times
def ToGrayscale(imagen, oper=0):
  for y in range(imagen.height):
    for x in range(imagen.width):
      r,g,b,a = imagen.getpixel((x,y))
      n = 0
      if (oper == 0):
        n = round(Clamp(getMagnitudes_([r/255,g/255,b/255])*255,0,255))
      elif (oper == 1):
        n = round(Clamp(getPromediate_([r/255,g/255,b/255])*255,0,255))
      elif (oper == 2):
        n = round(Clamp(sigmoid(getMagnitudes_([r/255,g/255,b/255]))*255,0,255))
      elif (oper == 3):
        n = round(Clamp(tanh(getMagnitudes_([r/255,g/255,b/255]))*255,0,255))
      imagen.putpixel((x,y),(n,n,n,a))
  return imagen
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
def CombineEdgesColors(imagen, imagen2):
  for y in range(imagen.height):
    for x in range(imagen.width):
      r2,g2,b2,a2 = imagen2.getpixel((x,y))
      r,g,b,a = imagen.getpixel((x,y))
      if (a == 0):
        imagen.putpixel((x,y),(r2,g2,b2,a2))
  return imagen
def findEdges(path):
  imagen = Image.open(path)
  #imagen = ToGrayscale(imagen,3)
  imagen_outline = encontrar_bordes_pixel_art(imagen,1.32,0.0,1,1,(1,0))
  symplyfy_imagen = SimplifyColors(imagen,2)
  inside_edges = visualizeEdges(symplyfy_imagen,identifyEdge(symplyfy_imagen,10,10))
  combined_edges = CombineEdgesColors(imagen_outline, inside_edges)
  outside_edges = identifyBorder(combined_edges)
  imagen2 = Image.open(path)
  return outside_edges, imagen2
def lerpColor2(colora, colorb, times):
  r, g, b, a = colora
  r_, g_, b_, a_ = colorb
  lerped_color = (
      int(r + (r_ - r) * times),
      int(g + (g_ - g) * times),
      int(b + (b_ - b) * times),
      int(a + (a_ - a) * times)
  )
  return lerped_color
def resizeEdges(edges, factor_x, factor_y):
  edgesDict = {}
  for i in range(len(edges)):
    edge_dict = {}
    for b in range(len(edges[i])):
      divX = math.floor(edges[i][b][0]/factor_x)
      divY = math.floor(edges[i][b][1]/factor_y)
      keyname = str(divX) + "," + str(divY)
      if (keyname in edge_dict):
        edge_dict[keyname].append([edges[i][b][0],edges[i][b][1]])
      else:
        edge_dict[keyname] = [[edges[i][b][0],edges[i][b][1]]]
    edgesDict[i] = edge_dict
  #print(edgesDict)
  return edgesDict
def imageFromEdges(image, edges, factor_x, factor_y):
  edges_image = Image.new(image.mode,(math.floor(image.width/factor_x),math.floor(image.height/factor_y)),(0,0,0,0))
  for i in range(len(list(edges.keys()))):
    positions = list(edges[i].keys())
    for b in range(len(positions)):
      position = positions[b]
      posit = position.split(",")
      x, y = int(posit[0]), int(posit[1])
      resultColor = 0, 0, 0, 0
      for c in range(len(edges[i][position])):
        nx, ny = edges[i][position][c][0], edges[i][position][c][1]
        if (c > 0):
          resultColor = lerpColor2(resultColor,image.getpixel((nx, ny)), 0.5)
          #resultColor = image.getpixel((nx, ny))
        else:
          resultColor = image.getpixel((nx, ny))
      edges_image.putpixel((x,y),resultColor)
  return edges_image
def CombineImageInCaps(image, image2):
  result_image = image.copy()
  for y in range(image.height):
    for x in range(image.width):
      r2,g2,b2,a2 = image2.getpixel((x,y))
      r,g,b,a = image.getpixel((x,y))
      if (a == 0):
        result_image.putpixel((x,y),(r2,g2,b2,a2))
  return result_image
def processImage(path,factor_x,factor_y):
  image_edges, image_result = findEdges(path)
  edg = resizeEdges(image_edges,factor_x,factor_y)
  return imageFromEdges(image_result,edg,factor_x,factor_y)
