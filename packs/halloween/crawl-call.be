# @name Crawl Call
# @desc A stitched crawling hand tiptoes in, waves a finger, taps, and scuttles away.
# @author Deskmate
# @version 1.1.0
# @display 32x8
# @config durationMs number "Duration" default=5000 min=1000 max=5000 step=100 unit=ms

class App
  var started, ms
  def init()
    self.started = now_ms()
    self.ms = self.duration()
  end
  def duration()
    var value = int(store.get('durationMs'))
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
    if t >= 1 return end
    var x = -10, ground = height() - 1
    if t < 0.34 x = int(-10 + (width() / 2 + 6) * t / 0.34)
    elif t < 0.66 x = int(width() / 2) - 4
    else x = int(width() / 2 - 4 + (width() / 2 + 14) * (t - 0.66) / 0.34) end
    var step = int(t * 24) % 2
    var lift = t > 0.34 && t < 0.66 ? 0 : step
    # A broad palm, severed purple cuff, four uneven fingers and a thumb.
    rect_fill(x, ground - 3 - lift, 6, 3, 0xDDF8F5)
    rect_fill(x - 2, ground - 2 - lift, 2, 2, 0xA855F7)
    for finger : 0..3
      var fx = x + finger * 2
      var top = ground - 5 - lift
      if finger == 1 || finger == 2 top -= 1 end
      if t > 0.39 && t < 0.61 && finger == 3
        top -= int((t - 0.39) * 24) % 2
      end
      line(fx, top, fx, ground - 3 - lift, 0xDDF8F5)
      pixel(fx, top, 0xFF8818)
    end
    line(x + 5, ground - 2 - lift, x + 7, ground - 3 - lift, 0xDDF8F5)
    pixel(x + 7, ground - 3 - lift, 0xFF8818)
    # Bent fingertips provide the stop-motion crawl, then a deliberate tap.
    var tap = int(t * 28) % 2
    if t <= 0.34 || t >= 0.66
      pixel(x + 1, ground, 0xDDF8F5)
      pixel(x + 4 + step, ground, 0xDDF8F5)
    elif t > 0.55
      line(x + 6, ground - 1, x + 6 + tap, ground, 0xDDF8F5)
      if tap == 0 pixel(x + 9, ground, 0xA855F7) end
    end
    # A stitched wrist keeps the silhouette recognizably a hand.
    pixel(x - 1, ground - 2 - lift, 0x94E044)
    pixel(x + 2, ground - 2 - lift, 0xA855F7)
    pixel(x + 4, ground - 2 - lift, 0xA855F7)
  end
end
return App()
