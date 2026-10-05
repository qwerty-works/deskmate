# @name Ocean Drops
# @desc Color tides ripple outward as bright drops sweep across the whole display.
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

  # A triangular wave gives a smooth, interpreter-friendly color channel.
  def tri(v)
    var p = v % 240
    if p < 120
      return int(p * 255 / 120)
    end
    return int((240 - p) * 255 / 120)
  end

  def channel(v)
    if v < 1 return 1 end
    if v > 255 return 255 end
    return v
  end

  def draw()
    clear()
    var t = (now_ms() - self.started) * 1.0 / self.ms
    if t < 0 t = 0 end
    if t > 1 t = 1 end

    # Keep a colorful, dim undercurrent at the edges of the transition so
    # even its first and last frames still paint every one of the 256 pixels.
    var light = 255
    if t < 0.28
      light = 22 + int(t * 4 * 233)
    elif t > 0.84
      light = 255 - int((t - 0.84) * 6.25 * 233)
    end
    if light < 22 light = 22 end
    if light > 255 light = 255 end

    var tick = int(t * 720)
    var w = width()
    var h = height()
    for y : 0..h-1
      for x : 0..w-1
        # Three offset color bands make a moving lagoon gradient.
        var red = 18 + int(self.tri(x * 9 + y * 13 + tick) * light / 255)
        var green = 18 + int(self.tri(x * 5 - y * 17 + 80 + tick * 2) * light / 255)
        var blue = 18 + int(self.tri(x * 13 + y * 7 + 160 - tick) * light / 255)

        # Two offset, expanding drop rings cross as diamond-ocean ripples.
        # The weighted vertical distance keeps the waves legible on an 8px panel.
        var ax = x - 7
        var ay = (y - 4) * 3
        var bx = x - 24
        var by = (y - 2) * 3
        var da = int((ax * ax + ay * ay) / 4)
        var db = int((bx * bx + by * by) / 4)
        var ra = (da + 240 - (tick * 3 % 240)) % 240
        var rb = (db + 240 - (tick * 2 % 240 + 120) % 240) % 240
        var ring_a = self.tri(ra)
        var ring_b = self.tri(rb)
        var shimmer = int((ring_a + ring_b) / 5)
        red = self.channel(red + int(ring_b / 8))
        green = self.channel(green + shimmer)
        blue = self.channel(blue + int(ring_a / 2))

        # The moving crest sweeps in, crests at the center, and drains away.
        var crest = (x * 5 + y * 11 + 240 - tick * 4 % 240) % 240
        var foam = int(self.tri(crest) / 12)
        red = self.channel(red + int(foam / 2))
        green = self.channel(green + foam)
        blue = self.channel(blue + foam)
        pixel(x, y, (red << 16) | (green << 8) | blue)
      end
    end
  end
end

return App()
