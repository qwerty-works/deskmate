# @name Prism Loom
# @desc A full-panel ribbon of shifting neon color turns inside out and settles to warm amber.
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
    var value = int(store.get('durationMs', 3000))
    if value < 1000 value = 1000 end
    if value > 5000 value = 5000 end
    return value
  end

  def on_show()
    self.started = now_ms()
    self.ms = self.duration()
  end

  def absolute(value)
    return value < 0 ? -value : value
  end

  def mix(a, b, amount)
    if amount < 0 amount = 0 end
    if amount > 1 amount = 1 end
    var ar = (a >> 16) & 255, ag = (a >> 8) & 255, ab = a & 255
    var br = (b >> 16) & 255, bg = (b >> 8) & 255, bb = b & 255
    var r = int(ar + (br - ar) * amount + 0.5)
    var g = int(ag + (bg - ag) * amount + 0.5)
    var blue = int(ab + (bb - ab) * amount + 0.5)
    return (r << 16) | (g << 8) | blue
  end

  def sample(position, reverse)
    var palette = [0x12E6C8, 0x168BFF, 0x7657FF, 0xF23DAB, 0xFF713D, 0xFFD447]
    var count = palette.size()
    var index = int(position)
    if position < index index -= 1 end
    var fraction = position - index
    while index < 0
      index += count
    end
    index = index % count
    var next = (index + 1) % count
    if reverse
      index = count - 1 - index
      next = count - 1 - next
    end
    return self.mix(palette[index], palette[next], fraction)
  end

  def draw()
    clear()
    var t = (now_ms() - self.started) * 1.0 / self.ms
    if t < 0 t = 0 end
    if t > 1 t = 1 end

    var w = width(), h = height()
    var travel = 0.0
    if t < 0.5
      travel = t * 2
    else
      travel = (1 - t) * 2
    end
    # Smoothly turn the palette inside out as the loom crosses its midpoint.
    var reverse = 0.0
    if t <= 0.44
      reverse = 0
    elif t >= 0.56
      reverse = 1
    else
      var u = (t - 0.44) / 0.12
      reverse = u * u * (3 - 2 * u)
    end

    var entrance = 1.0
    if t < 0.08
      var u = t / 0.08
      entrance = u * u * (3 - 2 * u)
    end
    var exit = 1.0
    if t > 0.88
      var u = (t - 0.88) / 0.12
      exit = 1 - u * u * (3 - 2 * u)
    end
    var energy = entrance
    if exit < energy energy = exit end

    var seam = -5 + travel * (w + 10)
    for y : 0..h-1
      for x : 0..w-1
        # Two shallow waves make the full-height curtains ripple as they slide.
        var curtain = x + 3.2 * math.sin(y * 0.82 + travel * 6.28318) + 1.5 * math.sin(y * 1.72 - travel * 4.4)
        var position = curtain * 0.18 + travel * 3.2
        var front = self.sample(position, false)
        var back = self.sample(position, true)
        var color = self.mix(front, back, reverse)

        # A fine bright selvedge traces the moving seam through the gradients.
        var seamAtY = seam + 2.0 * math.sin(y * 0.72 + travel * 4)
        var distance = self.absolute(x - seamAtY)
        if distance < 0.8
          color = self.mix(color, 0xFFF5C7, 0.78)
        elif distance < 1.8
          color = self.mix(color, 0xFFF5C7, 0.30)
        end
        # The curtain opens from and closes to the same vivid amber handoff color.
        pixel(x, y, self.mix(0xFF713D, color, energy))
      end
    end
  end
end

return App()
