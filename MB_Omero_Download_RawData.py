import os
import sys
import Ice
import omero
import numpy as np
import tifffile
from omero.gateway import BlitzGateway



USERNAME = 'username'
PASSWORD = 'passwd'
HOST = 'localhost'   # SSH tunnel assumed open
PORT = 4064
IMAGE_ID = int(sys.argv[1])
GROUP_ID = 107 #change this...
OUTPUT_DIR = 'omero_raw_export'

props = Ice.createProperties()
props.setProperty("Ice.MessageSizeMax", "512000")  # 512 MB
init_data = Ice.InitializationData()
init_data.properties = props


#Ouvre une conn
client = omero.client(HOST, PORT, init_data)
session = client.createSession(USERNAME, PASSWORD)

conn = BlitzGateway(client_obj=client)
conn.SERVICE_OPTS.setOmeroGroup(GROUP_ID)




#img
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
dtype = pixels.getPixelsType().getValue()

print(f"\n---> Exporting RAW image: {name} (ID: {IMAGE_ID})")
print(f"Dimensions: Z={size_z}, C={size_c}, T={size_t}, Y={size_y}, X={size_x}")
print(f"Pixel type: {dtype}")



#o.Img
os.makedirs(OUTPUT_DIR, exist_ok=True)
output_path = os.path.join(OUTPUT_DIR, f"{IMAGE_ID}_{name}_RAW.tiff")


#Get Raw
# We'll export T=0 only (extend easily if needed)

stack = np.zeros((size_z, size_c, size_y, size_x), dtype=np.dtype(dtype))

for z in range(size_z):
    for c in range(size_c):
        print(f" --> Fetching Z={z}, C={c}")
        
        plane = pixels.getPlane(z, c, 0)  # raw plane
        arr = np.array(plane)             # keep original dtype
        
        stack[z, c, :, :] = arr



print("\n---> Writing BigTIFF...")

tifffile.imwrite(
    output_path,
    stack,
    bigtiff=True,
    metadata={
        'axes': 'ZCYX'
    }
)



#CLean
conn.close()
client.closeSession()
