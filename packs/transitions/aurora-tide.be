# @name Aurora Tide
# @desc A full-panel aurora wave sweeps in, crests in shifting color, and fades away.
# @author Deskmate
# @version 1.0.0
# @display 32x8
# @config durationMs number "Duration" default=3000 min=1000 max=5000 step=100 unit=ms

import math

class App
  var started, ms
  def init()
    self.started = now_ms()
    self.ms = self.duration()
  end
  def duration()
    var configured = store.get('durationMs')
    var value = 3000
    if configured != nil value = int(configured) end
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

    # The aurora palette moves from deep blue through teal and violet to coral.
    var palette = [0x071B36, 0x08758A, 0x35D7C5, 0x9A78F2, 0xFF785A]
    var fade = 1.0
    if t < 0.12 fade = 0.12 + 0.88 * t / 0.12 end
    if t > 0.72 fade = 0.12 + 0.88 * (1 - t) / 0.28 end

    for y : 0..height()-1
      for x : 0..width()-1
        var row = y * 1.0 / (height() - 1)
        var across = x * 1.0 / (width() - 1)
        var phase = across * 5.1 - t * 9.0 + math.sin(row * 5.4 + t * 5.0) * 0.8
        var hue = 0.5 + 0.5 * math.sin(phase)
        var scaled = hue * 4
        var band = int(scaled)
        if band > 3 band = 3 end
        var blend = scaled - band
        var first = palette[band], second = palette[band + 1]
        var red = ((first >> 16) & 255) * (1 - blend) + ((second >> 16) & 255) * blend
        var green = ((first >> 8) & 255) * (1 - blend) + ((second >> 8) & 255) * blend
        var blue = (first & 255) * (1 - blend) + (second & 255) * blend

        # A broad, rippling front wipes left to right while a dim tinted base
        # keeps every pixel alive, including the leading and trailing edges.
        var front = t * 1.8 - across + math.sin(row * 7.2 - t * 8.0) * 0.075
        var entering = (front + 0.18) / 0.36
        if entering < 0 entering = 0 end
        if entering > 1 entering = 1 end
        entering = entering * entering * (3 - 2 * entering)
        var crest = 0.76 + 0.24 * math.cos(phase * 1.7)
        var light = 0.10 + 0.90 * entering * fade * crest

        red = int(red * light)
        green = int(green * light)
        blue = int(blue * light)
        if red < 1 red = 1 end
        if green < 1 green = 1 end
        if blue < 1 blue = 1 end
        pixel(x, y, (red << 16) | (green << 8) | blue)
      end
    end
  end
end
return App()
