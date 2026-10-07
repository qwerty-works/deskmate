# @name Great Wave
# @desc An original indigo wave curls and rolls across the display in a woodblock-inspired palette.
# @author Deskmate
# @version 1.0.0
# @display 32x8
# @config durationMs number "Duration" default=7000 min=1000 max=7000 step=100 unit=ms

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
    if value > 7000 value = 7000 end
    return value
  end

  def on_show()
    self.started = now_ms()
    self.ms = self.duration()
  end

  def draw()
    clear()
    var t = (now_ms() - self.started) * 1.0 / self.ms
    t = t - int(t)
    var phase = t * 6.283185307179586
    var w = width(), h = height()
    for y : 0..h-1
      for x : 0..w-1
        var row = y * 1.0 / (h - 1)
        var swell = 0.5 + 0.5 * math.sin(phase * 2.0 - x * 0.13 + y * 0.72)
        var fold = 0.5 + 0.5 * math.cos(phase - x * 0.22 + y * 0.54)
        var red = 4 + int(5 * row + 5 * swell)
        var green = 16 + int(28 * row + 38 * fold)
        var blue = 42 + int(48 * row + 76 * swell)

        # Circular displacement is smooth at the spatial wrap and time seam.
        var dx = (w / 6.283185307179586) * math.sin(x * 6.283185307179586 / w - phase)
        var crestY = 3.0 + 1.25 * math.sin(dx * 0.24 + phase) + 0.75 * math.sin(dx * 0.58 - phase * 2.0)
        var depth = y - crestY
        var foam = 0.5 + 0.5 * math.cos(dx * 0.82 + phase * 2.0 + y * 0.7)
        var foamBand = clamp((depth + 1.4) / 0.6, 0, 1) * clamp((1.8 - depth) / 0.7, 0, 1)
        var foamWeight = foamBand * clamp((foam - 0.12) / 0.3, 0, 1)
        red += int((80 + 70 * foam) * foamWeight)
        green += int((86 + 92 * foam) * foamWeight)
        blue += int((54 + 76 * foam) * foamWeight)
        var shadowWeight = clamp((depth - 0.5) / 0.5, 0, 1) * clamp((2.6 - depth) / 0.6, 0, 1)
        red += int(10 * shadowWeight)
        green += int(30 * shadowWeight)
        blue += int(42 * shadowWeight)
        var hook = math.sin(dx * 1.45 - phase * 2.0 + y * 0.9)
        var hookWeight = clamp((depth + 0.8) / 0.55, 0, 1) * clamp((0.65 - depth) / 0.55, 0, 1)
        hookWeight *= clamp((hook - 0.4) / 0.35, 0, 1)
        red += int(46 * hookWeight)
        green += int(42 * hookWeight)
        blue += int(22 * hookWeight)
        if red > 255 red = 255 end
        if green > 255 green = 255 end
        if blue > 255 blue = 255 end
        pixel(x, y, (red << 16) | (green << 8) | blue)
      end
    end
  end
end

return App()
