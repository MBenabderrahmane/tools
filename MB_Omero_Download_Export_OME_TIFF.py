import os
import sys
import Ice
import omero
import numpy as np
import tifffile
from omero.gateway import BlitzGateway

# U
USERNAME = 'x'
PASSWORD = 'x'
HOST = 'localhost'
PORT = 4064
IMAGE_ID = int(sys.argv[1])
GROUP_ID = 107
OUTPUT_DIR = 'omero_ometiff_export'

#
props = Ice.createProperties()
props.setProperty("Ice.MessageSizeMax", "512000")  # 512 MB
init_data = Ice.InitializationData()
init_data.properties = props




# CONN
client = omero.client(HOST, PORT, init_data)
session = client.createSession(USERNAME, PASSWORD)

conn = BlitzGateway(client_obj=client)
conn.SERVICE_OPTS.setOmeroGroup(GROUP_ID)







# GET IMAGE
image = conn.getObject("Image", IMAGE_ID)
if not image:
    raise Exception(f"Image {IMAGE_ID} not found in group {GROUP_ID}")

name = image.getName().replace(" ", "_")

size_z = image.getSizeZ()
size_c = image.getSizeC()
size_t = image.getSizeT()
size_x = image.getSizeX()
size_y = image.getSizeY()

pixels = image.getPrimaryPixels()
dtype = np.dtype(pixels.getPixelsType().getValue())

print(f"\n---> Exporting OME-TIFF: {name} (ID: {IMAGE_ID})")
print(f"Dimensions: T={size_t}, Z={size_z}, C={size_c}, Y={size_y}, X={size_x}")
print(f"Pixel type: {dtype}")




# OUTPUT
os.makedirs(OUTPUT_DIR, exist_ok=True)
output_path = os.path.join(OUTPUT_DIR, f"{IMAGE_ID}_{name}.ome.tiff")




def plane_generator():
    for t in range(size_t):
        for z in range(size_z):
            for c in range(size_c):
                print(f" --> T={t}, Z={z}, C={c}")
                plane = pixels.getPlane(z, c, t)
                yield np.array(plane)




# WRITE OME-TIFF
print("\n---> Writing OME-TIFF (streaming)...")

tifffile.imwrite(
    output_path,
    plane_generator(),
    shape=(size_t, size_z, size_c, size_y, size_x),
    dtype=dtype,
    bigtiff=True,
    metadata={
        'axes': 'TZCYX'
    }
)


conn.close()
client.closeSession()
