import os
import sys
import Ice
import omero
import numpy as np
import tifffile
from PIL import Image
from omero.gateway import BlitzGateway

#   config utilisateur ...
USERNAME = 'username'   #to modif (normal omero user)
PASSWORD = 'passwd' #to modif (pass)
HOST = 'localhost' #  I assume an ssh tunnel is already open, calls directly from localhost ...
PORT = 4064
IMAGE_ID = sys.argv[1]  # Image to be downloaded as arg
GROUP_ID = 107 # Group ID
OUTPUT_DIR = 'omero_rendered_export'

# Supp. Max_img_pixels
Image.MAX_IMAGE_PIXELS = None

# ICE props pour images larges
props = Ice.createProperties()
props.setProperty("Ice.MessageSizeMax", "512000")  # modified on the server to  512 MB as well
init_data = Ice.InitializationData()
init_data.properties = props

# ouvre une connexion (client)
client = omero.client(HOST, PORT, init_data)
session = client.createSession(USERNAME, PASSWORD)
conn = BlitzGateway(client_obj=client)
conn.SERVICE_OPTS.setOmeroGroup(GROUP_ID)


# -I img ...
image = conn.getObject("Image", IMAGE_ID)
if not image:
    raise Exception(f"Image {IMAGE_ID} not found in group {GROUP_ID}")

name = image.getName().replace(" ", "_")
size_z = image.getSizeZ()
size_x = image.getSizeX()
size_y = image.getSizeY()
size_t = image.getSizeT()


# -O img ...
os.makedirs(OUTPUT_DIR, exist_ok=True)
output_path = os.path.join(OUTPUT_DIR, f"{IMAGE_ID}_{name}.tiff")
print(f"---> Exporting rendered RGB Z-stack: {name} (ID: {IMAGE_ID})")
print(f"   Dimensions: Z={size_z}, X={size_x}, Y={size_y}, T={size_t}")



# For each Z slice (T=0) rendered RGB do
with tifffile.TiffWriter(output_path, bigtiff=True) as tif:
    for z in range(size_z):
        print(f" --> --> Rendering Z={z}")
        rendered = image.renderImage(z, t=0)
        rgb = np.asarray(rendered)
        tif.write(rgb.astype(np.uint8), photometric='rgb')

print(f"Rendered RGB TIFF saved to: {output_path}")
conn.close()

