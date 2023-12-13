import image_edges as imeg
import image_resize as imre

def processImage(image_path, factor_x, factor_y,iclude_outline=True, include_edges=True, only_edges=False, outline_threshold=1.32,center_threshold=0.0,sharp_radius=1,sharp_percent=1, color_simplifier=2, color_diff_threshold=10, color_light_threshold=10):
    """
    Processes an image by finding and resizing its edges
    """
    edges_image = imeg.processImage(image_path,factor_x,factor_y, iclude_outline, include_edges, only_edges, outline_threshold,center_threshold,sharp_radius,sharp_percent, color_simplifier, color_diff_threshold, color_light_threshold)
    image_downscaled = imre.processImage(image_path,factor_x,factor_y)
    image_merged = imeg.CombineImageInCaps(edges_image,image_downscaled)
    return image_merged
