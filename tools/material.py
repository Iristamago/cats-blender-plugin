# MIT License

# Copyright (c) 2017 GiveMeAllYourCats

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the 'Software'), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Code author: GiveMeAllYourCats
# Repo: https://github.com/michaeldegroot/cats-blender-plugin

# Code author: Michael Williamson
# Repo: https://github.com/scorpion81/blender-addons/blob/master/space_view3d_materials_utils.py
# Edits by: GiveMeAllYourCats

import bpy
import tools.common


class OneTexPerMatButton(bpy.types.Operator):
    bl_idname = 'one.tex'
    bl_label = 'One Material Texture'
    bl_description = 'Have all material slots ignore extra texture slots as these are not used by VRChat'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        if tools.common.get_armature() is None:
            return False
        return len(tools.common.get_meshes_objects()) > 0

    def execute(self, context):
        tools.common.set_default_stage()

        for mesh in tools.common.get_meshes_objects():
            for mat_slot in mesh.material_slots:
                for i, tex_slot in enumerate(mat_slot.material.texture_slots):
                    if i > 0 and tex_slot:
                        mat_slot.material.use_textures[i] = False

        self.report({'INFO'}, 'All materials have one texture now.')
        return{'FINISHED'}


class OneTexPerMatOnlyButton(bpy.types.Operator):
    bl_idname = 'one.tex_only'
    bl_label = 'One Material Texture'
    bl_description = 'Have all material slots ignore extra texture slots as these are not used by VRChat.' \
                     '\nAlso removes the textures from the material instead of disabling it.' \
                     '\nThis makes no difference, but cleans the list for the perfectionists'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        if tools.common.get_armature() is None:
            return False
        return len(tools.common.get_meshes_objects()) > 0

    def execute(self, context):
        tools.common.set_default_stage()

        for mesh in tools.common.get_meshes_objects():
            for mat_slot in mesh.material_slots:
                for i, tex_slot in enumerate(mat_slot.material.texture_slots):
                    if i > 0 and tex_slot:
                        tex_slot.texture = None

        self.report({'INFO'}, 'All materials have one texture now.')
        return{'FINISHED'}


class StandardizeTextures(bpy.types.Operator):
    bl_idname = 'textures.standardize'
    bl_label = 'Standardize Textures'
    bl_description = 'Enables Color and Alpha on every texture, sets the blend method to Multiply' \
                     '\nand changes the materials transparency to Z-Transparency'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        if tools.common.get_armature() is None:
            return False
        return len(tools.common.get_meshes_objects()) > 0

    def execute(self, context):
        tools.common.set_default_stage()

        for mesh in tools.common.get_meshes_objects():
            for mat_slot in mesh.material_slots:

                mat_slot.material.transparency_method = 'Z_TRANSPARENCY'
                mat_slot.material.alpha = 1

                for tex_slot in mat_slot.material.texture_slots:
                    if tex_slot:
                        tex_slot.use_map_alpha = True
                        tex_slot.use_map_color_diffuse = True
                        tex_slot.blend_type = 'MULTIPLY'

        self.report({'INFO'}, 'All textures are now standardized.')
        return{'FINISHED'}


class CombineMaterialsButton(bpy.types.Operator):
    bl_idname = 'combine.mats'
    bl_label = 'Combine Same Materials'
    bl_description = 'Combines similar materials into one, reducing draw calls.\n' \
                     'Your avatar should visibly look the same after this operation.\n' \
                     'This is a very important step for optimizing your avatar.\n' \
                     'If you have problems with this, please tell us!\n'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    combined_tex = {}

    @classmethod
    def poll(cls, context):
        if tools.common.get_armature() is None:
            return False
        return len(tools.common.get_meshes_objects()) > 0

    def assignmatslots(self, ob, matlist):
        scn = bpy.context.scene
        ob_active = bpy.context.active_object
        scn.objects.active = ob

        for s in ob.material_slots:
            bpy.ops.object.material_slot_remove()

        i = 0
        for m in matlist:
            mat = bpy.data.materials[m]
            ob.data.materials.append(mat)
            i += 1

        scn.objects.active = ob_active

    def cleanmatslots(self):
        objs = bpy.context.selected_editable_objects

        for ob in objs:
            if ob.type == 'MESH':
                mats = ob.material_slots.keys()

                usedMatIndex = []
                faceMats = []
                me = ob.data
                for f in me.polygons:
                    faceindex = f.material_index

                    currentfacemat = mats[faceindex]
                    faceMats.append(currentfacemat)

                    found = 0
                    for m in usedMatIndex:
                        if m == faceindex:
                            found = 1

                    if found == 0:
                        usedMatIndex.append(faceindex)

                ml = []
                mnames = []
                for u in usedMatIndex:
                    ml.append(mats[u])
                    mnames.append(mats[u])

                self.assignmatslots(ob, ml)

                i = 0
                for f in me.polygons:
                    matindex = mnames.index(faceMats[i])
                    f.material_index = matindex
                    i += 1

    # Iterates over each material slot and hashes combined image filepaths and material settings
    # Then uses this hash as the dict keys and material data as values
    def generate_combined_tex(self):
        self.combined_tex = {}
        for ob in bpy.data.objects:
            for index, mat_slot in enumerate(ob.material_slots):
                hash_this = ''
                for tex_index, mtex_slot in enumerate(mat_slot.material.texture_slots):
                    if mtex_slot:
                        if mat_slot.material.use_textures[tex_index]:
                            if hasattr(mtex_slot.texture, 'image') and bpy.data.materials[mat_slot.name].use_textures[tex_index] and mtex_slot.texture.image:
                                hash_this += mtex_slot.texture.image.filepath   # Filepaths makes the hash unique
                hash_this += str(mat_slot.material.alpha)           # Alpha setting on material makes the hash unique
                hash_this += str(mat_slot.material.specular_color)  # Specular color makes the hash unique
                hash_this += str(mat_slot.material.diffuse_color)   # Diffuse color makes the hash unique

                # print('---------------------------------------------------')
                # print(mat_slot.name, hash_this)

                # Now create or add to the dict key that has this hash value
                if hash_this not in self.combined_tex:
                    self.combined_tex[hash_this] = []
                self.combined_tex[hash_this].append({'mat': mat_slot.name, 'index': index})

        # print('CREATED COMBINED TEX', self.combined_tex)

    def execute(self, context):
        tools.common.set_default_stage()
        self.generate_combined_tex()
        tools.common.switch('OBJECT')
        i = 0

        for index, obj in enumerate(tools.common.get_meshes_objects()):

            tools.common.unselect_all()
            tools.common.select(obj)
            for file in self.combined_tex:  # for each combined mat slot of scene object
                combined_textures = self.combined_tex[file]

                # Combining material slots that are similar with only themselves are useless
                if len(combined_textures) <= 1:
                    continue
                i += len(combined_textures)

                # print('NEW', file, combined_textures, len(combined_textures))
                tools.common.switch('EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                # print('UNSELECT ALL')
                for mat in bpy.context.object.material_slots:  # for each scene object material slot
                    for tex in combined_textures:
                        if mat.name == tex['mat']:
                            bpy.context.object.active_material_index = tex['index']
                            bpy.ops.object.material_slot_select()
                            # print('SELECT', tex['mat'], tex['index'])

                bpy.ops.object.material_slot_assign()
                # print('ASSIGNED TO SLOT INDEX', bpy.context.object.active_material_index)
                bpy.ops.mesh.select_all(action='DESELECT')

            tools.common.unselect_all()
            tools.common.select(obj)
            tools.common.switch('OBJECT')
            self.cleanmatslots()

            # Clean material names
            for j, mat in enumerate(bpy.context.object.material_slots):
                if mat.name.endswith('.001'):
                    bpy.context.object.active_material_index = j
                    bpy.context.object.active_material.name = mat.name[:-4]
                if mat.name.endswith('. 001') or mat.name.endswith(' .001'):
                    bpy.context.object.active_material_index = j
                    bpy.context.object.active_material.name = mat.name[:-5]

            # print('CLEANED MAT SLOTS')

        if i == 0:
            self.report({'INFO'}, 'No materials combined.')
        else:
            self.report({'INFO'}, 'Combined ' + str(i) + ' materials!')

        return{'FINISHED'}
