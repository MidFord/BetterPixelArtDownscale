import image_edges as imeg
import image_resize as imre

def processImage(image_path, factor_x, factor_y):
    edges_image = imeg.processImage(image_path,factor_x,factor_y)
    image_downscaled = imre.processImage(image_path,factor_x,factor_y)
    image_merged = imeg.CombineImageInCaps(edges_image,image_downscaled)
    return image_merged