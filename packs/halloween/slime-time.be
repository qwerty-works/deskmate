# @name Slime Time
# @desc Uneven slime drips cover the screen, bubble, and drain away.
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

  def draw()
    clear()
    var t = (now_ms() - self.started) * 1.0 / self.ms
    if t < 0 t = 0 end
    if t > 1 t = 1 end
    if t <= 0 || t >= 0.98 return end
    var w = width()
    var h = height()
    for x : 0..w-1
      # Each five-column lobe has a round tip and its own arrival delay.
      var lobe = int(x / 5)
      var local_x = x % 5
      var delay = ((lobe * 3) % 5) * 0.018
      var tip = 0
      if local_x == 0 || local_x == 4 tip = 1 end
      if t < 0.40
        var depth = int((t - delay) * (h + 5) / 0.32) - tip
        if depth > h depth = h end
        if depth > 0
          rect_fill(x, 0, 1, depth, 0x94E044)
          if local_x == 1 && depth > 2 pixel(x, depth - 2, 0xDDF8F5) end
        end
      elif t < 0.64
        rect_fill(x, 0, 1, h, 0x94E044)
      else
        var top = int((t - 0.64 + delay) * (h + 3) / 0.30) + tip
        if top < 0 top = 0 end
        if top < h rect_fill(x, top, 1, h - top, 0x94E044) end
      end
    end
    # One trapped bubble rises, stretches, then pops through the surface.
    if t >= 0.42 && t < 0.62
      var bx = int(w / 2)
      var by = h - 2 - int((t - 0.42) * (h - 3) / 0.20)
      pixel(bx, by - 1, 0)
      pixel(bx - 1, by, 0)
      pixel(bx + 1, by, 0)
      pixel(bx, by + 1, 0)
      pixel(bx, by, 0xDDF8F5)
    end
  end
end

return App()
