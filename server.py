import web, os, urllib, hashlib, shutil
from web import form
from screenshot import WebKitRenderer
import subprocess
from PIL import ImageChops, Image
from itertools import izip
import math, operator
from img_comp import ImgComp

render = web.template.render('templates/')

urls = (
  '/', 'index',
  '/images/(new|base|diff)/(.*)', 'images',
  '/(.*)', 'screenshot'
)

def rmsdiff(img1, img2):
  img1_file = Image.open(img1)
  img2_file = Image.open(img2)
  
  #assert img1_file.mode == img2_file.mode, "Different kinds of images."
  #assert img1_file.size == img2_file.size, "Different sizes."
   
  pairs = izip(img1_file.getdata(), img2_file.getdata())
  if len(img1_file.getbands()) == 1:
      # for gray-scale jpegs
      dif = sum(abs(p1-p2) for p1,p2 in pairs)
  else:
      dif = sum(abs(c1-c2) for p1,p2 in pairs for c1,c2 in zip(p1,p2))
   
  ncomponents = img1_file.size[0] * img1_file.size[1] * 3
  return (dif / 255.0 * 100) / ncomponents


class index:
  def GET(self):
    return render.index()

class screenshot:
  def GET(self, url):
    params = web.input(delay=0, img_type="jpg")
    delay = params.delay
    img_type = params.img_type    

    name_hash = hashlib.md5()
    name_hash.update(url)

    new_img_name = "images/new/"+name_hash.hexdigest()
    base_img_name = new_img_name.replace('new', 'base')
    diff_img_name = new_img_name.replace('new', 'diff')

    subprocess.call(["python", "screenshot.py", urllib.unquote(url),"-d", ":99", "--debug", "-o", new_img_name])
    
    if not os.path.isfile(base_img_name+"."+img_type) and os.path.isfile(new_img_name+"."+img_type):
      shutil.copy('.'.join([new_img_name,img_type]), '.'.join([base_img_name,img_type]))

    diff = None
    if os.path.isfile(base_img_name+"."+img_type) and os.path.isfile(new_img_name+"."+img_type):
      diff = rmsdiff('.'.join([base_img_name,img_type]), '.'.join([new_img_name,img_type]))

      ic = ImgComp({
        'verbose': True,
        'save_diff_fname': diff_img_name+"."+img_type,
        'save_diff_if_error': True,
      })
      ic.compare('.'.join([base_img_name,img_type]), '.'.join([new_img_name,img_type]), 0.001)

    return render.screenshot(urllib.unquote(url), '.'.join([base_img_name,img_type]), '.'.join([new_img_name,img_type]), '.'.join([diff_img_name,img_type]), diff)

class images:
  def GET(self, age, name):
    ext = name.split('.')[-1]

    cType = {
      "png":"images/png",
      "jpg":"images/jpeg",
      "gif":"images/gif",
      "ico":"images/x-icon"
    }

    if os.path.isfile('/'.join(['images',age,name])):
      web.header("Content-Type", cType[ext])

      return open('/'.join(['images',age,name]), 'rb').read()
    else:
      raise web.notfound()

if __name__ == '__main__':
  app = web.application(urls, globals())
  app.run()
