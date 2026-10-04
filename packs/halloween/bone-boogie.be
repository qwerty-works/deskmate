# @name Bone Boogie
# @desc A rubber-hose skeleton shuffles in, kicks its knees, bows and skips away.
# @author Deskmate
# @version 1.1.0
# @display 32x8
# @config durationMs number "Duration" default=5000 min=1000 max=5000 step=100 unit=ms

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
    var x = width()/2 - 1
    if t < 0.22
      x = int(-6 + t/0.22*(x+6))
    elif t > 0.84
      x += int((t-0.84)/0.16*(width()/2+7))
    end
    var y = height()-8
    var beat = int(t*20)%4
    var c = 0xDDF8F5
    var bow = t > 0.72 && t < 0.84
    var head = x
    if bow head += 2 end
    var hy = y + (beat == 1 && !bow ? 1 : 0)
    # Two eye holes, lower jaw and open rib cage remain legible on eight rows.
    rect_fill(head-1,hy,3,2,c)
    pixel(head-1,hy+1,0)
    pixel(head+1,hy+1,0)
    pixel(head,hy+2,c)
    line(x-2,y+3,x+2,y+3,c)
    pixel(x-2,y+4,c)
    pixel(x,y+4,c)
    pixel(x+2,y+4,c)
    line(x-1,y+5,x+1,y+5,c)
    # Alternating raised elbows and knee kicks provide the cartoon dance.
    if bow
      line(x-2,y+3,x-3,y+5,c)
      line(x+2,y+3,x+4,y+4,c)
      line(x-1,y+5,x-2,y+7,c)
      line(x+1,y+5,x+2,y+7,c)
    elif beat < 2
      line(x-2,y+3,x-4,y+2,c)
      pixel(x-4,y+1,c)
      line(x+2,y+3,x+4,y+4,c)
      line(x-1,y+5,x-2,y+7,c)
      line(x+1,y+5,x+3,y+6,c)
      line(x+3,y+6,x+4,y+5,c)
    else
      line(x-2,y+3,x-4,y+4,c)
      line(x+2,y+3,x+4,y+2,c)
      pixel(x+4,y+1,c)
      line(x+1,y+5,x+2,y+7,c)
      line(x-1,y+5,x-3,y+6,c)
      line(x-3,y+6,x-4,y+5,c)
    end
    # Two orange stage marks bounce in time to the silent rhythm.
    if t > 0.22 && t < 0.72
      pixel(x-7,y+6-(beat%2),0xFF8818)
      pixel(x+7,y+6-((beat+1)%2),0xFF8818)
      if beat == 0 pixel(x-8,y+5,0xA855F7) end
      if beat == 2 pixel(x+8,y+5,0xA855F7) end
    end
  end
end

return App()
