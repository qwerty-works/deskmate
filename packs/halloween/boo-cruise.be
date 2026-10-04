# @name Boo Cruise
# @desc A friendly ghost floats in, spots you, gives a tiny boo and scoots away.
# @author Deskmate
# @version 1.0.0
# @display 32x8
# @config durationMs number "Duration (ms)" default=5000 min=1000 max=5000

class App
  var started, ms

  def init()
    self.started = 0
    self.ms = 5000
  end

  def duration()
    var value = int(store.get('durationMs', 5000))
    if value < 1000 value = 1000 end
    if value > 5000 value = 5000 end
    return value
  end

  def on_show()
    self.ms = self.duration()
    self.started = now_ms()
  end

  def draw()
    clear(0x000000)
    var t = (now_ms() - self.started) * 1.0 / self.ms
    if t < 0 t = 0 end
    if t > 1 t = 1 end
    var bob = int(t * 12) % 2
    var x = 12
    if t < 0.25
      x = int(t * 80) - 8
    elif t > 0.65
      x = int(12 + (t - 0.65) * 88)
    else
      x = 12 + (int(t * 10) % 2)
    end
    var y = bob
    # Rounded head, skirt and alternating scalloped hem, seven pixels tall.
    rect_fill(x + 2, y, 3, 1, 0xDDF8F5)
    rect_fill(x + 1, y + 1, 5, 5, 0xDDF8F5)
    pixel(x + 1, y + 6, 0xDDF8F5)
    pixel(x + 3, y + 6 - bob, 0xDDF8F5)
    pixel(x + 5, y + 6, 0xDDF8F5)
    pixel(x + 1, y + 4, 0xA855F7)
    # In transit, both eyes look right. At center the ghost faces the viewer.
    var gaze = 1
    if t >= 0.29 && t <= 0.64 gaze = 0 end
    pixel(x + 2 + gaze, y + 2, 0x000000)
    pixel(x + 4 + gaze, y + 2, 0x000000)
    if t > 0.40 && t < 0.54
      # Arms pop up and an orange round mouth delivers a silent "boo".
      pixel(x, y + 2, 0xDDF8F5)
      pixel(x + 6, y + 2, 0xDDF8F5)
      pixel(x + 3, y + 4, 0xFF8818)
      pixel(x - 3, y + 1, 0xA855F7)
      pixel(x + 9, y + 1, 0xA855F7)
    else
      pixel(x, y + 3, 0xDDF8F5)
      pixel(x + 6, y + 3, 0xDDF8F5)
      pixel(x + 3, y + 4, 0x000000)
    end
    # Two little sparkles settle after the greeting, then vanish before exit.
    if t > 0.54 && t < 0.64
      pixel(x - 3, 2, 0x94E044)
      pixel(x + 9, 4, 0xA855F7)
    end
  end
end

return App()
