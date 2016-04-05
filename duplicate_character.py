"""
Rigify auto character change name
#====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#======================= END GPL LICENSE BLOCK ========================
"""

bl_info = {
    'name': 'CHR Duplicator',
    'author': 'Lucio Rossi',
    'version': (0, 1),
    'blender': (2, 75, 0),
    'location': 'View3D > Tools > Changename',
    'category': 'Rigging',
}

import bpy
import random
import time
from rigify.generate import generate_rig

def random_id(length=8):
    """ Generates a random alphanumeric id string.
    """
    tlength = int(length / 2)
    rlength = int(length / 2) + int(length % 2)

    chars = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    text = ""
    for i in range(0, rlength):
        text += random.choice(chars)
    text += str(hex(int(time.time())))[2:][-tlength:].rjust(tlength, '0')[::-1]
    return text

def get_name(rig):

    try:
        name = rig.users_group[0].name.rstrip('_GRP')
    except:
        name = ""

    return name

def duplicate_rig_ui(name, newname, rig_id, new_id):

        try:
            rig_ui = bpy.data.texts[name + '_rig_ui.py']
            for line in rig_ui.lines:
                if rig_id in line.body:
                    line.body=('rig_id = "%s"' % new_id)
            rig_ui.name = newname + '_rig_ui.py'
        except:
            pass

def find_face_bones(metarig):

    face = metarig.data.edit_bones['face']

    bones = ['face']

    for chl in face.children_recursive:
        bones.append(chl.name)

    return bones

def get_bone_parents(rig, bones):

    bone_parents = {}

    for bone in rig.data.edit_bones:
        if (bone.name in bones) and bone.parent:
            bone_parents[bone.name] = bone.parent.name

    return bone_parents

class Duplicate_CHR(bpy.types.Panel):
    bl_label = "Duplicate Character"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    #bl_options = {'DEFAULT_OPEN'}
    bl_category = 'DupliCHR'

    @classmethod
    def poll(cls,context):
        if context.object and context.object.type == 'ARMATURE':
            return True

    def draw(self,context):

        layout = self.layout
        scn = context.scene
        rig = bpy.context.active_object

        row = layout.row(align=True)
        row.label('Current rig_id:')
        row.label(bpy.data.armatures[rig.name]['rig_id'])

        layout.separator()

        name = get_name(rig)
        row = layout.row(align=True)
        row.label('Current name:')
        row.label(name)

        layout.separator()

        row = layout.row(align=True)
        row.operator('duplichar.grab_info', icon = 'EYEDROPPER')

        row = layout.row(align=True)
        row.prop(scn,'NewName')

        row = layout.row(align=True)
        row.prop(scn,'NewRigID')

        layout.separator()

        row = layout.row(align=True)
        row.operator('duplichar.new_id', icon = 'PLUS')
        row = layout.row(align=True)
        row.operator('duplichar.update', icon = 'FILE_REFRESH')

        layout.separator()

        row = layout.row(align=True)
        row.operator('duplichar.face_off', icon = 'FILE_REFRESH')

class Generate_rig_id(bpy.types.Operator):
    """Generate new rig_id"""
    bl_idname = "duplichar.new_id"
    bl_label = "New rig_id"

    def execute(self,context):

        scn = context.scene
        rig_id = random_id(16)

        scn.NewRigID = rig_id

        return {'FINISHED'}

class Update_CHR(bpy.types.Operator):
    """Update Character"""
    bl_idname = "duplichar.update"
    bl_label = "Update character"

    def execute(self, context):

        scn = context.scene
        rig = bpy.context.active_object


        duplicate_rig_ui(rig.users_group[0].name.rstrip('_GRP'), scn.NewName, bpy.data.armatures[rig.name]['rig_id'], scn.NewRigID)

        bpy.data.armatures[rig.name]['rig_id'] = scn.NewRigID
        rig.users_group[0].name = scn.NewName + '_GRP'


        return {'FINISHED'}

class Grab_rig_info(bpy.types.Operator):
    """Grab rig infos"""
    bl_idname = "duplichar.grab_info"
    bl_label = "Grab rig infos"

    def execute(self, context):

        scn = context.scene
        rig = bpy.context.active_object

        try:
            scn.NewName = rig.users_group[0].name.rstrip('_GRP')
            scn.NewRigID = rig.data['rig_id']
        except:
            scn.NewName = ''
            scn.NewRigID = ''

        return {'FINISHED'}

class Face_off(bpy.types.Operator):
    """Refresh Face Bones"""
    bl_idname = "duplichar.face_off"
    bl_label = "Resfresh Face Bones"

    def execute(self, context):
        scn = context.scene

        rig = scn.objects['rig']
        metarig = scn.objects['metarig']

        if not metarig.is_visible(scn):
            self.report({'WARNING','INFO'}, "Metarig is not visible!")
            return {'FINISHED'}


        # Save rig_ui Text
        try:
            rig_ui_name = rig.users_group[0].name.rstrip('_GRP') + '_rig_ui.py'
        except:
            rig_ui_name = 'rig_ui.py'
        old_rig_id = bpy.data.armatures['rig']['rig_id']
        scn.NewRigID = old_rig_id
        scn.NewName = rig.users_group[0].name.rstrip('_GRP')

        # Duplicate metarig and rig
        bpy.ops.object.select_all(action='DESELECT')
        rig.select = True
        bpy.ops.object.duplicate()
        body_rig = scn.objects['rig.001']
        bpy.ops.object.select_all(action='DESELECT')
        metarig.select = True
        bpy.ops.object.duplicate()
        head_metarig = scn.objects['metarig.001']
        bpy.ops.object.select_all(action='DESELECT')

        # Eliminate unwanted head_metarig bones
        head_metarig.select = True
        scn.objects.active = head_metarig
        bpy.ops.object.mode_set(mode='EDIT')
        face_bones = find_face_bones(head_metarig)

        bpy.ops.armature.select_all(action='DESELECT')

        for bone in head_metarig.data.edit_bones:
            if bone.name not in face_bones:
                bone.select = True
        bpy.ops.armature.delete()

        # Generate head_metarig: the rig will be updated and contain only the head bones
        bpy.ops.object.mode_set(mode='OBJECT')
        generate_rig(context, head_metarig)
        bpy.ops.object.select_all(action='DESELECT')

        # Get head bone names from rig generated by head_metarig
        rig.select = True
        scn.objects.active = rig
        bpy.ops.object.mode_set(mode='EDIT')
        rig_face_bones = rig.data.edit_bones.keys()
        rig_face_bones.remove('root')
        rig.data.edit_bones.remove(rig.data.edit_bones['root'])
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        # Eliminate head bones from body rig (rig.001) saving parents info first
        body_rig.select = True
        scn.objects.active = body_rig
        bpy.ops.object.mode_set(mode='EDIT')
        layers = []
        for i, lyr in enumerate(body_rig.data.layers):
            layers.append(body_rig.data.layers[i])
            body_rig.data.layers[i]=True
        bone_parents = get_bone_parents(body_rig, rig_face_bones)

        bpy.ops.armature.select_all(action='DESELECT')
        for bone in body_rig.data.edit_bones:
            if bone.name in rig_face_bones:
                bone.select = True

        bpy.ops.armature.delete()
        for i in range(0, 32):
            body_rig.data.layers[i] = layers[i]
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        # Merge the head and body rigs
        rig.select = True
        body_rig.select = True
        scn.objects.active = rig
        bpy.ops.object.join()
        #body_rig.name = 'rig'
        #body_rig.data.name = 'rig'
        #rig = body_rig

        # Restore rig_ui
        duplicate_rig_ui(rig.users_group[0].name.rstrip('_GRP'), scn.NewName, bpy.data.armatures[rig.name]['rig_id'], scn.NewRigID)
        bpy.data.armatures[rig.name]['rig_id'] = scn.NewRigID
        rig.users_group[0].name = scn.NewName + '_GRP'

        # Restore parenting and layers
        bpy.ops.object.select_all(action='DESELECT')
        rig.select = True
        scn.objects.active = rig
        bpy.ops.object.mode_set(mode='EDIT')

        for i in range(0, 32):
            rig.data.layers[i] = layers[i]

        for bone in rig.data.edit_bones:
            if bone.name in bone_parents.keys():
                bone.parent = rig.data.edit_bones[bone_parents[bone.name]]

        # Delete head_metarig
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        head_metarig.select = True
        bpy.ops.object.delete()


        return {'FINISHED'}

def register():

    bpy.types.Scene.NewRigID = bpy.props.StringProperty(name='New rig_id', default='', description='New rig_id')
    bpy.types.Scene.NewName = bpy.props.StringProperty(name='New name', default='', description='New name')
    bpy.utils.register_class(Duplicate_CHR)
    bpy.utils.register_class(Generate_rig_id)
    bpy.utils.register_class(Grab_rig_info)
    bpy.utils.register_class(Update_CHR)
    bpy.utils.register_class(Face_off)

def unregister():
    bpy.utils.unregister_class(Duplicate_CHR)
    bpy.utils.unregister_class(Generate_rig_id)
    bpy.utils.unregister_class(Grab_rig_info)
    bpy.utils.unregister_class(Update_CHR)
    bpy.utils.unregister_class(Face_off)


if __name__ == "__main__":
    register()
