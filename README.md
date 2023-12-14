# BetterPixelArtDownscale
Python scripts for resizing pixel art to a smaller scale while preserving sharp edges and fine details. Ideal for video game development and graphic design projects. Simplify your pixel art resizing with this efficient and user-friendly toolkit.

## Usage
The code is composed of two 4 essential modules, which are:
### pattern_noise
This module allows you to create a list of numbers using ***create_pattern*** function, indicating the expected value of the sum of all the values in the list, and the size of the list,. It interleaves in a pattern of 0, 1, 2, 3, 4 the numbers in the list, thus creating a stylised pattern.
**Examples of use:**
```
import pattern_noise
list_size = 8
reach_value = 16
pattern = pattern_noise.create_pattern(reach_value, list_size)
print(pattern)
```
Result = **_[2, 2, 2, 2, 2, 2, 2, 2]_**


```
import pattern_noise
list_size = 9
reach_value = 16
pattern = pattern_noise.create_pattern(reach_value, list_size)
print(pattern)
```
Result = **_[2, 1, 2, 1, 2, 1, 2, 1, 4]_**


```
import pattern_noise
list_size = 16
reach_value = 64
pattern = pattern_noise.create_pattern(reach_value, list_size)
print(pattern)
```
Result = **_[4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4]_**

```
import pattern_noise
list_size = 12
reach_value = 32
pattern = pattern_noise.create_pattern(reach_value, list_size)
print(pattern)
```
Result = **_[3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 4]_**

**As we can see that the sum of all the values in the list always gives the expected value, but creating a stylised pattern of numbers, which we will use in the next module.**

### image_resize

This module allows you to process an image and resize it ***(intended to resize it to a smaller size than the original)*** to a new specified size ***(works best if the division between the current_size and the new_size is greater than 1.5)***. For this it uses the ***pattern_noise*** module to generate stylised lists of the pixel indices that should be taken into the new image at the new scale. It is used from the ***processImage** function, which receives the image path to process, a divisor factor for the width and a divisor factor for the height (these factors indicate the new image size/factor for the height and width), and optionally can be enabled to simplify the colours, and giving a simplifier factor, which takes each pixel and processes it round(pixel*simplifier)/simplifier. And returns a PIL image.

**Examples of use:**

Image to process ![mareep](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/b766d2e5-a928-4563-a066-e9c367288274)

```
import image_resize
from PIL import Image
image_path = "mareep.png"
width_factor = 2
height_factor = 2
resized_image = image_resize.processImage(image_path,width_factor,height_factor)
resized_image.save("resised_"+image_path)
```

Result ![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/91786f29-9165-4270-b4a3-f305baa72379)

### image_edges

This module allows you to process an image, and thus obtain the outline and borders of the image, additionally you can indicate a division factor to change the size of the resulting image. It is used from the ***processImage*** function, it receives the image path, the factor for the width, the factor for the height, and additionally you can decide whether to include the outline, the inner edges, or just the edges, you can also set parameters to change the edge detection ***(already set previously to work with pixel art)***. And it returns an PIL image with the new size that is size/factor, for height and width, the image contains what is specified as internal borders or outlines, and the pixel value that corresponds to the image in which the border is located.


**Examples of use:**

Image to process ![mareep](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/b766d2e5-a928-4563-a066-e9c367288274)

```
import image_edges
from PIL import Image
image_path = "mareep.png"
width_factor = 2
height_factor = 2
resized_image = image_edges.processImage(image_path,width_factor,height_factor)
resized_image.save("resised_"+image_path)
```

Result ![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/431b8319-9a51-4188-b6a8-440417fac346)

### image_resize_edge

This module is the main usage module, it allows you to process an image, resize it **(resize it to a smaller size than the original)*** and obtain the resized image, with sharp, fine contours and edges ***(intended for pixel art)***. For this it combines the modules ***image_resize*** to obtain the resized image by ***pattern_noise***, and ***image_edges*** to obtain the image of the contours and edges of the image. And it combines in the first layer the resized image and in the second layer the image of the edges, to obtain the final image. It receives the path of the image, the factor for the width, the factor for the height, additionally it receives optional parameters ***(already set previously to work with pixel art)*** to include or not the contours, the edges, for the edge detection. Returns an PIL image.

**Examples of use:**

Image to process ![mareep](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/b766d2e5-a928-4563-a066-e9c367288274)

```
import image_resize_edge
from PIL import Image
image_path = "mareep.png"
width_factor = 2
height_factor = 2
resized_image = image_resize_edge.processImage(image_path,width_factor,height_factor)
resized_image.save("resised_"+image_path)
```
Result ![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/9b70e850-8cf6-4a07-986e-e2616cbc33d7)
## Google Colab
To implement in Google Colab you must do these steps:

**First, clone this repository in Google Colab:**
```
!git clone https://github.com/MidFord/BetterPixelArtDownscale.git
```

**Finally, add this to the beginning of your code:**
```
import sys
sys.path.append('BetterPixelArtDownscale')
## Your Code Down Here!
```
## Usage results

### Minecraft item textures 16*16: 

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/1b838a61-e299-4071-85bd-d038c3a7a31a)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/710f814c-5912-46b1-a23f-b482814daccb)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/1dc045ab-0427-41bc-918b-877edd98b289)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/c419bdac-2eb0-4881-9d5b-a85a4f046016)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/d7177a46-69ae-42c7-aef7-77067b4e7706)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/12392623-a7e7-456b-aafb-4c5b740b3d69)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/56f1f795-8451-4f0e-b509-2375b4d4b6e6)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/8f9fcc5c-baf4-4161-9d94-5926a9241e47)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/8fb1db17-1250-44bc-abb0-fd82da07b2f1)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/3d7546d9-b227-4940-ac76-50872e01a46d)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/969217ca-c059-4949-af17-d744fcb5de54)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/fd3b9c55-adbe-4dda-af47-073d846807a3)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/36130562-133e-4abc-813a-3cd5a2a9d969)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/2a2b04b6-85d8-48d3-a00f-34dd497b9c6d)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/82ca2f3c-0ccb-4c5a-860f-9c3dd2554746)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/321c3bfa-11cd-459c-a9fa-4d5c752cf361)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/aa118908-d2e3-472e-81a7-ebd315e190d4)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/c664f8a7-552c-46ca-a733-2138c4a4e60d)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/f075bd4b-463e-46c9-9407-4c1e946d2a0b)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/bb0a5cdb-5b0b-4448-99c3-39242d7b5cf2)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/71650c98-01b4-4d83-8a8b-f6bde8ed7e26)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/7598c27d-4979-47f7-8fef-840bdf994eaa)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/2d954455-fa95-4651-ae18-d3fa4676ddf7)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/517688be-adf1-4371-a04e-50826b532ced)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/1e3008a5-cce0-46cd-b18f-85c3692aa8a9)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/de2ec8da-1942-4d5b-871c-6476da9b18af)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/384373c9-c9f0-46d1-a10c-f0da842cb396)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/55aba9f1-b6ff-4f76-a9dd-733cfb41f7b9)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/84405e3b-de7a-4ed8-92b7-84e612950f90)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/0ea6d2bb-aef4-47dc-ba21-67715efcca6f)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/8452770f-81b4-4b23-810f-4e279b3551b3)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/58417e23-34dd-4d02-a2e5-4c22e2cd1f4e)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/08f27e64-263a-4ce3-bb4d-1ea53f2d234f)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/feeced39-74d1-468b-8022-a266291765e5)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/2531b806-e68c-4587-af82-75f076ad5d24)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/f12beb33-7ae5-4c0b-9406-df1597c8540b)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/0d3c224a-7c02-4bee-bf3f-9c02c3928987)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/c4ddd442-e34e-4b2d-a5a5-dbf2a19a79d0)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/1f82d4e7-297e-42a3-b95f-458606b82537)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/f2160ee6-e549-4adb-acf1-556e5ee40ad5)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/dac988c0-f1d2-4eab-93da-1fbd3871997e)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/425533c6-bb53-4c5f-87eb-4aa263ac32e4)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/a08c01db-5dd6-4b11-aa27-b3a86cb8853a)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/5e16684a-2a2c-4954-aa23-a783c7d8680e)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/2edc5dae-7812-42ef-b558-3d1c3a47cd32)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/9af325c5-d727-4c54-95b0-0a25889bad69)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/a49f6177-8d73-48b5-b3d4-51e4e2fbf4dd)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/de6d2e14-0829-4bb3-af02-71919d95df13)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/ac82d08c-01bc-49fd-9498-a25fe135f3a5)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/d2b07884-01cd-46fa-a3ec-758bf8567ecf)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/1aac80e4-beb0-49f9-83ec-8c6dec8da91f)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/b0889cea-e84a-406b-8b53-fdc21229137a)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/82b063ed-daed-49e1-a080-3f05febadb49)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/4643a7a0-d1b0-46a0-8038-ef638923d88f)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/2abab32a-7f53-4915-97cb-be12dd500f8a)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/fa580bbb-6872-4494-9cce-07a0a1b196c8)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/7b64a98e-55c2-4ebb-8ec9-f2032765ee3c)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/d3a62fe6-b5dc-437d-9b15-fea70bc45f17)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/92aefcc3-4bda-42d2-b4a3-5bf99ee5edeb)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/14dec4c5-90e7-4674-8a38-472d18fc6203)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/a8aa3d1e-16ae-4fc8-82c5-f38b3dd24529)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/4cfda966-5fb8-400e-b5c5-ec3e53c9ca3d)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/bc2700bf-4b1e-47f2-9689-aead8f16f56b)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/9cc6d4f9-e974-4b89-8f1c-980437f85a85)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/fe20b1b8-e67b-4328-bbab-eccaf7488461)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/6ff2ec06-199b-4d9d-8d0e-ce4c670b69b5)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/ebd5eda4-a970-41cf-b2ce-3cfc80dc7618)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/9ae29ad6-9673-4c26-ab14-f4b2693c7f60)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/36974f85-9d1d-4cfe-b68f-9a8cb7b327be)

### Minecraft mob textures:

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/a6a14c5c-8417-4f68-be4a-278bc2e7e6bd)

**Resized with factor 2 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/07a331ab-6caf-4ce6-b75b-443648ea5f8a)

**Resized with factor 2 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/5eb4aef2-7841-4a4d-88ef-5c607628c01b)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/5a9a362c-f9d1-4f33-b086-dd9375ab0af0)

**Resized with factor 2 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/f1d9a0fd-8671-40cd-a092-40ca05883736)

**Resized with factor 2 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/ea0003b1-d902-4a32-b8f5-82f7b2706ffb)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/13243e05-71d9-490a-9170-802c7629b75e)

**Resized with factor 2 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/00278b9a-66d8-44c6-8030-f0e00dabcfb1)

**Resized with factor 2 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/96989b03-dba6-4d6c-862e-26413a2503db)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/02c3199f-9981-496d-9ec3-45f0284adf4c)

**Resized with factor 2 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/fae87e5e-fea2-4e42-a14d-fd2445da8a30)

**Resized with factor 2 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/37edacc5-53e4-4700-819d-4193ec006954)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/ecfd6428-1777-4d91-9951-2244177e1bd5)

**Resized with factor 2 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/587ff578-a2a5-460d-8695-b50f08b1404b)

**Resized with factor 2 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/3cd73954-a942-4f32-aeb1-363eb6effc78)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/553548fa-fb7b-43e0-a0fe-742fa0dd7ad0)

**Resized with factor 2 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/a30b7cdf-0fd3-4eda-b51c-0109a55f8d31)

**Resized with factor 2 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/e2c355a4-675d-4354-bc6e-64e99446c079)

