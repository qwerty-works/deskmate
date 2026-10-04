# @name Who's There?
# @desc Watchful eyes blink in the dark before a tiny ghost peeks in.
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

  def eyes(x, y, look, closed, color)
    if closed
      line(x, y + 1, x + 2, y + 1, color)
      line(x + 5, y + 1, x + 7, y + 1, color)
    else
      rect_fill(x, y, 3, 2, color)
      rect_fill(x + 5, y, 3, 2, color)
      pixel(x + look, y + 1, 0)
      pixel(x + 5 + look, y + 1, 0)
    end
  end

  def ghost(x, y)
    rect_fill(x + 1, y, 3, 1, 0xDDF8F5)
    rect_fill(x, y + 1, 5, 3, 0xDDF8F5)
    pixel(x + 1, y + 2, 0)
    pixel(x + 3, y + 2, 0)
    pixel(x, y + 4, 0xDDF8F5)
    pixel(x + 2, y + 4, 0xDDF8F5)
    pixel(x + 4, y + 4, 0xDDF8F5)
  end

  def draw()
    clear()
    if self.started == nil self.on_show() end
    var t = (now_ms() - self.started) * 1.0 / self.ms
    if t < 0 t = 0 end
    if t >= 1 return end
    # Green eyes open first; a violet pair joins them from above.
    if t > 0.04 && t < 0.68
      var look = 1
      if t > 0.25 && t < 0.40 look = 0 end
      if t > 0.40 && t < 0.58 look = 2 end
      var closed = (t < 0.10 || (t > 0.46 && t < 0.49) || t > 0.64)
      self.eyes(4, 4, look, closed, 0x94E044)
    end
    if t > 0.18 && t < 0.70
      var look = t < 0.38 ? 0 : 2
      var closed = (t < 0.22 || (t > 0.53 && t < 0.57) || t > 0.66)
      self.eyes(21, 1, look, closed, 0xA855F7)
    end
    # The culprit rises slowly, looks out, then ducks below the panel.
    if t > 0.72
      var y = 8
      if t < 0.84
        y = int(8 - 5 * (t - 0.72) / 0.12)
      elif t < 0.93
        y = 3
      else
        y = int(3 + 6 * (t - 0.93) / 0.07)
      end
      self.ghost(14, y)
    end
  end
end

return App()
