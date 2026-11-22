import io, json, math, random, shutil, tempfile, threading, traceback, uuid, zipfile, datetime, functools, os, sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageOps, ImageFilter

# PyInstaller bundles the cutout model so no runtime download is required.
if getattr(sys, 'frozen', False):
    model_dir = Path(sys._MEIPASS) / 'models'
    if (model_dir / 'u2netp.onnx').is_file():
        os.environ['U2NET_HOME'] = str(model_dir)
HOME=Path.home()/'Keepsake Albums' ; HOME.mkdir(exist_ok=True)
CACHE=HOME/'Imported Albums'; CACHE.mkdir(exist_ok=True)
EXT={'.jpg','.jpeg','.png','.webp','.bmp','.tif','.tiff','.gif','.heic','.heif'}
BG='#262522'; BASE_W,BASE_H=1200,760
CAPTIONS=['little moments','all the good days','the way we were','collected memories','a day to remember','our story','somewhere, together','the good times']

def font(sz):
    for p in ['C:/Windows/Fonts/segoeui.ttf','C:/Windows/Fonts/arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
        if Path(p).exists(): return ImageFont.truetype(p,max(9,int(sz)))
    return ImageFont.load_default()

PHOTOS_PER_SPREAD=14

@functools.lru_cache(maxsize=2048)
def capture_date(path):
    """Sort by embedded camera date, falling back to filesystem time."""
    try:
        with Image.open(path) as im:
            exif=im.getexif()
            for tag in (36867, 36868, 306):
                raw=exif.get(tag)
                if raw:
                    return datetime.datetime.strptime(str(raw)[:19], '%Y:%m:%d %H:%M:%S').timestamp()
    except Exception: pass
    try:return Path(path).stat().st_mtime
    except Exception:return 0

CUTOUT_ERROR = None
CUTOUT_SESSION = None

def cutout_backend():
    """Lazy backend with an actionable error rather than silently disabling AI."""
    global CUTOUT_ERROR, CUTOUT_SESSION
    if CUTOUT_SESSION is not None:
        return CUTOUT_SESSION
    try:
        from rembg import remove, new_session
        CUTOUT_SESSION = (remove, new_session('u2netp'))
        CUTOUT_ERROR = None
        return CUTOUT_SESSION
    except Exception as exc:
        CUTOUT_ERROR = f'{type(exc).__name__}: {exc}'
        return None

@functools.lru_cache(maxsize=256)
def subject_cutout(path):
    """Segment an imported image; failures are reported to the UI."""
    global CUTOUT_ERROR
    backend=cutout_backend()
    if backend is None:return None
    try:
        with Image.open(path) as original:
            photo=ImageOps.exif_transpose(original).convert('RGBA')
            photo.thumbnail((900,900),Image.Resampling.LANCZOS)
        out=backend[0](photo,session=backend[1]).convert('RGBA')
        if not out.getchannel('A').getbbox():
            CUTOUT_ERROR='The model returned an empty cutout.'
            return None
        return out
    except Exception as exc:
        CUTOUT_ERROR=f'{type(exc).__name__}: {exc}'
        return None


def render(paths, page, seed, scale=1, theme='Summer camp', cutouts=False):
    """Original-photo-only mixed-media journal spread; deterministic layout."""
    s=scale; W,H=1200*s,760*s
    rng=random.Random(int(seed)+page*9173)
    themes={
      'Summer camp':['#f1a8a6','#b7d0a3','#f3d78c','#c8b4d9','#a8cdd4'],
      'Soft romance':['#efb9c5','#d9b7d3','#f5d6d8','#e4d0b3','#b8c6b3'],
      'Vintage botanical':['#b4c5a6','#ddc9a3','#a7b9a2','#e8d7ba','#c6c6a6'],
      'Golden hour':['#e7a575','#f2d28c','#c99b79','#e7b8a1','#d2ba86']}
    palette=themes.get(theme,themes['Summer camp'])
    im=Image.new('RGBA',(W,H),'#302b28')
    def S(v):return int(round(v*s))
    def rect(box,fill,radius=0,outline=None,width=1):
        d=ImageDraw.Draw(im);bb=tuple(S(v) for v in box)
        if radius:d.rounded_rectangle(bb,radius=S(radius),fill=fill,outline=outline,width=max(1,S(width)))
        else:d.rectangle(bb,fill=fill,outline=outline,width=max(1,S(width)))
    def text_label(x,y,txt,sz=17,ink='#59463b',bg='#fff2d6',rotation=0):
        f=font(S(sz));bb=f.getbbox(txt);tw=bb[2]-bb[0];th=bb[3]-bb[1]
        layer=Image.new('RGBA',(tw+S(24),th+S(20)),(0,0,0,0));d=ImageDraw.Draw(layer)
        d.rounded_rectangle((0,0,layer.width-1,layer.height-1),radius=S(4),fill=bg)
        d.text((S(12),S(9)-bb[1]),txt,font=f,fill=ink)
        layer=layer.rotate(rotation,expand=True,resample=Image.Resampling.BICUBIC)
        im.alpha_composite(layer,(S(x),S(y)))
    # Paperboard, textured surface, and patterned swatches
    for side in range(2):
        x=42+side*558
        rect((x+7,28,x+546,733),'#211b18',radius=7)
        rect((x,16,x+532,718),'#b9956e',radius=6)
        rect((x+12,27,x+521,707),'#e2caa5',radius=3)
        d=ImageDraw.Draw(im)
        for _ in range(6500):
            px=S(rng.randint(x+14,x+519));py=S(rng.randint(30,705))
            d.point((px,py),fill=rng.choice(['#cbb28e','#e8d6b7','#d8bf9a','#dfc8a7']))
        # Large scrapbook paper backgrounds
        for k in range(5):
            px=x+rng.randint(20,335);py=rng.randint(40,575)
            ww=rng.randint(105,205);hh=rng.randint(85,185)
            col=rng.choice(palette)
            rect((px,py,px+ww,py+hh),col)
            dd=ImageDraw.Draw(im)
            for yy in range(py+9,py+hh-6,17):
                for xx in range(px+9,px+ww-6,17):
                    if k%3==0:dd.ellipse((S(xx),S(yy),S(xx+3),S(yy+3)),fill='#fff1df')
                    elif k%3==1:dd.line((S(xx-3),S(yy-3),S(xx+3),S(yy+3)),fill='#fff1df',width=max(1,S(2)))
                    else:dd.arc((S(xx-4),S(yy-4),S(xx+4),S(yy+4)),20,160,fill='#fff1df',width=max(1,S(2)))
    # Each page gets seven photos. Several portrait/landscape combinations.
    templates=[
      [(23,48,242,210),(261,40,235,180),(38,245,190,206),(224,229,275,206),(29,456,229,193),(252,450,239,192),(175,346,155,150)],
      [(28,52,206,225),(231,56,268,182),(28,287,258,177),(279,255,206,223),(34,492,222,161),(256,486,237,167),(170,365,165,145)],
      [(26,47,260,190),(274,53,215,225),(29,251,217,223),(239,286,254,181),(30,496,257,159),(286,488,207,163),(178,358,150,151)]
    ]
    captions=['the good days','little moments','sunshine & us','remember this','our people','made of memories','love this day']
    for side in range(2):
        x=42+side*558
        positions=templates[(page+side)%len(templates)]
        for j,(dx,dy,ww,hh) in enumerate(positions):
            idx=page*PHOTOS_PER_SPREAD+side*7+j
            if idx>=len(paths):continue
            dx+=rng.randint(-9,9);dy+=rng.randint(-10,10)
            angle=rng.randint(-11,11)
            try:
                with Image.open(paths[idx]) as src:
                    src=ImageOps.exif_transpose(src).convert('RGB')
                    photo=ImageOps.fit(src,(S(ww-14),S(hh-14)),method=Image.Resampling.LANCZOS,centering=(.5,.45))
                card=Image.new('RGBA',(S(ww),S(hh)),'#fffaf0')
                card.paste(photo,(S(7),S(7)))
                if j in (3,5):
                    # small polaroid-like footer
                    extra=Image.new('RGBA',(card.width,card.height+S(20)),'#fffaf0')
                    extra.paste(card,(0,0));card=extra
                    ImageDraw.Draw(card).text((S(11),S(hh+2)),rng.choice(captions),font=font(S(11)),fill='#76604f')
                rotated=card.rotate(angle,expand=True,resample=Image.Resampling.BICUBIC)
                px=S(x+dx)-((rotated.width-card.width)//2)
                py=S(dy)-((rotated.height-card.height)//2)
                shadow=Image.new('RGBA',rotated.size,(30,22,15,0))
                shadow.putalpha(rotated.getchannel('A').point(lambda a:int(a*.35)))
                shadow=shadow.filter(ImageFilter.GaussianBlur(max(1,S(5))))
                im.alpha_composite(shadow,(px+S(5),py+S(7)))
                im.alpha_composite(rotated,(px,py))
                if j%2==0:
                    tape=Image.new('RGBA',(S(62),S(20)),rng.choice([(238,214,156,203),(177,204,163,199),(236,172,170,197)]))
                    tape=tape.rotate(rng.randint(-25,25),expand=True,resample=Image.Resampling.BICUBIC)
                    im.alpha_composite(tape,(S(x+dx+ww//2)-tape.width//2,S(dy-10)))
            except Exception:
                rect((x+dx,dy,x+dx+ww,dy+hh),'#f3e9d8',outline='#9f7d63',width=2)
                text_label(x+dx+8,dy+15,'Photo unavailable',12)
    # Optional locally segmented foreground subjects. Draw over existing
    # photograph layers, as real hand-trimmed stickers with a cream outline.
    if cutouts and cutout_backend() is not None:
        for side in range(2):
            idx=page*PHOTOS_PER_SPREAD+side*7+3
            if idx>=len(paths):continue
            foreground=subject_cutout(str(paths[idx]))
            if foreground is None:continue
            foreground.thumbnail((S(205),S(245)),Image.Resampling.LANCZOS)
            alpha=foreground.getchannel('A')
            from PIL import ImageFilter as _Filter
            outline=alpha.filter(_Filter.MaxFilter(17))
            sticker=Image.new('RGBA',foreground.size,'#fff9e9')
            sticker.putalpha(outline)
            sticker.alpha_composite(foreground)
            sticker=sticker.rotate((-7 if side==0 else 8),expand=True,resample=Image.Resampling.BICUBIC)
            xx=S((42+side*558)+280);yy=S(325)
            if xx+sticker.width<=W and yy+sticker.height<=H:
                im.alpha_composite(sticker,(xx,yy))
    # Hand-placed accents above photos
    for side in range(2):
        x=42+side*558
        d=ImageDraw.Draw(im)
        for k in range(17):
            xx=x+rng.randint(24,493);yy=rng.randint(45,685)
            color=rng.choice(['#bd7879','#7d9a78','#d1a44e','#a184ad'])
            if k%4==0:
                for a in range(6):
                    theta=a*math.tau/6;cx=S(xx+math.cos(theta)*9);cy=S(yy+math.sin(theta)*9);rr=S(5)
                    d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),fill=color)
                rr=S(5);d.ellipse((S(xx)-rr,S(yy)-rr,S(xx)+rr,S(yy)+rr),fill='#f4dc8a')
            elif k%4==1:
                d.line((S(xx-8),S(yy),S(xx+8),S(yy)),fill=color,width=max(1,S(2)))
                d.line((S(xx),S(yy-8),S(xx),S(yy+8)),fill=color,width=max(1,S(2)))
            elif k%4==2:
                d.arc((S(xx-9),S(yy-7),S(xx+9),S(yy+7)),0,180,fill=color,width=max(1,S(2)))
            else:d.ellipse((S(xx),S(yy),S(xx+4),S(yy+4)),fill=color)
        text_label(x+22,665,f'{page*2+side+1:02d}  •  KEEPSAKE',11,bg='#f5e7ca')
        if side==0:text_label(x+23,31,rng.choice(['THE DAYS WE KEEP','GOOD TIMES','OUR LITTLE WORLD']),15,rotation=-3)
        else:text_label(x+306,34,rng.choice(['SO MUCH LOVE','SWEET MEMORIES','TOGETHER']),15,rotation=3)
    # Chunky brass twin-loop wire binding
    rect((573,18,628,720),'#71583f')
    rect((590,18,610,720),'#46382b')
    d=ImageDraw.Draw(im)
    for yy in range(37,707,26):
        d.ellipse((S(575),S(yy),S(625),S(yy+18)),outline='#342819',width=max(2,S(6)))
        d.arc((S(575),S(yy),S(625),S(yy+18)),0,350,fill='#e8c16f',width=max(2,S(4)))
    return im.convert('RGB')

class Studio:
    """Local-first scrapbook desktop studio."""
    def __init__(self, root):
        self.root=root; self.paths=[]; self.seed=random.randrange(10**8); self.page=0
        self.preview=None; self.tkpreview=None; self.busy=False; self.album_path=None
        self.theme='Summer camp'; self.title='My memory book'; self.zoom=1.0; self.cutouts_var=tk.BooleanVar(value=False)
        root.title('Keepsake Studio — Memory Journal')
        root.geometry('1440x900'); root.minsize(1050,680); root.configure(bg='#171a1e')
        self.C={'bg':'#171a1e','panel':'#20242a','panel2':'#292e35','ink':'#f1eee9','muted':'#a4a6a9','accent':'#e6bd82','line':'#363a40'}
        self.sidebar=tk.Frame(root,bg=self.C['panel'],width=272); self.sidebar.pack(side='left',fill='y');self.sidebar.pack_propagate(False)
        self.main=tk.Frame(root,bg=self.C['bg']);self.main.pack(side='left',fill='both',expand=True)
        self._sidebar();self._main()
        root.bind('<Left>',lambda e:self.navigate(-1));root.bind('<Right>',lambda e:self.navigate(1))
        root.bind('<Control-o>',lambda e:self.import_folder());root.bind('<Control-s>',lambda e:self.save_album())
        root.bind('<Control-e>',lambda e:self.export_hd());root.bind('<Control-Shift-E>',lambda e:self.export_all())
        self.draw()

    def label(self,parent,text,size=11,weight='normal',color=None,bg=None,**kw):
        return tk.Label(parent,text=text,font=('Segoe UI',size,weight),fg=color or self.C['ink'],bg=bg or parent.cget('bg'),**kw)
    def btn(self,parent,text,cmd,primary=False,**kw):
        return tk.Button(parent,text=text,command=cmd,relief='flat',bd=0,cursor='hand2',font=('Segoe UI',10,'bold'),padx=13,pady=10,
            bg=self.C['accent'] if primary else self.C['panel2'],fg='#22211f' if primary else self.C['ink'],
            activebackground='#f2d5a8' if primary else '#41464d',activeforeground='#1b1b1b' if primary else '#ffffff',**kw)
    def _sidebar(self):
        p=self.sidebar
        tk.Frame(p,bg=self.C['accent'],height=5).pack(fill='x')
        self.label(p,'✦  keepsake studio',21,'bold',self.C['accent']).pack(anchor='w',padx=24,pady=(27,1))
        self.label(p,'AUTOMATIC MEMORY JOURNAL',9,color=self.C['muted']).pack(anchor='w',padx=25,pady=(0,26))
        self.btn(p,'＋  Import photo folder',self.import_folder,True).pack(fill='x',padx=18,pady=5)
        self.btn(p,'＋  Select individual photos',self.import_files).pack(fill='x',padx=18,pady=5)
        self.btn(p,'＋  Add more photos',self.add_photos).pack(fill='x',padx=18,pady=5)
        self.label(p,'YOUR ALBUM',10,'bold',self.C['muted']).pack(anchor='w',padx=24,pady=(27,8))
        self.name_var=tk.StringVar(value=self.title)
        name=tk.Entry(p,textvariable=self.name_var,fg=self.C['ink'],bg=self.C['panel2'],insertbackground='white',relief='flat',font=('Segoe UI',12),highlightthickness=1,highlightbackground=self.C['line'])
        name.pack(fill='x',padx=18,ipady=10)
        self.label(p,'VISUAL THEME',10,'bold',self.C['muted']).pack(anchor='w',padx=24,pady=(24,8))
        self.theme_var=tk.StringVar(value='Summer camp')
        menu=tk.OptionMenu(p,self.theme_var,'Summer camp','Soft romance','Vintage botanical','Golden hour',command=lambda v:self.redraw())
        menu.config(bg=self.C['panel2'],fg=self.C['ink'],activebackground='#42464e',activeforeground='white',highlightthickness=0,relief='flat',font=('Segoe UI',10));menu['menu'].config(bg=self.C['panel2'],fg=self.C['ink'])
        menu.pack(fill='x',padx=18)
        self.label(p,'LAYOUT',10,'bold',self.C['muted']).pack(anchor='w',padx=24,pady=(25,8))
        self.btn(p,'⤨  Remix this scrapbook',self.shuffle).pack(fill='x',padx=18,pady=4)
        tk.Checkbutton(p,text='AI subject stickers (optional)',variable=self.cutouts_var,command=self.toggle_cutouts,fg=self.C['ink'],bg=self.C['panel'],selectcolor=self.C['panel2'],activebackground=self.C['panel'],activeforeground=self.C['ink'],font=('Segoe UI',10)).pack(anchor='w',padx=20,pady=5)
        self.label(p,'ALBUM FILES',10,'bold',self.C['muted']).pack(anchor='w',padx=24,pady=(24,8))
        self.btn(p,'▣  Save complete album',self.save_album).pack(fill='x',padx=18,pady=4)
        self.btn(p,'▤  Open saved album',self.open_album).pack(fill='x',padx=18,pady=4)
        self.label(p,'EXPORT',10,'bold',self.C['muted']).pack(anchor='w',padx=24,pady=(24,8))
        self.btn(p,'↧  Current spread (HD)',self.export_hd).pack(fill='x',padx=18,pady=4)
        self.btn(p,'↧  Every spread (HD)',self.export_all).pack(fill='x',padx=18,pady=4)
        self.btn(p,'↧  Export printable PDF',self.export_pdf).pack(fill='x',padx=18,pady=4)
        self.count_label=self.label(p,'No photos imported',10,color=self.C['muted'],wraplength=230,justify='left')
        self.count_label.pack(side='bottom',anchor='w',padx=22,pady=24)
    def _main(self):
        top=tk.Frame(self.main,bg=self.C['bg']);top.pack(fill='x',padx=32,pady=(24,8))
        self.label(top,'Your scrapbook',24,'bold').pack(side='left')
        self.btn(top,'View originals',self.originals).pack(side='right',padx=4)
        self.btn(top,'Save album',self.save_album).pack(side='right',padx=4)
        self.btn(top,'Fit to window',self.fit).pack(side='right',padx=4)
        self.subtitle=self.label(self.main,'Every photo deserves a place in the story.',11,color=self.C['muted'])
        self.subtitle.pack(anchor='w',padx=33,pady=(0,13))
        stage=tk.Frame(self.main,bg='#101215',highlightthickness=1,highlightbackground=self.C['line']);stage.pack(fill='both',expand=True,padx=32,pady=(0,13))
        self.canvas=tk.Label(stage,bg='#101215',cursor='hand2');self.canvas.pack(fill='both',expand=True,padx=14,pady=14)
        self.canvas.bind('<Configure>',lambda e:self.show_preview());self.canvas.bind('<Button-1>',lambda e:self.originals())
        self.canvas.bind('<MouseWheel>',lambda e:self.navigate(-1 if e.delta>0 else 1))
        bottom=tk.Frame(self.main,bg=self.C['bg']);bottom.pack(fill='x',padx=32,pady=(0,24))
        self.btn(bottom,'←  Previous',lambda:self.navigate(-1)).pack(side='left')
        self.btn(bottom,'Next  →',lambda:self.navigate(1),True).pack(side='right')
        self.page_label=self.label(bottom,'Start by importing photographs',11,color=self.C['muted']);self.page_label.pack(expand=True)
    def fit(self):self.zoom=1;self.show_preview()
    def toggle_cutouts(self):
        if self.cutouts_var.get():
            self.root.config(cursor='watch')
            self.root.update_idletasks()
            backend=cutout_backend()
            self.root.config(cursor='')
            if backend is None:
                self.cutouts_var.set(False)
                messagebox.showerror('AI cutouts unavailable',
                    'The local background-removal model could not start.\n\n'
                    + str(CUTOUT_ERROR)
                    + '\n\nThis installer should include the AI model. Please report this error. '
                    'The first model download requires internet. '
                    'If installation fails, run DIAGNOSE_AI_WINDOWS.bat and share the report.')
                return
            if self.paths:
                idx=min(self.page*PHOTOS_PER_SPREAD+3,len(self.paths)-1)
                if subject_cutout(str(self.paths[idx])) is None:
                    self.cutouts_var.set(False)
                    messagebox.showerror('Cutout failed',str(CUTOUT_ERROR))
                    return
        self.draw()
    def redraw(self):
        if self.paths:self.seed+=271828;self.draw()
    def validate(self,paths):
        good=[];bad=[]
        for p in dict.fromkeys(str(x) for x in paths):
            try:
                with Image.open(p) as im: im.verify()
                good.append(p)
            except Exception:bad.append(Path(p).name)
        return good,bad
    def set_photos(self,paths):
        good,bad=self.validate(paths)
        if not good:
            messagebox.showwarning('No usable photos','No supported photos found. Please try JPG, PNG, or WebP files.');return
        self.paths=sorted(good,key=capture_date);self.page=0;self.seed=random.randrange(10**8);self.album_path=None;self.draw()
        if bad:messagebox.showwarning('Some files skipped',f'{len(good)} imported, {len(bad)} skipped.\n'+', '.join(bad[:8]))
    def import_folder(self):
        folder=filedialog.askdirectory(parent=self.root,title='Select a folder of memories')
        if not folder:return
        paths=sorted((p for p in Path(folder).rglob('*') if p.is_file() and p.suffix.lower() in EXT),key=lambda p:(p.parent.name.lower(),p.name.lower()))
        self.set_photos(paths)
    def import_files(self):
        paths=filedialog.askopenfilenames(parent=self.root,title='Select photographs',filetypes=[('Photographs','*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff *.gif'),('All files','*.*')])
        if paths:self.set_photos(paths)
    def add_photos(self):
        paths=filedialog.askopenfilenames(parent=self.root,title='Add more photographs',filetypes=[('Photographs','*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff *.gif'),('All files','*.*')])
        if not paths:return
        good,bad=self.validate(paths)
        existing=set(map(str,self.paths))
        self.paths.extend(p for p in good if str(p) not in existing)
        self.paths.sort(key=capture_date)
        self.draw()
        if bad:messagebox.showwarning('Skipped photos',f'{len(bad)} files could not be opened.')
    def export_pdf(self):
        if not self.paths:return messagebox.showinfo('No photos','Import photographs first.')
        target=filedialog.asksaveasfilename(parent=self.root,defaultextension='.pdf',initialfile='Keepsake_Journal.pdf',filetypes=[('PDF document','*.pdf')])
        if not target:return
        try:
            self.root.config(cursor='watch');self.root.update_idletasks()
            pages=[]
            for i in range(math.ceil(len(self.paths)/PHOTOS_PER_SPREAD)):
                pages.append(render(self.paths,i,self.seed,scale=2,theme=self.theme_var.get(),cutouts=self.cutouts_var.get()))
            pages[0].save(target,save_all=True,append_images=pages[1:],resolution=180)
            messagebox.showinfo('PDF exported',f'Saved {len(pages)} spreads to:\n{target}')
        except Exception as e:messagebox.showerror('PDF export failed',str(e))
        finally:self.root.config(cursor='')
    def draw(self):
        if self.paths:
            try:self.preview=render(self.paths,self.page,self.seed,theme=self.theme_var.get(),cutouts=self.cutouts_var.get())
            except Exception as e:traceback.print_exc();messagebox.showerror('Render error',str(e));return
            total=math.ceil(len(self.paths)/PHOTOS_PER_SPREAD)
            self.page_label.config(text=f'Spread {self.page+1} of {total}    •    {len(self.paths)} photographs')
            self.count_label.config(text=f'{len(self.paths)} photos · {total} scrapbook spreads\nAll photos are included across the album.')
            self.subtitle.config(text='A little messy. A lot of memories.  •  Click the spread to explore originals.')
        else:
            self.preview=Image.new('RGB',(1200,760),'#d9c3a2');d=ImageDraw.Draw(self.preview)
            d.rounded_rectangle((65,60,1135,695),radius=20,fill='#e9d7b9',outline='#bba07e',width=5)
            d.text((175,275),'A home for all your little moments.',font=font(43),fill='#5c4739')
            d.text((280,350),'Import a photo folder to create your first album.',font=font(23),fill='#816a56')
            self.page_label.config(text='Start by importing photographs')
        self.show_preview()
    def show_preview(self):
        if self.preview is None:return
        w=max(150,self.canvas.winfo_width()-12);h=max(120,self.canvas.winfo_height()-12)
        img=self.preview.copy();img.thumbnail((w,h),Image.Resampling.LANCZOS)
        self.tkpreview=ImageTk.PhotoImage(img);self.canvas.config(image=self.tkpreview)
    def navigate(self,d):
        if self.paths:self.page=max(0,min(math.ceil(len(self.paths)/PHOTOS_PER_SPREAD)-1,self.page+d));self.draw()
    def shuffle(self):
        if self.paths:self.seed=random.randrange(10**8);self.draw()
    def save_album(self):
        if not self.paths:return messagebox.showinfo('Nothing to save','Import photographs first.')
        target=filedialog.asksaveasfilename(parent=self.root,initialdir=HOME,defaultextension='.keepsake',initialfile='My Keepsake.keepsake',filetypes=[('Keepsake album','*.keepsake')])
        if not target:return
        try:
            self.root.config(cursor='watch');self.root.update_idletasks()
            with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
                names=[]
                for i,p in enumerate(self.paths):
                    name=f'photos/{i:06d}{Path(p).suffix.lower()}'
                    z.write(p,name);names.append(name)
                z.writestr('album.json',json.dumps({'version':5,'title':self.name_var.get(),'theme':self.theme_var.get(),'seed':self.seed,'page':self.page,'photos':names,'cutouts':self.cutouts_var.get()}))
            self.album_path=target;messagebox.showinfo('Album saved',f'Saved {len(self.paths)} original photos and your layout in:\n{target}')
        except Exception as e:messagebox.showerror('Save failed',str(e))
        finally:self.root.config(cursor='')
    def open_album(self):
        source=filedialog.askopenfilename(parent=self.root,initialdir=HOME,filetypes=[('Keepsake albums','*.keepsake')])
        if not source:return
        try:
            folder=CACHE/uuid.uuid4().hex;folder.mkdir(parents=True)
            with zipfile.ZipFile(source) as z:
                info=json.loads(z.read('album.json'));names=info['photos'];paths=[]
                if len(names)>10000:raise ValueError('Album contains too many photos')
                for i,name in enumerate(names):
                    if not name.startswith('photos/') or '..' in Path(name).parts or '/' in name[7:]:raise ValueError('Invalid photo entry')
                    ext=Path(name).suffix.lower()
                    if ext not in EXT:raise ValueError('Unsupported photo entry')
                    out=folder/f'{i:06d}{ext}'
                    with z.open(name) as src,out.open('wb') as dst:shutil.copyfileobj(src,dst)
                    paths.append(str(out))
            if not paths:raise ValueError('This album contains no photos')
            self.paths=paths;self.seed=int(info.get('seed',1));self.page=max(0,min(int(info.get('page',0)),math.ceil(len(paths)/PHOTOS_PER_SPREAD)-1))
            self.name_var.set(info.get('title','My memory book'));self.theme_var.set(info.get('theme','Summer camp'))
            self.cutouts_var.set(bool(info.get('cutouts',False)) and cutout_backend() is not None)
            self.album_path=source;self.draw()
        except Exception as e:traceback.print_exc();messagebox.showerror('Cannot open album',str(e))
    def export_hd(self):
        if not self.paths:return messagebox.showinfo('No photos','Import photographs first.')
        target=filedialog.asksaveasfilename(parent=self.root,defaultextension='.png',initialfile=f'Keepsake_Spread_{self.page+1:02d}.png',filetypes=[('PNG image','*.png')])
        if not target:return
        try:
            self.root.config(cursor='watch');self.root.update_idletasks()
            render(self.paths,self.page,self.seed,scale=3,theme=self.theme_var.get(),cutouts=self.cutouts_var.get()).save(target)
            messagebox.showinfo('Export complete',f'Saved 3600 × 2280 image:\n{target}')
        except Exception as e:messagebox.showerror('Export failed',str(e))
        finally:self.root.config(cursor='')
    def export_all(self):
        if not self.paths:return messagebox.showinfo('No photos','Import photographs first.')
        folder=filedialog.askdirectory(parent=self.root,title='Choose where to export all spreads')
        if not folder:return
        total=math.ceil(len(self.paths)/PHOTOS_PER_SPREAD)
        try:
            self.root.config(cursor='watch');self.root.update_idletasks()
            for i in range(total):
                self.page_label.config(text=f'Exporting spread {i+1} / {total}…');self.root.update_idletasks()
                render(self.paths,i,self.seed,scale=3,theme=self.theme_var.get(),cutouts=self.cutouts_var.get()).save(Path(folder)/f'Keepsake_Spread_{i+1:03d}.png')
            self.draw();messagebox.showinfo('All spreads exported',f'Saved {total} high-resolution spreads to:\n{folder}')
        except Exception as e:messagebox.showerror('Export failed',str(e))
        finally:self.root.config(cursor='');self.draw()
    def originals(self):
        if not self.paths:return
        win=tk.Toplevel(self.root);win.title('Photos in this spread');win.configure(bg=self.C['bg']);win.geometry('1000x650')
        outer=tk.Frame(win,bg=self.C['bg']);outer.pack(fill='both',expand=True)
        cv=tk.Canvas(outer,bg=self.C['bg'],highlightthickness=0);bar=tk.Scrollbar(outer,orient='vertical',command=cv.yview)
        bar.pack(side='right',fill='y');cv.pack(side='left',fill='both',expand=True);cv.configure(yscrollcommand=bar.set)
        body=tk.Frame(cv,bg=self.C['bg']);cv.create_window((0,0),window=body,anchor='nw')
        body.bind('<Configure>',lambda e:cv.configure(scrollregion=cv.bbox('all')))
        refs=[]
        for i,p in enumerate(self.paths[self.page*PHOTOS_PER_SPREAD:(self.page+1)*PHOTOS_PER_SPREAD]):
            try:
                with Image.open(p) as src:
                    img=ImageOps.exif_transpose(src).convert('RGB');img.thumbnail((215,170))
                photo=ImageTk.PhotoImage(img);refs.append(photo)
                cell=tk.Frame(body,bg=self.C['panel'],padx=8,pady=8);cell.grid(row=i//4,column=i%4,padx=12,pady=12)
                lbl=tk.Label(cell,image=photo,bg=self.C['panel'],cursor='hand2');lbl.pack();lbl.bind('<Button-1>',lambda e,p=p:self.full_photo(p))
                self.label(cell,Path(p).name[:24],9,color=self.C['muted']).pack(pady=4)
            except Exception:pass
        win.refs=refs
    def full_photo(self,p):
        try:
            with Image.open(p) as src:
                img=ImageOps.exif_transpose(src).convert('RGB');img.thumbnail((1400,900))
            w=tk.Toplevel(self.root);w.title(Path(p).name);w.configure(bg='#111315')
            photo=ImageTk.PhotoImage(img);lbl=tk.Label(w,image=photo,bg='#111315');lbl.image=photo;lbl.pack(padx=12,pady=12)
        except Exception as e:messagebox.showerror('Photo error',str(e))

if __name__=='__main__':
    root=tk.Tk();Studio(root);root.mainloop()
