"""Orthographic z-buffer rendering of actual mesh geometry; no invented texture."""
from pathlib import Path
import numpy as np,trimesh
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]

def render(m,elev,azim,width,height,color=(232,219,183)):
 e,a=np.radians([elev,azim]);forward=np.array([np.cos(e)*np.cos(a),np.cos(e)*np.sin(a),np.sin(e)])
 right=np.array([-np.sin(a),np.cos(a),0]);up=np.cross(forward,right)
 v=m.vertices@np.stack([right,up,forward],axis=1)
 lo=v[:,:2].min(0);hi=v[:,:2].max(0);scale=min((width-32)/(hi[0]-lo[0]),(height-32)/(hi[1]-lo[1]))
 v[:,:2]=(v[:,:2]-(hi+lo)/2)*[scale,-scale]+[width/2,height/2]
 depths=np.full((height,width),-np.inf);img=np.full((height,width,3),[245,241,233],dtype=np.uint8)
 light=np.array([-.4,-.6,.8]);light/=np.linalg.norm(light)
 normals=m.face_normals.copy();back=normals@forward<0;normals[back]*=-1
 intensity=.48+.48*np.maximum(normals@light,0)
 intensity[back]*=.7
 colors=np.clip(np.array(color)*intensity[:,None],0,255).astype(np.uint8)
 for tri,col in zip(v[m.faces],colors):
  x0=max(0,int(np.floor(tri[:,0].min())));x1=min(width-1,int(np.ceil(tri[:,0].max())))
  y0=max(0,int(np.floor(tri[:,1].min())));y1=min(height-1,int(np.ceil(tri[:,1].max())))
  if x1<x0 or y1<y0:continue
  (ax,ay,az),(bx,by,bz),(cx,cy,cz)=tri
  den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
  if abs(den)<1e-9:continue
  yy,xx=np.mgrid[y0:y1+1,x0:x1+1];xx=xx+.5;yy=yy+.5
  w0=((by-cy)*(xx-cx)+(cx-bx)*(yy-cy))/den
  w1=((cy-ay)*(xx-cx)+(ax-cx)*(yy-cy))/den;w2=1-w0-w1
  z=w0*az+w1*bz+w2*cz
  d=depths[y0:y1+1,x0:x1+1];mask=(w0>=-1e-8)&(w1>=-1e-8)&(w2>=-1e-8)&(z>d)
  d[mask]=z[mask];img[y0:y1+1,x0:x1+1][mask]=col
 return img

shade=trimesh.load_mesh(ROOT/'models/shade.stl')
fig=plt.figure(figsize=(12,9),facecolor='#f5f1e9')
for x,color,label in [(.07,(232,219,183),'DESERT TAN'),(.53,(111,132,145),'MUTED GREY-BLUE')]:
 body=render(shade,12,-60,750,1250,color=color)
 ax=fig.add_axes([x,.13,.40,.70]);ax.imshow(body);ax.axis('off')
 fig.text(x+.20,.10,label,fontsize=12,fontweight='bold',ha='center',color='#625740')
fig.text(.07,.937,'SOFT SPIRAL',fontsize=28,fontweight='bold',color='#40392c')
fig.text(.07,.895,'Rounded folds · tucked light openings · a quieter, fabric-like finish',fontsize=13,color='#766a55')
fig.text(.07,.04,'Actual mesh geometry. Fuzzy skin appears after slicing. Grey-blue is an illustrative color, not a matched filament swatch.',fontsize=9,color='#766a55')
fig.savefig(ROOT/'previews/colors.png',dpi=150,facecolor=fig.get_facecolor())
