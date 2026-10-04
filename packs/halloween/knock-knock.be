# @name Knock Knock
# @desc A haunted door creaks open to a watchful visitor, then slams shut.
# @author Deskmate
# @version 1.1.0
# @display 32x8
# @config durationMs number "Duration" default=5000 min=1000 max=5000 step=100 unit=ms

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
    var cx = int(width() / 2), y = height() - 8
    var extent = 4
    if t < 0.14 extent = int(1 + 3 * t / 0.14) end
    if t > 0.87 extent = int(4 * (1 - t) / 0.13) end
    if extent < 1 return end
    var shake = 0
    if t > 0.17 && t < 0.31 shake = int(t * 35) % 3 - 1 end
    cx += shake
    line(cx - extent, y, cx + extent, y, 0xFF8818)
    line(cx - extent, y, cx - extent, y + 7, 0xFF8818)
    line(cx + extent, y, cx + extent, y + 7, 0xFF8818)
    line(cx - extent, y + 7, cx + extent, y + 7, 0xFF8818)
    var opening = 0
    if t > 0.30 && t < 0.56 opening = int(6 * (t - 0.30) / 0.26) end
    if t >= 0.56 && t < 0.74 opening = 6 end
    if t >= 0.74 && t < 0.84 opening = int(6 * (0.84 - t) / 0.10) end
    var slab = extent * 2 - 1 - opening
    if slab > 0
      rect_fill(cx - extent + 1, y + 1, slab, 6, 0xA855F7)
      pixel(cx - extent + slab, y + 4, 0xFF8818)
    end
    if t > 0.46 && t < 0.74
      var gaze = int((t - 0.46) * 12) % 2
      line(cx + gaze, y + 3, cx + 2 + gaze, y + 3, 0xDDF8F5)
      pixel(cx + 1 + gaze, y + 3, 0x94E044)
      if t > 0.62
        pixel(cx + 1, y + 5, 0xA855F7)
        pixel(cx, y + 6, 0xA855F7)
        pixel(cx + 2, y + 6, 0xA855F7)
      end
    end
    # Dust creeps toward the threshold; the slam sends it away.
    for i : 0..3
      var travel = int(t * 24 + i * 7) % 12
      var side = i % 2 == 0 ? -1 : 1
      var px = cx + side * (5 + travel)
      var py = y + 6 - (i % 3)
      if t < 0.84 pixel(px, py, 0xA855F7) end
    end
  end
end
return App()
