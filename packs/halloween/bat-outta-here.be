# @name Bat Outta Here
# @desc Three flapping bats cross the night; the little one races to catch up.
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

  # Purple wings fold around a three-pixel body. Green eyes face the journey.
  def bat(x, y, flap, small)
    if small
      pixel(x, y, 0xA855F7)
      pixel(x + 1, y, 0x94E044)
      if flap == 0
        pixel(x - 1, y - 1, 0xA855F7)
        pixel(x - 2, y - 2, 0xA855F7)
        pixel(x + 2, y - 1, 0xA855F7)
        pixel(x + 3, y - 2, 0xA855F7)
      else
        pixel(x - 1, y + 1, 0xA855F7)
        pixel(x - 2, y, 0xA855F7)
        pixel(x + 2, y + 1, 0xA855F7)
        pixel(x + 3, y, 0xA855F7)
      end
    else
      rect_fill(x, y - 1, 3, 3, 0xA855F7)
      pixel(x, y - 2, 0xA855F7)
      pixel(x + 2, y - 2, 0xA855F7)
      pixel(x + 2, y - 1, 0x94E044)
      if flap == 0
        line(x - 3, y - 2, x - 1, y, 0xA855F7)
        line(x + 3, y, x + 5, y - 2, 0xA855F7)
        pixel(x - 3, y - 1, 0xA855F7)
        pixel(x + 5, y - 1, 0xA855F7)
      else
        line(x - 3, y, x - 1, y + 1, 0xA855F7)
        line(x + 3, y + 1, x + 5, y, 0xA855F7)
        pixel(x - 2, y + 2, 0xA855F7)
        pixel(x + 4, y + 2, 0xA855F7)
      end
    end
  end

  def draw()
    clear(0x000000)
    var t = (now_ms() - self.started) * 1.0 / self.ms
    if t < 0 t = 0 end
    if t > 1 t = 1 end
    # A small crescent establishes the night without obscuring the bats.
    if t > 0.03 && t < 0.78
      rect_fill(26, 0, 3, 3, 0xFF8818)
      pixel(26, 0, 0x000000)
      pixel(28, 2, 0x000000)
      rect_fill(27, 0, 2, 2, 0x000000)
    end
    var flap = int(t * 26) % 2
    self.bat(int(t * 60) - 7, 2, flap, false)
    self.bat(int(t * 60) - 18, 5, 1 - flap, false)
    # The straggler enters late, flaps faster and overtakes the second bat.
    if t > 0.20
      self.bat(int((t - 0.20) * 65) - 7, 4, int(t * 40) % 2, true)
    end
  end
end

return App()
