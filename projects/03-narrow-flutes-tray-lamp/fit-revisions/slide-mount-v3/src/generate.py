"""Parametric prototype. Requires numpy, manifold3d, trimesh and Pillow.
Run: python generate.py. Units: mm. Hardware mount and thermal behavior provisional.
"""
from pathlib import Path
import json, math, zipfile
import numpy as np
import manifold3d as md
import trimesh
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1]
MODELS = OUT / "models"
DOCS = OUT / "docs"
PREVIEWS = OUT / "previews"
for folder in (MODELS, DOCS, PREVIEWS):
    folder.mkdir(parents=True, exist_ok=True)
P = dict(tray_width=9.45*25.4, tray_depth=7.9*25.4, tray_height=25.4,
         tray_mass_g=13.1*28.349523125, tray_corner_radius=27.0, receiver_outer_corner_radius=18.6,
         side_clearance=0.6, collar_wall=3.0, pocket_depth=8.0,
         body_height=152.0, ledge_width=15.0, diffuser_wall=1.2,
         flute_depth=3.4, flute_pitch=8.4,
         socket_envelope_length=73.0, socket_envelope_diameter=58.0)
if (OUT/'parameters.json').exists():
    P.update(json.loads((OUT/'parameters.json').read_text()))
P.pop('ventilation_gap',None)  # V2 uses vent windows, not V1's open gap.
W,D=P['tray_width'],P['tray_depth']
CW,CD=W+2*P['side_clearance'],D+2*P['side_clearance']
CR=P['tray_corner_radius']+P['side_clearance']
OW,OD=CW+2*P['collar_wall'],CD+2*P['collar_wall']
# Keep the exterior from the physically tested R27 coupon.
OR=P['receiver_outer_corner_radius']
NW,ND=OW-2*P['flute_depth'],OD-2*P['flute_depth']
NR=OR-P['flute_depth']
SEAT=P['body_height']-P['pocket_depth']
DECK=SEAT-4

def rounded(w,d,r,step=0.3):
    """CCW perimeter sampled approximately by arc length; analytic normals."""
    pts=[]; normals=[]
    def line(a,b,n):
        count=max(1,math.ceil(math.dist(a,b)/step))
        for t in np.arange(count)/count:
            pts.append(np.array(a)*(1-t)+np.array(b)*t); normals.append(n)
    def arc(c,start):
        count=max(8,math.ceil(math.pi*r/2/step))
        for theta in np.linspace(start,start+math.pi/2,count,endpoint=False):
            n=np.array([math.cos(theta),math.sin(theta)])
            pts.append(np.array(c)+r*n); normals.append(n)
    line((-w/2+r,-d/2),(w/2-r,-d/2),(0,-1))
    arc((w/2-r,-d/2+r),-math.pi/2)
    line((w/2,-d/2+r),(w/2,d/2-r),(1,0))
    arc((w/2-r,d/2-r),0)
    line((w/2-r,d/2),(-w/2+r,d/2),(0,1))
    arc((-w/2+r,d/2-r),math.pi/2)
    line((-w/2,d/2-r),(-w/2,-d/2+r),(-1,0))
    arc((-w/2+r,-d/2+r),math.pi)
    return np.array(pts),np.array(normals)

def cs(w,d,r):
    return md.CrossSection([rounded(w,d,max(.5,r),.65)[0]])

def box(w,d,h,x=0,y=0,z=0):
    return md.Manifold.cube((w,d,h)).translate((x-w/2,y-d/2,z))

def cylinder(d,h,x=0,y=0,z=0):
    return md.Manifold.cylinder(h,d/2,circular_segments=64).translate((x,y,z))

def extrude(section,z0,z1):
    return section.extrude(z1-z0).translate((0,0,z0))

def mesh(solid):
    m=solid.to_mesh()
    result=trimesh.Trimesh(np.asarray(m.vert_properties)[:,:3],
                           np.asarray(m.tri_verts),process=True)
    result.update_faces(result.nondegenerate_faces())
    result.update_faces(result.unique_faces())
    result.remove_unreferenced_vertices()
    return result

def collar(z0=DECK,ledge=P['ledge_width'],test=False):
    floor_t=2 if test else 4
    seat=z0+floor_t
    outer=cs(OW,OD,OR)
    pocket=cs(CW,CD,CR)
    floor_hole=cs(CW-2*ledge,CD-2*ledge,max(.6,CR-ledge))
    result=extrude(outer-floor_hole,z0,seat)
    result+=extrude(outer,seat,seat+P['pocket_depth'])
    # Straight pocket, with a tapered top 1.2 mm for the tray's entry.
    straight=extrude(pocket,seat-.02,seat+P['pocket_depth']-1.2)
    tapered=pocket.extrude(1.22,scale_top=((CW+.8)/CW,(CD+.8)/CD))
    result-=straight+tapered.translate((0,0,seat+P['pocket_depth']-1.2))
    # Recesses accept adhesive felt/silicone pads. 1 mm pad yields ~0.1 mm
    # nominal compression against the stated tray dimensions; tune by fit test.
    for y in (-1,1):
        result-=box(24,.32,4.5,0,y*(CD/2-.02+.16),seat+1)
    for x in (-1,1):
        result-=box(.32,24,4.5,x*(CW/2-.02+.16),0,seat+1)
        # Grip opening on both short ends; tray remains engaged elsewhere.
        result-=box(12,26,4,x*OW/2,0,seat+P['pocket_depth']-4)
    return result

# V2: one continuous olive print. No loose olive supports or receiver screws.
core_cs=cs(NW,ND,NR)
inner_cs=cs(NW-2*P['diffuser_wall'],ND-2*P['diffuser_wall'],NR-P['diffuser_wall'])
base_band=14.0
corbel_start=124.0
body=extrude(core_cs,0,DECK+.1)
pts,normals=rounded(NW,ND,NR,.2)
lengths=np.linalg.norm(np.roll(pts,-1,axis=0)-pts,axis=1)
arc_lengths=np.r_[0,np.cumsum(lengths[:-1])]
flute_count=round(sum(lengths)/P['flute_pitch'])
targets=(np.arange(flute_count)+.5)*sum(lengths)/flute_count
indices=np.searchsorted(arc_lengths,targets).clip(0,len(pts)-1)
rib_radius=3.5
z_low=base_band
z_high=130.0
ribs=[]
for i in indices:
    x,y=pts[i]-.1*normals[i]
    rib=cylinder(2*rib_radius,z_high-z_low,x,y,z_low)
    cap=md.Manifold.sphere(rib_radius,circular_segments=32)
    rib+=md.Manifold.cylinder(rib_radius,0,rib_radius,circular_segments=64).translate((x,y,z_low-rib_radius))
    rib+=cap.translate((x,y,z_high))
    ribs.append(rib)
body+=md.Manifold.batch_boolean(ribs,md.OpType.Add)
# The ledge grows inward over 16 mm height. Its taper is under 45 degrees
# relative to vertical on the straight faces; corners use larger round fillets.
body+=core_cs.extrude(DECK-corbel_start+.1,scale_top=(OW/NW,OD/ND)).translate((0,0,corbel_start))
body-=extrude(inner_cs,-.1,corbel_start+.01)
FW,FD=CW-2*P['ledge_width'],CD-2*P['ledge_width']
body-=inner_cs.extrude(DECK-corbel_start+.12,
    scale_top=(FW/(NW-2*P['diffuser_wall']),FD/(ND-2*P['diffuser_wall']))).translate((0,0,corbel_start))
receiver=collar(z0=DECK,ledge=P['ledge_width'])
body+=receiver

# Tested V2 receiver, elevated 2 mm for the existing snap-pin tips.
# Existing bracket: X -55..30; Y +/-27; base thickness5.
# Test receiver raises base to Z3. Lateral and vertical running clearance .35/.45.
r=box(118,60.6,3,1,0,0)
for y in (-1,1):
 r+=box(89,2.5,8.45,-13.5,y*28.6,0)
 r+=box(89,3.5,2,-13.5,y*28.1,8.45)
r+=box(2.5,60.6,10.45,-56.6,0,0)
# Lateral spring cantilever: root +X, release by pushing out toward +Y.
# A relief slot isolates the leaf from the receiver floor and side wall.
r-=box(33,8,11,45,29.6,0)
r+=box(4,8,8.45,62,29.6,0)
r+=box(29,1.2,8.45,47,29.6,0)
# Catch face behind bracket front edge; diagonal nose guides insertion.
section=md.CrossSection([np.array([[30.4,25.5],[32.4,25.5],[36.4,29],[30.4,29]])])
r+=section.extrude(7.5)
r+=box(5,4,3,33,31.2,5.45)
# Floor bores allow printed pins through anchor + bracket + receiver.
for x in (-20,20):r-=cylinder(3.4,3.4,x,12,-.2)

slide_receiver=r.translate((0,0,2))
# Extend the free leaf and catch to the bed, keeping relief gaps clear.
# This increases vertical leaf height by 2 mm; integrated latch must be retested.
slide_receiver+=box(29,1.2,2.02,47,29.6,0)
slide_receiver+=section.extrude(2.02)
slide_receiver+=box(4,8,2.02,62,29.6,0)
# Rails connect floor to body without blocking underside pin access or leaf.
for x in (-20,20):
    for sign in (-1,1):
        reach=ND/2-29.8+.25
        body+=box(8,reach,5,x,sign*(29.8+reach/2),0)
body+=slide_receiver

def house_cut(width,eave,base_z,wall_depth=42):
    # Vertical window. The triangular roof closes at 45 degrees, with no
    # unsupported horizontal span. Local X is window width; local Z height.
    w=width/2
    section=md.CrossSection([np.array([[-w,0],[w,0],[w,eave],[0,eave+w],[-w,eave]])])
    return section.extrude(wall_depth).rotate((90,0,0)).translate((0,wall_depth/2,base_z))

upper_cuts=[];lower_cuts=[]
for side in (-1,1):
    for x in np.linspace(-91,91,8):
        if side==1: # Rear: keep the main front face uninterrupted.
            upper_cuts.append(house_cut(22,4,121).translate((x,side*ND/2,0)))
            lower_cuts.append(house_cut(20,2,1).translate((x,side*ND/2,0)))
    for y in np.linspace(-65,65,6):
        if side==-1: # Left end: second airflow path, rear cord exit stays clear.
            upper_cuts.append(house_cut(22,4,121).rotate((0,0,90)).translate((side*NW/2,y,0)))
            lower_cuts.append(house_cut(20,2,1).rotate((0,0,90)).translate((side*NW/2,y,0)))
body-=md.Manifold.batch_boolean(upper_cuts+lower_cuts,md.OpType.Add)
body-=house_cut(12,3,0).translate((0,ND/2,0))
body=body ^ extrude(cs(OW+.05,OD+.05,OR+.025),-.1,P['body_height']+.1)
body=body.simplify(.005) # remove sub-5-micron boolean slivers before STL export

# Optional tan trim fits outside the continuous olive body. It carries no load.
TW,TD=OW+4,OD+4
trim_cs=cs(TW,TD,OR+2)-cs(OW+.6,OD+.6,OR+.3)
tan_base=extrude(trim_cs,0,base_band)
tan_base-=md.Manifold.batch_boolean(lower_cuts,md.OpType.Add)
tan_base-=house_cut(12,3,0).translate((0,OD/2,0))
tan_top=extrude(trim_cs,DECK,P['body_height'])
for x in (-1,1): tan_top-=box(12,26,4,x*TW/2,0,P['body_height']-4)
fit=collar(0,4,True)
corner_fit=fit ^ box(80,80,11,OW/2-40,OD/2-40,0)
bulb=cylinder(60,123).rotate((0,90,0)).translate((-25,0,75))
socket=cylinder(58,73).rotate((0,90,0)).translate((-98,0,75))
# Threaded neck passes the tested mount; clearance envelope is conservative.
socket-=box(28,80,100,-39,0,25)
envelope=bulb+socket
parts={'olive_body_slide_mount_PETG':body,'tan_base_trim_PLA':tan_base,
       'tan_top_trim_PLA':tan_top,'tray_fit_test_rim':fit,'tray_corner_coupon':corner_fit}
report={'version':3,'units':'mm','parameters':P,'flute_count':flute_count,
        'rib_radius_mm':rib_radius,'olive_body_mm':[OW,OD,P['body_height']],
        'trim_footprint_mm':[TW,TD],'pocket_mm':[CW,CD,P['pocket_depth']],
        'tray_seat_mm':SEAT,'total_height_with_tray_mm':SEAT+P['tray_height'],
        'print_intent':'one connected olive body, upright; tan trim printed separately',
        'upper_vent_count':len(upper_cuts),'lower_vent_count':len(lower_cuts),
        'slicer_validation_completed':False,'thermal_validation_completed':False,
        'physical_tray_fit_confirmed':True,'corner_coupon_fit_confirmed':True,
        'corner_fit_evidence':'User accepted printed R27 coupon on 2026-10-02; full R27 rim accepted by user on 2026-10-02','socket_adapter_finalized':False,'slide_receiver_v2_fit_confirmed':True,'integrated_slide_mount_fit_confirmed':False,'pin_underfloor_clearance_mm':2,'integrated_leaf_height_increase_mm':2,'parts':{}}
for name,solid in parts.items():
    m=mesh(solid)
    assert m.is_watertight and m.is_winding_consistent and m.volume>0,name
    assert len(solid.decompose())==1,(name,len(solid.decompose()))
    assert np.all(m.extents<=256),(name,m.extents)
    assert str(solid.status())=='Error.NoError',name
    mesh(solid.translate((0,0,-solid.bounding_box()[2]))).export(MODELS/(name+'.stl'))
    report['parts'][name]={'extents_mm':m.extents.tolist(),
        'volume_cm3':float(m.volume/1000),'watertight':bool(m.is_watertight),
        'winding_consistent':bool(m.is_winding_consistent),'connected_solids':1}
report['hardware_envelope_overlap_cm3']=float((body^envelope).volume()/1000)
assert report['hardware_envelope_overlap_cm3']<.001
report['trim_body_overlap_cm3']={n:float((s^body).volume()/1000) for n,s in [('base',tan_base),('top',tan_top)]}
assert max(report['trim_body_overlap_cm3'].values())<.001
(OUT/'parameters.json').write_text(json.dumps(P,indent=2))
(DOCS/'validation.json').write_text(json.dumps(report,indent=2))

# CAD geometry render: compare exterior with a schematic tray to the bare body.
SCALE=2
im=Image.new('RGB',(1800*SCALE,1200*SCALE),(245,241,230))
draw=ImageDraw.Draw(im)
FONT=next((str(p) for p in [
    Path('/System/Library/Fonts/Supplemental/Arial.ttf'),
    Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
    Path('C:/Windows/Fonts/arial.ttf')
] if p.is_file()), None)
def text(x,y,s,size=22,fill=(45,48,41)):
    draw.text((int(x*SCALE),int(y*SCALE)),s,font=(ImageFont.truetype(FONT,size*SCALE) if FONT else ImageFont.load_default(size=size*SCALE)),fill=fill)
def render(solids,center,scale=2):
    global im,draw
    view=np.array([[.94,.342,0],[-.128,.353,.927],[.317,-.871,.376]])
    light=np.array([.5,-.8,.7]);light/=np.linalg.norm(light)
    half=light+view[2];half/=np.linalg.norm(half)
    canvas=np.array(im)
    depth=np.full(canvas.shape[:2],-np.inf,dtype=np.float32)
    for solid,color in solids:
        m=mesh(solid);p=np.asarray(m.vertices)@view.T
        for f,n in zip(m.faces,m.face_normals):
            if n@view[2]<=0: continue
            shade=.46+.48*max(0,n@light)
            spec=.15*max(0,n@half)**28
            c=tuple(int(min(255,v*shade+255*spec)) for v in color)
            v=p[f]
            q=np.column_stack(((center[0]+v[:,0]*scale)*SCALE,(center[1]-v[:,1]*scale)*SCALE))
            xmin=max(0,int(np.floor(q[:,0].min())));xmax=min(canvas.shape[1]-1,int(np.ceil(q[:,0].max())))
            ymin=max(0,int(np.floor(q[:,1].min())));ymax=min(canvas.shape[0]-1,int(np.ceil(q[:,1].max())))
            if xmax<xmin or ymax<ymin: continue
            xx,yy=np.meshgrid(np.arange(xmin,xmax+1)+.5,np.arange(ymin,ymax+1)+.5)
            a,b,cq=q
            den=(b[1]-cq[1])*(a[0]-cq[0])+(cq[0]-b[0])*(a[1]-cq[1])
            if abs(den)<1e-9: continue
            wa=((b[1]-cq[1])*(xx-cq[0])+(cq[0]-b[0])*(yy-cq[1]))/den
            wb=((cq[1]-a[1])*(xx-cq[0])+(a[0]-cq[0])*(yy-cq[1]))/den
            wc=1-wa-wb
            zz=wa*v[0,2]+wb*v[1,2]+wc*v[2,2]
            ds=depth[ymin:ymax+1,xmin:xmax+1]
            mask=(wa>=-1e-7)&(wb>=-1e-7)&(wc>=-1e-7)&(zz>ds)
            ds[mask]=zz[mask]
            canvas[ymin:ymax+1,xmin:xmax+1][mask]=c
    im=Image.fromarray(canvas);draw=ImageDraw.Draw(im)
olive=(151,161,86);tan=(212,186,148);brown=(140,101,67)
# Tray is a dimensional proxy, not an exact scan of the purchased object.
tray_cs=cs(W,D,P['tray_corner_radius'])
tray_base=extrude(tray_cs,SEAT,SEAT+2)
tray_wall=extrude(tray_cs-cs(W-6,D-6,P['tray_corner_radius']-3),SEAT+1.9,SEAT+25.4)
tray_partitions=box(2.5,D-6,20,36,0,SEAT+2)
tray_partitions+=box(152,2.5,20,-40,-10,SEAT+2)
tray_partitions+=box(2.5,107,20,-40,45,SEAT+2)
text(55,35,'NARROW FLUTES  /  one-piece olive body',37)
text(55,89,'V3 CAD revision: tested slide receiver integrated into lamp body',23)
render([(body,olive),(tan_base,tan),(tan_top,tan),
        (tray_base,tan),(tray_wall,brown),(tray_partitions,tan)],(470,740),2.25)
text(95,845,'WITH TRAY — schematic tray geometry',24)
text(95,885,'Rounded 7 mm ribs / approximately 8.4 mm spacing',21)
text(95,923,'8 mm recessed tray engagement; optional tan sleeves',21)
render([(body,olive)],(1320,725),2.25)
text(975,845,'ONE CONTINUOUS PRINT — tan trim removed',24)
text(975,885,'Integral sloped ledge and self-supporting vent roofs',21)
text(975,923,'No olive frame assembly, feet, or receiver screws',21)
text(55,1050,f'Olive body: {OW:.1f} × {OD:.1f} × 152 mm. With tan trim: {TW:.1f} × {TD:.1f} mm.',23)
text(55,1095,'Actual CAD geometry; transparency is not simulated. Socket adapter, fit, slicing and heat tests remain pending.',20)
im.resize((1800,1200),Image.Resampling.LANCZOS).save(PREVIEWS/'cad-preview-v3.png')
print(json.dumps(report,indent=2))
