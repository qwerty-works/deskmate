# @name Hex Spin
# @desc Twin neon spirals wind into a rotating occult sigil and scatter into sparks.
# @author Deskmate
# @version 1.1.0
# @display 32x8
# @config durationMs number "Duration" default=5000 min=1000 max=5000 step=100 unit=ms

import math

class App
  var started, ms
  def init()
    self.started = now_ms()
    self.ms = self.duration()
  end
  def duration()
    var value = int(store.get('durationMs'))
    if value < 1000 value = 1000 end
    if value > 5000 value = 5000 end
    return value
  end
  def on_show()
    self.started = now_ms()
    self.ms = self.duration()
  end
  def draw()
    clear()
    var t = (now_ms() - self.started) * 1.0 / self.ms
    if t < 0 t = 0 end
    if t >= 1 return end
    var cx = (width() - 1) * 0.5, cy = (height() - 1) * 0.5
    var envelope = 1.0
    if t < 0.18 envelope = t / 0.18 end
    if t > 0.78 envelope = (1 - t) / 0.22 end
    # Two opposing stepped spirals form a compact animated sigil.
    for arm : 0..1
      var oldx = int(cx), oldy = int(cy)
      for k : 1..36
        var r = k / 36.0
        var angle = r * 8.5 - t * 13 + arm * 3.14159
        var x = int(cx + math.cos(angle) * r * (width() * 0.44) * envelope)
        var y = int(cy + math.sin(angle) * r * ((height() - 1) * 0.5) * envelope)
        var color = arm == 0 ? 0xA855F7 : 0x94E044
        if k > 29 color = 0xFF8818 end
        line(oldx, oldy, x, y, color)
        oldx = x oldy = y
      end
    end
    pixel(int(cx), int(cy), 0xDDF8F5)
    if t > 0.78
      for k : 0..5
        var angle = k * 1.0472 + t * 3
        var r = (t - 0.78) / 0.22
        pixel(int(cx + math.cos(angle) * r * width() * 0.46),
              int(cy + math.sin(angle) * r * height() * 0.45), 0xFF8818)
      end
    end
  end
end
return App()
