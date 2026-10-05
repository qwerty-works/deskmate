# Pixel Fireplace · Desk Mate idle mode · 32x8 · 5 second loop
# Warm coals flicker beneath a tiny brick hearth.
# @name Pixel Fireplace
# @desc A quiet pixel fireplace for overnight idle mode.
# @author Desk Mate
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
    var phase = int((now_ms() - self.started) / 180) % 6
    rect_fill(2, 1, 28, 1, 0x5A3020)
    rect_fill(4, 2, 24, 1, 0x8A4A28)
    rect_fill(7, 3, 18, 4, 0x160A06)
    rect_fill(5, 7, 22, 1, 0x6B3520)
    pixel(16, 3, 0xFF9E32)
    pixel(15 + phase % 2, 4, 0xFFB83D)
    pixel(17 - phase % 2, 4, 0xFF7624)
    pixel(14 + (phase + 1) % 3, 5, 0xF24A1C)
    pixel(18 - (phase + 2) % 3, 5, 0xFF8A20)
    pixel(15, 6, 0xC92C15)
    pixel(16, 6, 0xFF5B18)
    pixel(17, 6, 0xD83212)
    pixel(11 + phase % 4, 6 - phase % 3, 0xE85A1A)
    pixel(21 - phase % 4, 5 - (phase + 1) % 3, 0xFF9E32)
  end
end

return App()
