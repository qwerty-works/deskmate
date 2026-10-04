# @name Pumpkin Chomp
# @desc A jack-o'-lantern grows, chews twice, and shrinks into a spark.
# @author Deskmate
# @version 1.0.0
# @display 32x8
# @config durationMs number "Duration" default=5000 min=1000 max=5000 step=100 unit=ms

class App
  var started, ms

  def init()
    self.started = now_ms()
    self.ms = 5000
  end

  def duration()
    var v = int(store.get('durationMs', 5000))
    if v < 1000 v = 1000 end
    if v > 5000 v = 5000 end
    return v
  end

  def on_show()
    self.ms = self.duration()
    self.started = now_ms()
  end

  def draw()
    clear()
    var t = (now_ms() - self.started) * 1.0 / self.ms
    if t < 0 t = 0 end
    if t > 1 t = 1 end
    if t >= 0.97 return end
    var size = 1.0
    if t < 0.22 size = t / 0.22 end
    if t > 0.78 size = (0.95 - t) / 0.17 end
    if size < 0
      pixel(15, 4, 0xFF8818)
      return
    end
    var cx = int(width() / 2)
    var cy = int(height() / 2)
    var rx = int(7 * size)
    var ry = int(3 * size)
    if rx < 1 rx = 1 end
    if ry < 1 ry = 1 end
    # Stepped shoulders and rounded corners stay crisp at eight pixels tall.
    for y : -ry..ry
      var inset = 0
      if y == -ry || y == ry inset = 2 end
      var left = cx - rx + inset
      var right = cx + rx - inset
      if right >= left rect_fill(left, cy + y, right - left + 1, 1, 0xFF8818) end
    end
    if size > 0.85
      # Two mischievous embers creep toward the pumpkin during the suspense.
      var drift = int((t - 0.22) * 12)
      if drift < 0 drift = 0 end
      var lift = int(t * 18) % 3
      pixel(cx - 12 + drift, cy - 2 + lift, 0xA855F7)
      pixel(cx + 12 - drift, cy + 2 - lift, 0xA855F7)
      pixel(cx, cy - 4, 0x94E044)
      pixel(cx + 1, cy - 4, 0x94E044)
      # Eyes lean inward; a squint adds anticipation before each bite.
      pixel(cx - 4, cy - 2, 0)
      pixel(cx - 3, cy - 2, 0)
      pixel(cx - 3, cy - 1, 0)
      pixel(cx + 3, cy - 2, 0)
      pixel(cx + 4, cy - 2, 0)
      pixel(cx + 3, cy - 1, 0)
      pixel(cx, cy, 0)
      var open = (t >= 0.31 && t < 0.43) || (t >= 0.58 && t < 0.70)
      if open
        rect_fill(cx - 4, cy + 1, 9, 2, 0)
        pixel(cx - 2, cy + 1, 0xFF8818)
        pixel(cx + 2, cy + 1, 0xFF8818)
        pixel(cx, cy + 2, 0xFF8818)
      else
        line(cx - 4, cy + 1, cx + 4, cy + 1, 0)
        pixel(cx - 3, cy + 2, 0)
        pixel(cx + 3, cy + 2, 0)
      end
    end
  end
end

return App()
