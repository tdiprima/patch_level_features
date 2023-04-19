# Opens a .svs slide using OpenSlide, extracts a 512x512 pixel patch from the slide, and saves it as a PNG image.
import openslide

slide = openslide.OpenSlide('/data1/tdiprima/dataset/PC_058_0_1/PC_058_0_1.svs')
patch = slide.read_region((119808, 55808), 0, (512, 512))
# newImg1 = PIL.Image.new('RGB', (512,512))
patch.save("img1.png")
slide.close()
