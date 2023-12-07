from PIL import Image, ImageFilter
import numpy as np
import random
import colorsys
import math

#Custom Math
def Clamp(value, mini, maxi):
  return max(mini, min(value, maxi))

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def tanh(x):
    return math.tanh(x)

def TuppleToList(tupple):
  a, b, c = tupple
  return [a,b,c]

def simplify(value, times):
  return round(value*times)/times

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

#Color Math
def colorDifference(color, color2):
  return getPromediate_(colorDiferenceHSL(color, color2, "hsl"))

def rgba_to_rgb(color):
  r,g,b,a = color
  return r, g, b

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

def rgb_to_hsl(color):
  r,g,b = color
  r /= 255.0
  g /= 255.0
  b /= 255.0
  h, l, s = colorsys.rgb_to_hsv(r, g, b)
  h = round(round(h, 2)*359)
  s = math.ceil(round(s, 2)*255)
  l = math.ceil(round(l, 2)*255)

  return h, l, s

def rgba_to_hsl(color):
  r,g,b = rgba_to_rgb(color)
  r /= 255.0
  g /= 255.0
  b /= 255.0
  h, l, s = colorsys.rgb_to_hsv(r, g, b)
  h = round(round(h, 2)*359)
  s = math.ceil(round(s, 2)*255)
  l = math.ceil(round(l, 2)*255)


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

#Pixel Math
def getPixelClamped(image, x, y):
  """
  Receives (image) as the main image and (x, y) as the pixel position.
  Gets the pixel at the specified position, if the position exceeds the image boundaries, the position is limited to the image boundaries.
  """
  if (x >= image.width or y >= image.height or x < 0 or y <0):
    return image.getpixel((Clamp(x,0,image.width), Clamp(y,0,image.height)))
  else:
    return image.getpixel((Clamp(x,0,image.width), Clamp(y,0,image.height)))

def getPixelZero(image, x, y):
  """
  Receives (image) as the main image and (x, y) as the pixel position.
  Gets the pixel at the specified position, if the position exceeds the image boundaries, the returned pixel will be just an RGBA value (0,0,0,0,0).
  """
  if (x >= image.width or y >= image.height or x < 0 or y < 0):
    return 0,0,0,0
  else:
    return image.getpixel((Clamp(x,0,image.width), Clamp(y,0,image.height)))

  return h, l, s

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

#Edge Math
def pixelIsNotTransparent(pixel):
  """
  If the alpha value of the indicated colour is greater than 0.
  """
  r,g,b,a = pixel
  return (a > 0)

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

def IdentifyDirection(image, x, y, prefered=(-1,-1), lastdirection=(0,0)):
  """
  It receives (image) as the image, (x, y) as the pixel position, (preferred) indicates the default preferred direction 
  is (-1,-1) i.e. Top Left, and (lastdirection) as the previous direction.
  Evaluate the pixels surrounding the pixel at the specified position, evaluate if they are not transparent, 
  then evaluate first the pixel in the preferred direction (in case it is not 0,0), and the rest of the pixels, 
  the first pixel that is not transparent, will cause the function to return its surrounding position, which is the direction.
  """
  xl, yl = lastdirection
  xp, yp = prefered
  directionPrefered = indexByDirection(xp,yp)
  directionLast = indexByDirection(xl, yl)
  collidables = []
  collidables.append([pixelIsNotTransparent(getPixelZero(image, x, y-1)),0,-1]) # Top = 0
  collidables.append([pixelIsNotTransparent(getPixelZero(image, x, y+1)),0,1]) # Down = 1
  collidables.append([pixelIsNotTransparent(getPixelZero(image, x-1, y)),-1,0]) # Left = 2
  collidables.append([pixelIsNotTransparent(getPixelZero(image, x+1, y)),1,0]) # Right = 3
  collidables.append([pixelIsNotTransparent(getPixelZero(image, x-1, y-1)),-1,-1]) # Top Left = 4
  collidables.append([pixelIsNotTransparent(getPixelZero(image, x+1, y-1)),1,-1]) # Top Right = 5
  collidables.append([pixelIsNotTransparent(getPixelZero(image, x-1, y+1)),-1,1]) # Down Left = 6
  collidables.append([pixelIsNotTransparent(getPixelZero(image, x+1, y+1)),1,1]) # Down Right = 7
  if (directionPrefered != -1 and (directionPrefered < 4)):
    if (collidables[directionPrefered][0]):
      return collidables[directionPrefered][1], collidables[directionPrefered][2]
    collidables.pop(directionPrefered)
  for i in range(len(collidables)):
    collide = collidables[i]
    if (collide[0]):
      return collide[1], collide[2]
  return 0, 0

def identifyIndividualEdges(image,debugl=False):
  """
  It takes an RGBA image and evaluates its connected edges and returns them.
  """
  edges = []
  lastdirection = 0, 0
  for y in range(image.height):
    for x in range(image.width):
      pixel = getPixelZero(image,x, y)
      if (pixelIsNotTransparent(pixel)):
        if (debugl):
          print("Edge #"+str(len(edges)+1)+" Detected AT ("+str(x)+","+str(y)+")")
        startX, startY = x, y
        image.putpixel((startX,startY),(0,0,0,0))
        current_edge = []
        directionx, directiony = IdentifyDirection(image, x ,y, (0,0))
        if (not (directionx == 0 and directiony == 0)):
          while (not (directionx == 0 and directiony == 0)):
            if (debugl):
              print("   Edge #"+str(len(edges)+1)+" AT ("+str(startX)+","+str(startY)+") has direction to ("+str(directionx)+","+str(directiony)+")")
            image.putpixel((startX,startY),(0,0,0,0))
            current_edge.append([startX, startY])
            startX += directionx
            startY += directiony
            directionx, directiony = IdentifyDirection(image, startX ,startY, (directionx,directiony), (-directionx,-directiony))

          current_edge.append([startX, startY])
          image.putpixel((startX,startY),(0,0,0,0))
          edges.append(current_edge)
        else:
            if (debugl):
              print("   Edge #"+str(len(edges)+1)+" AT ("+str(x)+","+str(y)+") not detected direction")
  if (debugl):
    print("\n Ended Succesfully with (",len(edges),") edges findedged.")
  return edges

def IdentifyEdgeDirection(image, x, y, prefered=(-1,-1), lastdirection=(0,0), diff_threshold=20, light_threshold=20, debugl=False):
  """
  It receives (image) as the image, (x, y) as the pixel position, 
  (preferred) indicates the preferred direction default is (-1,-1) i.e. Top Left, 
  and (lastdirection) as the previous direction, it also receives 
  (diff_threshold) which indicates the threshold of difference between pixels to be considered as an edge, 
  (light_threshold) which indicates the threshold of difference in brightness between pixels to be considered as an edge.
  It evaluates the pixels surrounding the pixel at the specified position, evaluates if they are not transparent, 
  then evaluates first the pixel in the preferred direction (in case it is not 0,0), and the rest of the pixels, 
  the first pixel that is not transparent, will make the function evaluate the difference between the central pixel and the neighbouring pixel, 
  and depending on the specified thresholds will evaluate if it is an edge connection or not, if so, returns the direction of the connection.
  """
  current_pixel = image.getpixel((x, y))
  xl, yl = lastdirection
  xp, yp = prefered
  directionPrefered = indexByDirection(xp,yp)
  directionLast = indexByDirection(xl, yl)
  colordiferences = []
  collidables = []
  collidables.append([pixelIsNotTransparent(getPixelZero(image, x, y-1)),colorDifference(current_pixel,getPixelZero(image, x, y-1)),0,-1]) # Top = 0
  collidables.append([pixelIsNotTransparent(getPixelZero(image, x, y+1)),colorDifference(current_pixel,getPixelZero(image, x, y+1)),0,1]) # Down = 1
  collidables.append([pixelIsNotTransparent(getPixelZero(image, x-1, y)),colorDifference(current_pixel,getPixelZero(image, x-1, y)),-1,0]) # Left = 2
  collidables.append([pixelIsNotTransparent(getPixelZero(image, x+1, y)),colorDifference(current_pixel,getPixelZero(image, x+1, y)),1,0]) # Right = 3
  collidables.append([pixelIsNotTransparent(getPixelZero(image, x-1, y-1)),colorDifference(current_pixel,getPixelZero(image, x-1, y-1)),-1,-1]) # Top Left = 4
  collidables.append([pixelIsNotTransparent(getPixelZero(image, x+1, y-1)),colorDifference(current_pixel,getPixelZero(image, x+1, y-1)),1,-1]) # Top Right = 5
  collidables.append([pixelIsNotTransparent(getPixelZero(image, x-1, y+1)),colorDifference(current_pixel,getPixelZero(image, x-1, y+1)),-1,1]) # Down Left = 6
  collidables.append([pixelIsNotTransparent(getPixelZero(image, x+1, y+1)),colorDifference(current_pixel,getPixelZero(image, x+1, y+1)),1,1]) # Down Right = 7


  colordiferences.append(getColorDiferenceAtribute_abs(rgba_to_hsl(current_pixel),rgba_to_hsl(getPixelZero(image, x, y-1)),2)) # Top = 0
  colordiferences.append(getColorDiferenceAtribute_abs(rgba_to_hsl(current_pixel),rgba_to_hsl(getPixelZero(image, x, y+1)),2)) # Down = 1
  colordiferences.append(getColorDiferenceAtribute_abs(rgba_to_hsl(current_pixel),rgba_to_hsl(getPixelZero(image, x-1, y)),2)) # Left = 2
  colordiferences.append(getColorDiferenceAtribute_abs(rgba_to_hsl(current_pixel),rgba_to_hsl(getPixelZero(image, x+1, y)),2)) # Right = 3
  colordiferences.append(getColorDiferenceAtribute_abs(rgba_to_hsl(current_pixel),rgba_to_hsl(getPixelZero(image, x-1, y-1)),2)) # Top Left = 4
  colordiferences.append(getColorDiferenceAtribute_abs(rgba_to_hsl(current_pixel),rgba_to_hsl(getPixelZero(image, x+1, y-1)),2)) # Top Right = 5
  colordiferences.append(getColorDiferenceAtribute_abs(rgba_to_hsl(current_pixel),rgba_to_hsl(getPixelZero(image, x-1, y+1)),2)) # Down Left = 6
  colordiferences.append(getColorDiferenceAtribute_abs(rgba_to_hsl(current_pixel),rgba_to_hsl(getPixelZero(image, x+1, y+1)),2)) # Down Right = 7
  maximumLightDifference = -getMinimum(colordiferences)
  lightBool = (maximumLightDifference >= light_threshold) and (TuppleToList(rgba_to_hsl(current_pixel))[2] < maximumLightDifference)
  if (debugl):
    print("Light Maximum Difference =",maximumLightDifference, light_threshold)
  if (directionPrefered != -1 and (directionPrefered < 4)):
    if (collidables[directionPrefered][0] and lightBool):
      if (collidables[directionPrefered][1] < diff_threshold):
        return collidables[directionPrefered][2], collidables[directionPrefered][3]
    collidables.pop(directionPrefered)
  else:
        if (debugl):
          print("References",collidables[directionPrefered][1], diff_threshold, maximumLightDifference)
  for i in range(len(collidables)):
    collide = collidables[i]
    if (collide[0] and lightBool):
      if (collide[1] < diff_threshold):
        return collide[2], collide[3]
      else:
        if (debugl):
          print("References",collide[1], diff_threshold, maximumLightDifference)
  return 0, 0

def identifyEdge(image, diff_threshold=20, light_threshold=20,debugl=False):
  """
  Receives (image) as the image, (diff_threshold) as the threshold of difference between pixels to be considered an edge, 
  (light_threshold) as the threshold of difference in brightness between pixels to be considered an edge.
  Gets the edges of an image (ignoring transparent pixels).
  """
  edges = []
  lastdirection = 0, 0
  for y in range(image.height):
    for x in range(image.width):
      pixel = image.getpixel((x, y))
      if (pixelIsNotTransparent(pixel)):
        if (debugl):
          print("Edge #"+str(len(edges)+1)+" Detected AT ("+str(x)+","+str(y)+")")
        startX, startY = x, y
        current_edge = []
        directionx, directiony = IdentifyEdgeDirection(image, x ,y, (0,0), (0,0), diff_threshold,light_threshold,debugl)
        if (not (directionx == 0 and directiony == 0)):
          while (not (directionx == 0 and directiony == 0)):
            if (debugl):
              print("   Edge #"+str(len(edges)+1)+" AT ("+str(startX)+","+str(startY)+") has direction to ("+str(directionx)+","+str(directiony)+")")
            image.putpixel((startX,startY),(0,0,0,0))
            current_edge.append([startX, startY])
            startX += directionx
            startY += directiony
            directionx, directiony = IdentifyEdgeDirection(image, startX ,startY, (directionx,directiony), (-directionx,-directiony), diff_threshold,light_threshold,debugl)

          current_edge.append([startX, startY])
          image.putpixel((startX,startY),(0,0,0,0))
          edges.append(current_edge)
  print("\n Ended Succesfully with (",len(edges),") edges findedged.")
  return edges

def visualizeEdges(image, edges):
  """
  Allows the display of the edges indicated in the list (edges), 
  (image) is the reference image to obtain the values of the new image to be returned.
  """
  edges_image = Image.new(image.mode,(image.width,image.height),(0,0,0,0))
  for i in range(len(edges)):
    edge = edges[i]
    color_value = random.randint(0,255), random.randint(0,255), random.randint(0,255), 255
    for edgeValue in edge:
      edges_image.putpixel((edgeValue[0],edgeValue[1]),color_value)
  return edges_image

def findEdge(image, _threshold_edge_image=1.0, center__threshold=0.0,sharp_radius=2,sharp_percent=2):
    """
    Receives (image) as the image to process, (_threshold_edge_image) as the threshold to identify edges, 
    (centre__threshold) as the threshold of the centre pixel to be an edge, (sharp_radius,sharp_percent) as drivers for the UnsharpMask filter.
    Returns an image with an outline around the image (works for images with transparency).
    """
    sharpedImage = image.filter(ImageFilter.UnsharpMask(radius=sharp_radius, percent=sharp_percent))
    edge_image = sharpedImage.filter(ImageFilter.Kernel((3, 3), (-1*_threshold_edge_image, -1*_threshold_edge_image, -1*_threshold_edge_image, -1*_threshold_edge_image, 8+center__threshold, -1*_threshold_edge_image, -1*_threshold_edge_image, -1*_threshold_edge_image, -1*_threshold_edge_image), 1, 0))
    edge_image = edge_image.convert("RGBA")
    for y in range(edge_image.height):
      for x in range(edge_image.width):
        pixel1 = image.getpixel((x,y))
        pixel = edge_image.getpixel((x,y))
        r,g,b,a = pixel
        r1,g1,b1,a1 = pixel1 
        if (a > 0):
          a = 255
          r,g,b = 0,0,0
          edge_image.putpixel((x,y),(r,g,b,a))
        else:
          a = 0
          edge_image.putpixel((x,y),(r1,g1,b1,a))
    return edge_image

    return cv2_to_pillow(rgba_image)
def ToGrayscale(image, oper=0):
  """
  Receives (image) as the image to process, (oper) as the method to use:
  0 : Takes the magnitude of the values r, g, b.
  1 : Take the averages of the sum of r, g, g.
  2 : Takes the magnitude of the r, g, b values by applying the sigmoid function. 
  3 : Takes the magnitude of the r, g, b values by applying the inverse tangent function. 

  Returns an RGBA image but the colours are in greyscale depending on the method used.
  """
  for y in range(image.height):
    for x in range(image.width):
      r,g,b,a = image.getpixel((x,y))
      n = 0
      if (oper == 0):
        n = round(Clamp(getMagnitudes_([r/255,g/255,b/255])*255,0,255))
      elif (oper == 1):
        n = round(Clamp(getPromediate_([r/255,g/255,b/255])*255,0,255))
      elif (oper == 2):
        n = round(Clamp(sigmoid(getMagnitudes_([r/255,g/255,b/255]))*255,0,255))
      elif (oper == 3):
        n = round(Clamp(tanh(getMagnitudes_([r/255,g/255,b/255]))*255,0,255))
      image.putpixel((x,y),(n,n,n,a))
  return image

def SimplifyColors(image, simplifier=8):
  """
  Receives (image) as the image to be processed, (simplifier) as the number of colours per channel r, g, b, a.
  Returns an RGBA image but the colours are simplified in the r, g, b, a channels depending on the (simplifier).
  """
  simplyimage = Image.new(image.mode,(image.width,image.height),(0,0,0,0))
  for y in range(simplyimage.height):
    for x in range(simplyimage.width):
      r,g,b,a = image.getpixel((x,y))
      r = round(simplify(r/255,simplifier)*255)
      g = round(simplify(g/255,simplifier)*255)
      b= round(simplify(b/255,simplifier)*255)
      simplyimage.putpixel((x,y),(r,g,b,a))
  return image

def CombineEdgesColors(image, image2):
  """
  Combine the two given images, and return the combined one, only in the pixels that are transparent for the first image.
  """
  for y in range(image.height):
    for x in range(image.width):
      r2,g2,b2,a2 = image2.getpixel((x,y))
      r,g,b,a = image.getpixel((x,y))
      if (a == 0):
        image.putpixel((x,y),(r2,g2,b2,a2))
  return image

def findEdgedges(path,outline_threshold=1.32,center_threshold=0.0,sharp_radius=1,sharp_percent=1, color_simplifier=2, color_diff_threshold=10, color_light_threshold=10):
  """
  Receives (path) which indicates the path of the image file to process, 
  (outline_threshold) indicates the threshold for the outline, 
  (centre_threshold) indicates how much the centre threshold increases to consider outline, 
  (sharp_radius, sharp_percent) control the values of the UnSharpMask filter, 
  (colour_simplifier) value of colours for each colour channel to find edges, 
  (colour_diff_threshold) threshold of the difference between pixels to be considered edges, 
  (colour_light_threshold) threshold of the difference in brightness between pixels to be considered edges.

  Returns a dictionary which contains the positional values of each different connected edge.
  """
  image = Image.open(path)
  image_outline = findEdge(image,outline_threshold,center_threshold,sharp_radius,sharp_percent)
  symplyfy_image = SimplifyColors(image,color_simplifier)
  inside_edges = visualizeEdges(symplyfy_image,identifyEdge(symplyfy_image,color_diff_threshold,color_light_threshold))
  combined_edges = CombineEdgesColors(image_outline, inside_edges)
  outside_edges = identifyIndividualEdges(combined_edges)
  image2 = Image.open(path)
  return outside_edges, image2

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
  return edgesDict

def imageFromEdges(image, edges, factor_x, factor_y):
  """
  Returns an image with the colour specified in the (edges) dictionary.
  (factor_x) and (factor_y) indicate the value to divide the size of the previous image to create a new image.
  """
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
        else:
          resultColor = image.getpixel((nx, ny))
      edges_image.putpixel((x,y),resultColor)
  return edges_image

def CombineImageInCaps(image, image2):
  """
  Combine the two given images, and return the combined one, only in the pixels that are transparent for the first image.
  """
  result_image = image.copy()
  for y in range(image.height):
    for x in range(image.width):
      r2,g2,b2,a2 = image2.getpixel((x,y))
      r,g,b,a = image.getpixel((x,y))
      if (a == 0):
        result_image.putpixel((x,y),(r2,g2,b2,a2))
  return result_image

def processImage(path,factor_x,factor_y):
  image_edges, image_result = findEdgedges(path)
  edg = resizeEdges(image_edges,factor_x,factor_y)
  return imageFromEdges(image_result,edg,factor_x,factor_y)
