

# make sure to put packages in setup.py
import os
import math
import time
import sys
import traceback
import argparse
import builtins
import bpy
from mathutils import Vector, Matrix, Euler

# region Globals
def test12345():
  msg("hi")

def test():
  msg("hi")

def dbg(str):
  _msg("[D] " + str)


def msg(str):
  _msg("[I] " + str)


def _msg(str):
  builtins.print(str)
  sys.stdout.flush()
  time.sleep(0)


def throw(ex):
  raise Exception("Exception: " + ex)

# endregion
# region Classes


class Blender:
  # blender utilities

  def set_frame(sample):
    # frame_set is slowest this method comes first
    bpy.context.scene.frame_set(int(sample), subframe=math.fmod(sample, 1))
    bpy.context.view_layer.update()

  def getMinKeyframeForAction(curAction):
    iRet = 9999999
    for fcu in curAction.fcurves:
      for keyf in fcu.keyframe_points:
        x, y = keyf.co
        if x < iRet:
          iRet = x
    return int(iRet)

  def getMaxKeyframeForAction(curAction):
    iRet = -9999999
    for fcu in curAction.fcurves:
      for keyf in fcu.keyframe_points:
        x, y = keyf.co
        if x > iRet:
          iRet = x
    return int(iRet)

  def active_object():
    return bpy.context.view_layer.objects.active

  def blendFileIsOpen():
    return bpy.data.filepath

  def get_shader_node_image_input(node):
    img = None
    for input in node.links:
      if type(input.from_node) is bpy.types.ShaderNodeTexImage:  # .type== 'TEX_IMAGE'
        img = input.from_node.image
    return img


class Utils:
  # generic utilities
  M_2PI = float(math.pi * 2)

  def printObj(obj):
    if hasattr(obj, '__dict__'):
      for k, v in obj.__dict__.items():
        msg(str(k) + "," + str(v))
        Utils.printObj(v)
    else:
      msg(str(dir(obj)))

  def millis():
    return int(round(time.time() * 1000))

  def debugDumpMatrix(str, in_matrix):
    # return ""
    strDebug = ""
    loc, rot, sca = in_matrix.decompose()
    strDebug += "\n\n"
    strDebug += "#" + str + " mat\n" + Convert.matToString(in_matrix.to_4x4(), ",", True) + "\n"
    strDebug += "#  loc     (" + Convert.vec3ToString(loc) + ")\n"
    strDebug += "#  quat    (" + Convert.vec4ToString(rot) + ")\n"

    strDebug += "#gl_quat:  (" + Convert.vec4ToString(Convert.glQuat(rot)) + ")\n"
    strDebug += "#to_euler_deg: (" + Convert.vec3ToString(euler3ToDeg(rot.to_euler("XYZ"))) + ")\n"
    strDebug += "#gl_euler_deg: (" + Convert.vec3ToString(euler3ToDeg(Convert.glEuler3(rot.to_euler()))) + ")\n"

    strDebug += "#AxAng(Blender) " + Convert.vec3ToString(Convert.glVec3(in_matrix.to_quaternion().axis))
    strDebug += "," + Convert.fPrec() % ((180.0) * in_matrix.to_quaternion().angle / 3.14159)
    strDebug += "\n"

    strDebug += "#Ax,Ang(conv)   " + Convert.vec3ToString(Convert.glVec3(Convert.glMat4(in_matrix).to_quaternion().axis))
    strDebug += "," + Convert.fPrec() % ((180.0) * Convert.glMat4(in_matrix).to_quaternion().angle / 3.14159)
    strDebug += "\n"

    return strDebug

  def getFileInfo():
    # print info aobut .blend file in JSON format
    if bpy.context.mode != 'OBJECT':
      bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    # JSON
    strOut = "$3{\"Objects\":["
    app1 = ""
    for ob in bpy.context.visible_objects:
      print("Found " + ob.name + " Type = " + str(ob.type))
      if ob != None:
        if ob.type == 'MESH' or ob.type == 'ARMATURE':
          strOut += app1 + "{"
          strOut += "\"Name\":\"" + ob.name + "\","
          strOut += "\"Type\":\"" + ob.type + "\","
          strOut += "\"Checked\":\"False\","
          strOut += "\"Actions\":["
          if ob.animation_data != None:
            if ob.animation_data.nla_tracks != None:
              for nla in ob.animation_data.nla_tracks:
                nla.select = True
                app2 = ""
                for strip in nla.strips:
                  curAction = strip.action
                  strOut += app2 + "{\"Name\":\"" + \
                    curAction.name + "\", \"Checked\":\"False\"}"
                  app2 = ","

          strOut += "]"
          strOut += "}"
          app1 = ","
    strOut = strOut + "]}$3"

    print(strOut)

  def printExcept(e):
    extype = type(e)
    tb = e.__traceback__
    traceback.print_exception(extype, e, tb)
    return
    msg(str(e))
    exc_tb = sys.exc_info()  # in python 3 - __traceback__
    print(str(exc_tb))
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print("fname=" + fname)
    msg(fname + " line " + str(exc_tb.tb_lineno))
    msg(traceback.format_exc())
    sys.exc_clear()

  def getArgs():
    argv = sys.argv
    if "--" not in argv:
      argv = []
    else:
      argv = argv[argv.index("--") + 1:]
    parser = argparse.ArgumentParser(description="MRT sprite baker")
    parser.add_argument("-b", dest="blendfile", type=str,
                        required=False, help=".blend file")
    parser.add_argument("-o", dest="outpath", type=str,
                        required=False, help="output path")
    parser.add_argument("-s", dest="settingspath", type=str, required=False,
                        help="Settings save directory. Default: blendfile directory")
    args = parser.parse_args(argv)

    return args


class Convert:
  def fPrec():
    return "%.8f"

  def matToString(mat, delim=',', sp=False):
    strRet = ""
    mat_4 = mat.to_4x4()
    strApp = ""
    for row in range(4):
      if sp == True:
        strRet += "#"
      for col in range(4):
        # strRet += str(row) + " " + str(col)
        strFormat = "" + strApp + fPrec() + ""
        strRet += strFormat % mat_4[row][col]
        strApp = delim
      if sp == True:
        strRet += "\n"
    return strRet

  def floatToString(float):
    strFormat = "" + fPrec() + ""
    strRet = strFormat % (float)
    return strRet

  def vec4ToString(vec4, delim=' '):
    strRet = ""
    strFormat = "" + fPrec() + delim + fPrec() + delim + fPrec() + delim + fPrec() + ""
    strRet = strFormat % (vec4.x, vec4.y, vec4.z, vec4.w)
    return strRet

  def vec3ToString(vec3, delim=' '):
    strRet = ""
    strFormat = "" + fPrec() + delim + fPrec() + delim + fPrec() + ""
    strRet = strFormat % (vec3.x, vec3.y, vec3.z)
    return strRet

  def color3ToString(vec3, delim=' '):
    strRet = ""
    strFormat = "" + fPrec() + delim + fPrec() + delim + fPrec() + ""
    strRet = strFormat % (vec3.r, vec3.g, vec3.b)
    return strRet

  def vec2ToString(vec2, delim=' '):
    strRet = ""
    strFormat = "" + fPrec() + delim + fPrec() + ""
    strRet = strFormat % (vec2.x, vec2.y)
    return strRet

  def glEuler3(eu, yup):
    # NOTE: use Deep exploration to test- same coordinate system as vault
    # Convert Vec3 tgo OpenGL coords
    # -x,-z,-y is the correct export into deep expl
    # This is the correct OpenGL conversion
    if yup:  # self._config._convertY_Up:
      ret = Euler([eu.x, eu.y, eu.z])
      tmp = ret.y
      ret.y = ret.z
      ret.z = tmp
      return ret
    else:
      return eu

  def glQuat(quat, yup):
    if yup:  # self._config._convertY_Up:
      e = quat.to_euler()
      e = glEuler3(e)
      return e.to_quaternion()
    else:
      return quat

  def glVec3(vec, yup):
    # NOTE: use Deep exploration to test- same coordinate system as vault
    # Convert Vec3 tgo OpenGL coords
    ret = Vector([vec.x, vec.y, vec.z])

    # -x,-z,-y is the correct export into deep expl
    # This is the correct OpenGL conversion
    if yup:  # self._config._convertY_Up
      tmp = ret.y
      ret.y = ret.z
      ret.z = tmp
      ret.x = ret.x

    return ret

  def glMat4(in_mat, yup):
    # NOTE this functio works
     # global_matrix = io_utils.axis_conversion(to_forward="-Z", to_up="Y").to_4x4()
     # mat_conv = global_matrix * in_mat * global_matrix.inverted()
     # mat_conv = mat_conv.transposed()
     # return mat_conv

    # NOTE: t12/20/17 this actually works but seems to return a negative z value?

    # NOTE: use Deep exploration to test- same coordinate system as vault
    # convert matrix from Blender to OpenGL Coords
    m1 = in_mat.copy()
    m1 = m1.to_4x4()

    x = 0
    y = 1
    z = 2
    w = 3

    # change of basis matrix
    if yup:  # self._config._convertY_Up:
      cbm = Matrix.Identity(4)
      cbm[x][0] = 1
      cbm[x][1] = 0
      cbm[x][2] = 0
      cbm[x][3] = 0

      cbm[y][0] = 0
      cbm[y][1] = 0
      cbm[y][2] = 1
      cbm[y][3] = 0

      cbm[z][0] = 0
      cbm[z][1] = 1
      cbm[z][2] = 0
      cbm[z][3] = 0

      cbm[w][0] = 0
      cbm[w][1] = 0
      cbm[w][2] = 0
      cbm[w][3] = 1

      # multiply CBM twice
      m1 = cbm.inverted() * m1 * cbm.inverted()

    # blender is row-major?
   # m1.transpose()

    return m1

# endregion
