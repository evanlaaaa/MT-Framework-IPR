bl_info = {
    "name": "MHW IPR Model Importer",
    "category": "Import-Export",
    "author": "Evanla",
    "location": "File > Import-Export > IPR",
    "version": (1,0,0)
}
 
import struct
import bpy
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty

def menu_func_import(self, context):
    self.layout.operator(ImportIPR.bl_idname, text="MHW IPR (.ipr)")
        
class ImportIPR(Operator, ImportHelper):
    bl_idname = "custom_import.import_mhw_ipr"
    bl_label = "Load MHW IPR file (.ipr)"
    bl_options = {'REGISTER', 'PRESET', 'UNDO'}

    # ImportHelper mixin class uses this
    filename_ext = ".ipr"
    filter_glob = StringProperty(default="*.ipr", options={'HIDDEN'}, maxlen=255)

    texture_path = StringProperty(
        name = "Texture Source",
        description = "Root directory for the MRL3 (Native PC if importing from a chunk).",
        default = "")

    def execute(self,context):
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass

        # Define the format strings for each structure
        header_format = '<64sQL56xQQ'
        entry_format = '<32xQ40xQQ32x'
        config_format = '<10f52s'

        # Open the binary file
        with open(self.properties.filepath, "rb") as binary_file:
            binary_data = binary_file.read()

        # Unpack the header
        header_data = struct.unpack_from(header_format, binary_data)
        FileType, EntryOffSet, entryCount, _, Version = header_data

        # Unpack the entries
        entries = []
        for i in range(entryCount):
            entry_data = struct.unpack_from(entry_format, binary_data, EntryOffSet + i * 128)
            assetOffset, configOffset, configCount = entry_data
            entries.append({
                "assetOffset": assetOffset,
                "configOffset": configOffset,
                "configCount": configCount
            })

        # Unpack the configs
        for entry in entries:
            # Extract the path1
            path1_end = binary_data[entry["assetOffset"]:].index(b'\x00')
            path1 = binary_data[entry["assetOffset"]:entry["assetOffset"]+path1_end].decode()
            print("Importing " + path1 + "(TOTAL: " + str(entry["configCount"]) + ")")
            
            for i in range(entry["configCount"]):
                config_data = struct.unpack_from(config_format, binary_data, entry["configOffset"]  + i * 144)
                coordX, coordY, coordZ, scaleX, scaleY, scaleZ, rotX, rotY, rotZ, rotW, unk = config_data
                print("Currently importing index: " + str(i))

                # mod3 import here
                bpy.ops.object.select_all(action="DESELECT")
                options = {
                    "import_textures": True,
                    "texture_path": self.properties.texture_path,
                    "import_skeleton": "None",
                    "clear_scene": False,
                    "import_materials": True
                }
                bpy.ops.custom_import.import_mhw_mod3(filepath=str(self.properties.texture_path +"\\"+ path1 +'.mod3'), **options)
                bpy.ops.object.select_all(action="SELECT")
                objs = [obj for obj in bpy.context.selected_objects if obj.tag == True and obj.get("isTransformed") is None]
                bpy.ops.object.select_all(action="DESELECT")
                for x in objs:
                    x["isTransformed"] = 1
                    x.location = (coordX, coordY, coordZ)
                    x.scale = (scaleX, scaleY, scaleZ)
                    x.rotation_mode = 'QUATERNION'
                    x.rotation_quaternion = (rotW, rotX, rotY, rotZ)
                    x.tag = False
                bpy.ops.object.select_all(action="DESELECT")

        return {'FINISHED'}

    def parseOptions(self):
        options = {}
        return options

def register():
    bpy.utils.register_class(ImportIPR)
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    

def unregister():
    bpy.utils.unregister_class(ImportIPR)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    
    #del bpy.types.Object.MHWSkeleton

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()
