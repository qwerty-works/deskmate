# @name Witching Hour
# @desc A storybook witch swoops past a crescent moon with a sparkling broom trail.
# @author Deskmate
# @version 1.1.0
# @display 32x8
# @config durationMs number "Duration" default=5000 min=1000 max=5000 step=100 unit=ms

import math

class App
  var started, ms
  def init()
    self.started = now_ms()
    self.ms = 0
  end
  def duration()
    var ms = int(store.get("durationMs"))
    if ms < 1000 ms = 1000 elif ms > 5000 ms = 5000 end
    return ms
  end
  def on_show()
    self.started = now_ms()
    self.ms = self.duration()
  end
  def draw()
    clear(0)
    var t = (now_ms() - self.started) * 1.0 / self.ms
    if t < 0 t = 0 end
    if t >= 1 return end
    var w = width()
    var base = (height() - 8) / 2
    # The crescent frames the scene, then slips away with the final swoop.
    if t < 0.93
      var mx = w - 7
      rect_fill(mx+1,base,3,1,0xDDF8F5)
      rect_fill(mx,base+1,2,3,0xDDF8F5)
      rect_fill(mx+1,base+4,3,1,0xDDF8F5)
      pixel(mx+2,base+1,0xDDF8F5)
      pixel(mx+2,base+3,0xDDF8F5)
    end
    var x = int(-11 + t * (w + 24))
    var bob = int(math.sin(t * 18) + 0.5)
    var y = base + bob
    # Pointed hat, nose and bent robe make a readable seven-row silhouette.
    pixel(x+5,y,0xA855F7)
    line(x+4,y+1,x+6,y+1,0xA855F7)
    line(x+3,y+2,x+8,y+2,0xA855F7)
    line(x+5,y+3,x+7,y+3,0x94E044)
    pixel(x+8,y+3,0x94E044)
    rect_fill(x+4,y+4,3,1,0xA855F7)
    line(x+7,y+4,x+8,y+5,0x94E044)
    pixel(x+3,y+4,0xA855F7)
    line(x+2,y+5,x+10,y+5,0xFF8818)
    line(x,y+4,x+2,y+5,0xFF8818)
    line(x,y+6,x+2,y+5,0xFF8818)
    pixel(x+6,y+6,0xA855F7)
    # Sparse twinkles trail the broom rather than filling the background.
    var i = 0
    while i < 3
      var sx = x - 3 - i * 4
      var sy = base + ((int(t*23)+i*3)%7)
      if (int(t*18)+i)%3 != 0
        pixel(sx,sy,0xDDF8F5)
        if i == 0 && int(t*24)%2 == 0
          pixel(sx-1,sy,0xFF8818)
          pixel(sx+1,sy,0xFF8818)
        end
      end
      i += 1
    end
  end
end

return App()
