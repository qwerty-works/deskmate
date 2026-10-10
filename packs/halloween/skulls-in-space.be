# @name Skulls in Space
# @desc Small skulls drift through empty space, with size, brightness, and speed creating depth.
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

  def draw_small(cx, top, color)
    # A compact five-by-five version of the stepped reference skull.
    rect_fill(cx - 1, top, 3, 1, color)
    rect_fill(cx - 2, top + 1, 5, 3, color)
    pixel(cx - 1, top + 2, 0)
    pixel(cx + 1, top + 2, 0)
    pixel(cx, top + 3, 0)
    pixel(cx - 2, top + 4, color)
    pixel(cx - 1, top + 4, color)
    pixel(cx + 1, top + 4, color)
    pixel(cx + 2, top + 4, color)
  end

  def draw_medium(cx, top, color)
    # A seven-by-six version with broad eye sockets and separated teeth.
    rect_fill(cx - 1, top, 3, 1, color)
    rect_fill(cx - 3, top + 1, 7, 4, color)
    rect_fill(cx - 2, top + 5, 2, 1, color)
    pixel(cx + 1, top + 5, color)
    pixel(cx + 2, top + 5, color)
    rect_fill(cx - 2, top + 2, 2, 2, 0)
    rect_fill(cx + 1, top + 2, 2, 2, 0)
    pixel(cx, top + 4, 0)
  end

  def draw_large(cx, top, color)
    # An eleven-by-seven foreground version closest to the supplied reference.
    rect_fill(cx - 1, top, 3, 1, color)
    rect_fill(cx - 3, top + 1, 7, 1, color)
    rect_fill(cx - 4, top + 2, 9, 1, color)
    rect_fill(cx - 5, top + 3, 11, 2, color)
    rect_fill(cx - 4, top + 5, 9, 1, color)
    pixel(cx - 4, top + 3, 0)
    pixel(cx - 3, top + 3, 0)
    pixel(cx - 2, top + 3, 0)
    pixel(cx + 2, top + 3, 0)
    pixel(cx + 3, top + 3, 0)
    pixel(cx + 4, top + 3, 0)
    pixel(cx - 4, top + 4, 0)
    pixel(cx - 3, top + 4, 0)
    pixel(cx - 2, top + 4, 0)
    pixel(cx + 2, top + 4, 0)
    pixel(cx + 3, top + 4, 0)
    pixel(cx + 4, top + 4, 0)
    pixel(cx, top + 5, 0)
    pixel(cx - 3, top + 6, color)
    pixel(cx - 2, top + 6, color)
    pixel(cx, top + 6, color)
    pixel(cx + 2, top + 6, color)
    pixel(cx + 3, top + 6, color)
  end

  def draw()
    clear()
    var t = (now_ms() - self.started) * 1.0 / self.ms
    if t < 0 t = 0 end
    if t > 1 t = 1 end

    # The one-pixel skulls are farthest away: dimmest and slowest.
    if t >= 0.03 && t < 0.95
      var far = (t - 0.03) / 0.92
      pixel(int(-1 + far * (width() + 2)), 0, 0x252525)
    end
    if t >= 0.28 && t < 0.98
      var far2 = (t - 0.28) / 0.70
      pixel(int(-1 + far2 * (width() + 2)), 7, 0x303030)
    end

    # Smaller readable skulls move more slowly than the foreground skull.
    if t >= 0.08 && t < 0.73
      var middle = (t - 0.08) / 0.65
      self.draw_small(int(-3 + middle * (width() + 6)), 2, 0x777777)
    end
    if t >= 0.38 && t < 0.86
      var near = (t - 0.38) / 0.48
      self.draw_medium(int(-4 + near * (width() + 8)), 1, 0xB8B8B8)
    end
    if t >= 0.22 && t < 0.60
      var front = (t - 0.22) / 0.38
      self.draw_large(int(-5 + front * (width() + 10)), 1, 0xFFFFFF)
    end
  end
end

return App()
