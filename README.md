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

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/b9989842-6a29-46cb-9652-cf4f763efdec)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/f9001b2c-c2a3-4958-9602-6fbae85c8db3)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/67a157a4-dc91-432b-8939-12b3f71c6c3c)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/468ff450-d853-4475-ab48-af4094e0f242)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/92e2bfbf-8a36-4607-9cb6-652ade96c428)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/a28bf0dd-0e3c-4498-b788-c5efdc7e391e)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/95b64fea-faef-4a43-8dc2-321ae2fde554)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/1d261d01-90b0-4d0d-9c09-94337a596c72)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/ccadcc7d-4455-4947-b3c7-9a9f3c22e0a7)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/f9926670-502e-4589-a813-619c7dd035f7)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/66053821-27bb-4690-adff-06aa767f627f)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/f98b5672-6952-43ad-999d-3bea5ef28b12)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/327c1e5e-fb2b-4b4f-94cb-9ef529ffc92c)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/43fbeb21-7546-484e-b216-1030d7067708)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/cba46e43-b035-44b6-ae05-144a1a980e92)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/f48bd5ff-5c7a-4276-8bc0-3e8d706ff999)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/da52f5b7-6444-4403-87c5-1e99750bfc20)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/b69753ab-d36a-48ba-9f19-87c2e2b18b66)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/7ddd48cd-933d-4a29-adb2-35d5c84a970a)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/c985734b-0a84-4142-9a5e-8caf48dc23b0)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/c66a1249-7fe1-4659-994c-b3a819c2d8f5)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/a2681a4f-9bb6-4c79-8f9f-dd96fff43d59)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/de2ec8da-1942-4d5b-871c-6476da9b18af)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/c6a92f5f-d8bc-4378-b539-f924e9fdf82a)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/939c0ec6-59df-41f2-8ce9-16a5c5de613a)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/84405e3b-de7a-4ed8-92b7-84e612950f90)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/73f516cb-4101-44ca-9b68-170866f782f8)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/eb68ed3a-3ab3-4e21-bd2f-3cc25d96c436)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/58417e23-34dd-4d02-a2e5-4c22e2cd1f4e)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/ae863531-07d1-4510-9f43-bc99e124fe93)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/b2cdc290-1c32-4857-bfe3-fbb810954630)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/2531b806-e68c-4587-af82-75f076ad5d24)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/cff2e20d-722d-4576-845c-bf109ed9e81c)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/be2abdce-bd7c-4211-88bc-33184363d22c)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/c4ddd442-e34e-4b2d-a5a5-dbf2a19a79d0)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/2fedbc27-7721-423a-bbb0-c2f643c94c95)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/afb41c0a-745d-42d2-b22a-d384f36ef169)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/dac988c0-f1d2-4eab-93da-1fbd3871997e)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/ab84089e-a90a-4e28-9ea0-036e91fb6927)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/f9361b95-bca4-4a0e-b9bf-39b4409e7c89)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/5e16684a-2a2c-4954-aa23-a783c7d8680e)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/2edc5dae-7812-42ef-b558-3d1c3a47cd32)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/c49e1b13-20c8-4b21-bca7-1a477b27548e)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/a49f6177-8d73-48b5-b3d4-51e4e2fbf4dd)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/de6d2e14-0829-4bb3-af02-71919d95df13)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/8ebbc69a-1a05-4ac5-a6d2-8b4449ab4fe7)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/d2b07884-01cd-46fa-a3ec-758bf8567ecf)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/1aac80e4-beb0-49f9-83ec-8c6dec8da91f)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/0d2402a1-2f48-4f55-a701-d5a20bbd5ad1)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/82b063ed-daed-49e1-a080-3f05febadb49)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/4643a7a0-d1b0-46a0-8038-ef638923d88f)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/22efa713-8dcb-46df-91a3-2bc2210ea4ae)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/fa580bbb-6872-4494-9cce-07a0a1b196c8)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/7b64a98e-55c2-4ebb-8ec9-f2032765ee3c)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/ed38922a-088f-4d58-a4be-4d8998cf543b)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/92aefcc3-4bda-42d2-b4a3-5bf99ee5edeb)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/14dec4c5-90e7-4674-8a38-472d18fc6203)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/ef49477f-a975-4fed-9c6f-4f7a0a257aca)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/4cfda966-5fb8-400e-b5c5-ec3e53c9ca3d)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/bc2700bf-4b1e-47f2-9689-aead8f16f56b)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/0ac78775-6dd4-414e-8495-068998e2aeba)

**Resized to 8*8 using the pattern_noise algorithm:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/fe20b1b8-e67b-4328-bbab-eccaf7488461)

**Resized to 8*8 using the pattern_noise algorithm + edge detection and edge permanence:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/6ff2ec06-199b-4d9d-8d0e-ce4c670b69b5)

**Original image:**

![image](https://github.com/MidFord/BetterPixelArtDownscale/assets/87622554/995a84a4-e942-4b2c-9ec4-7e25a6615e5e)

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

