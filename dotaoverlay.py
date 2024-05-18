#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import imgui
import glfw
import OpenGL.GL as gl
from imgui.integrations.glfw import GlfwRenderer
import simpleaudio as sa

from PIL import ImageGrab
import PIL as pil
import pytesseract

class Bundle:
  def __init__(self):
    self.imgCampStack = Bundle.loadImageGl("campstack.png")
    self.imgCampWalk = Bundle.loadImageGl("campwalk.png")
    self.imgPowerRune = Bundle.loadImageGl("powerrune.png")
    self.imgHealingLotus = Bundle.loadImageGl("healinglotus.png")
    self.imgWisdomRune = Bundle.loadImageGl("wisdomrune.png")

    self.sndCampStack = sa.WaveObject.from_wave_file("campstack.wav") #
    self.sndCampWalk = sa.WaveObject.from_wave_file("campwalk.wav") #
    self.sndPowerRune = sa.WaveObject.from_wave_file("powerrune.wav") #
    self.sndHealingLotus = sa.WaveObject.from_wave_file("healinglotus.wav") #
    self.sndWisdomRune = sa.WaveObject.from_wave_file("wisdomrune.wav") #
    self.sndIntro = sa.WaveObject.from_wave_file("intro.wav") #

  def loadImageGl(path):
    img = pil.Image.open(path)
    img_data = img.tobytes("raw", "RGBA", 0, -1)
    width, height = img.size
    texture = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
    gl.glTexImage2D(
      gl.GL_TEXTURE_2D,
      0, gl.GL_RGBA, width, height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img_data
    )
    return texture

class Time:
  def __init__(self, minutes, seconds):
    self.minutes = minutes
    self.seconds = seconds

class dotaTimingGui: # {
  def displayImage(image : Bundle):
    imgui.set_cursor_pos_y(imgui.get_cursor_pos_y() - 15)
    # display image upside down
    imgui.image(image, 64, 64, uv0=(0, 1), uv1=(1, 0))
    imgui.same_line()
    imgui.set_cursor_pos_y(imgui.get_cursor_pos_y() + 15)
  def walkToCamp(time : Time, bundle : Bundle):
    # walk to camp to pull or stack around X:05-10 and X:35-40
    # this is only important during laning phase
    inRange = (
         (time.seconds >= 5 and time.seconds <= 10)
      or (time.seconds >= 35 and time.seconds <= 40)
    )
    # only matters for 1-9 minutes
    inRange = (inRange and time.minutes < 10 and time.minutes >= 1)
    if (inRange):
      dotaTimingGui.displayImage(bundle.imgCampWalk)
      return bundle.sndCampWalk
    return None
  def stackCamp(time : Time, bundle : Bundle):
    # stack camp around X:45-55
    inRange = time.seconds >= 45 and time.seconds <= 55
    if (inRange):
      dotaTimingGui.displayImage(bundle.imgCampStack)
      return bundle.sndCampStack
    return None
  def powerRune(time : Time, bundle : Bundle):
    # power rune spawns every 2 minutes (first 2 are water runes)
    # so prepare to get it around X:30-60 (for regen especially)
    inRange = (
      (time.minutes % 2 == 1) and (time.seconds >= 30 and time.seconds <= 59)
    )
    if (inRange):
      dotaTimingGui.displayImage(bundle.imgPowerRune)
      return bundle.sndPowerRune
    return None
  def healingLotus(time : Time, bundle : Bundle):
    # the first two healing lotus are important, you need to push your lane
    # in to grab it at around :30
    inRange = (
      (time.minutes == 2 or time.minutes == 5)
      and (time.seconds >= 30 and time.seconds <= 59)
    )
    if (inRange):
      dotaTimingGui.displayImage(bundle.imgHealingLotus)
      return bundle.sndHealingLotus
    return None
  def wisdomRune(time : Time, bundle : Bundle):
    # wisdom rune spawns every 7 minutes, so prepare to get it around X:30-60
    inRange = (
      ((time.minutes+1) % 7 == 0) and (time.seconds >= 30 and time.seconds <= 59)
    )
    inRange = inRange and time.minutes > 0
    if (inRange):
      dotaTimingGui.displayImage(bundle.imgWisdomRune)
      return bundle.sndWisdomRune
    return None
  def all(time : Time, bundle : Bundle):
    events = [
      dotaTimingGui.walkToCamp(time, bundle),
      dotaTimingGui.stackCamp(time, bundle),
      dotaTimingGui.powerRune(time, bundle),
      dotaTimingGui.healingLotus(time, bundle),
      dotaTimingGui.wisdomRune(time, bundle),
    ]
    return events

  def dotaFetchTimestamp():
    global monitorWs
    msize = (monitorWs[2]/2, monitorWs[3]/16)
    moful = (monitorWs[0]+msize[0] - 50, monitorWs[1] + 20)
    moflr = (monitorWs[0]+msize[0] + 50, monitorWs[1] + 50)
    screen = ImageGrab.grab(bbox=(moful[0], moful[1], moflr[0], moflr[1]))
    # grayscale it
    screen = screen.convert('L')
    screen.save("dotaoverlay.png")
    # limit tesseract to only numbers
    text = pytesseract.image_to_string(
      screen, lang='eng', config='--psm 6 -c tessedit_char_whitelist=0123456789:'
    )
    try:
      # strip whitespace
      text = text.strip()
      # strip out :
      text = text.replace(":", "")
      # seconds will always be last two digits
      seconds = int(text[-2:])
      # minutes will be the rest
      minutes = int(text[:-2])
    except:
      return 0
    return minutes*60 + seconds
# } dotaTimingGui


# globals
timeDota = 0
timeGlfwReference = 0

# glfw setup
def glfwInit(window_name="minimal ImGui/GLFW3 example"):
  global monitorWs
  if not glfw.init():
      print("Could not initialize OpenGL context")
      exit(1)

  glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
  glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
  glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
  glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)
  glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, glfw.TRUE)
  # remove decoration
  glfw.window_hint(glfw.DECORATED, glfw.FALSE)
  glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)
  glfw.window_hint(glfw.FLOATING, glfw.TRUE)
  glfw.window_hint(glfw.FOCUSED, glfw.TRUE)
  #glfw.window_hint(glfw.MOUSE_PASSTHROUGH, glfw.TRUE)

  # Create a windowed mode window and its OpenGL context
  monitor = glfw.get_primary_monitor()
  window = glfw.create_window(400, 64, window_name, None, None)
  glfw.make_context_current(window)

  # set window pos to 300 pixels from the left
  monitorWs = glfw.get_monitor_workarea(monitor)
  window_pos = [monitorWs[0], monitorWs[1]]
  window_pos[0] += 140
  window_pos[1] += 1
  glfw.set_window_pos(window, *window_pos)

  return window

prevEvents = None
def processImguiEvent(bundle : Bundle):
  global prevEvents
  # compute time difference between glfw and now, then offset it to dota time
  time = (glfw.get_time() - timeGlfwReference) + timeDota
  time = Time(int(time//60), int(time%60))
  imgui.text(f"Time: {time.minutes:02}:{time.seconds:02}")
  imgui.same_line()
  events = dotaTimingGui.all(time, bundle)
  if (prevEvents == None):
    prevEvents = events
  newEventChange = False
  for i in range(len(events)):
    if (events[i] and not prevEvents[i]):
      (events[i]).play()
  prevEvents = events

# -- hook up pynput --
def hookUpPynput():
  global timeDota, timeGlfwReference
  import pynput
  keycodeY = pynput.keyboard.KeyCode.from_char('y')
  def processFetchTimestampRequest(key):
    global timeDota, timeGlfwReference
    # check if user hit 'y'
    if (key == keycodeY):
      print("fetching dota time")
      timeDota = dotaTimingGui.dotaFetchTimestamp()
      timeGlfwReference = glfw.get_time()

  listener = (
    pynput.keyboard.Listener(
      on_press=None,
      on_release=processFetchTimestampRequest,
    )
  )
  listener.start()
  return listener

# -- imgui main --
def imguiMain():
  window = glfwInit()
  imgui.create_context()
  impl = GlfwRenderer(window)
  gl.glClearColor(0.0, 0.0, 0.0, 0.0)
  bundle = Bundle()
  (bundle.sndIntro).play()

  while not glfw.window_should_close(window):
    glfw.poll_events()
    impl.process_inputs()
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    imgui.new_frame()
    # create window that has no decoration, no title, no close button
    #   and is at position 0, 0
    imgui.set_next_window_position(0, 0)
    imgui.set_next_window_size(400, 50)
    imgui.begin(
      "Custom window",
      flags= (
          imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE
        | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_MOVE
        | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
        | imgui.WINDOW_ALWAYS_AUTO_RESIZE
        | imgui.WINDOW_NO_FOCUS_ON_APPEARING
        | imgui.WINDOW_NO_NAV
        | imgui.WINDOW_NO_BACKGROUND
        | imgui.WINDOW_NO_SAVED_SETTINGS
        | imgui.WINDOW_NO_SCROLLBAR
      )
    )
    processImguiEvent(bundle)
    imgui.end()
    imgui.render()
    impl.render(imgui.get_draw_data())
    glfw.swap_buffers(window)
    # sleep to reduce cpu usage, only need an update each second anyway
    import time
    time.sleep(1)

  impl.shutdown()
  glfw.terminate()

if __name__ == "__main__":
  listener = hookUpPynput()
  imguiMain()
