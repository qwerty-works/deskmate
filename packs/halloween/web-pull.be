# @name Web Pull
# @desc Two curious spiders drop in, dance on violet threads, and zip away.
# @author Deskmate
# @version 1.0.0
# @display 32x8
# @config durationMs number "Duration" default=5000 min=1000 max=5000 step=100 unit=ms

class App
  var started, ms

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

  def spider(x, y, wiggle, color)
    # The little leg tips alternate without flashing the body.
    if y < -3 return end
    if y > 0 line(x, 0, x, y - 1, 0xA855F7) end
    rect_fill(x - 1, y, 3, 2, color)
    pixel(x - 1, y, 0xDDF8F5)
    pixel(x + 1, y, 0xDDF8F5)
    pixel(x - 2, y - 1 + wiggle, color)
    pixel(x + 2, y - 1 + wiggle, color)
    pixel(x - 2, y + 2 - wiggle, color)
    pixel(x + 2, y + 2 - wiggle, color)
    pixel(x, y + 2, color)
  end

  def draw()
    clear()
    if self.started == nil self.on_show() end
    var t = (now_ms() - self.started) * 1.0 / self.ms
    if t < 0 t = 0 end
    if t >= 1 return end
    var first = -4
    var second = -4
    var beat = int(t * 22)
    if t < 0.32
      first = int(-4 + 8 * t / 0.32)
    elif t < 0.74
      first = 3 + (beat % 3 == 1 ? 1 : 0)
    else
      first = int(4 - 11 * (t - 0.74) / 0.20)
    end
    if t > 0.10 && t < 0.38
      second = int(-4 + 7 * (t - 0.10) / 0.28)
    elif t >= 0.38 && t < 0.78
      second = 3 + (beat % 3 == 2 ? 1 : 0)
    elif t >= 0.78
      second = int(4 - 11 * (t - 0.78) / 0.18)
    end
    var step = int(t * 20) % 2
    self.spider(8, first, step, 0xFF8818)
    self.spider(23, second, 1 - step, 0x94E044)
  end
end

return App()
