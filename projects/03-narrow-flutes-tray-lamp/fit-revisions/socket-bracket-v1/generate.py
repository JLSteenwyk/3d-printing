from pathlib import Path
import json,runpy
import numpy as np
import manifold3d as md
import trimesh
OUT=Path(__file__).resolve().parent

def box(w,d,h,x=0,y=0,z=0):return md.Manifold.cube((w,d,h)).translate((x-w/2,y-d/2,z))
def cyl(d,h,x=0,y=0,z=0):return md.Manifold.cylinder(h,d/2,circular_segments=128).translate((x,y,z))
def export(s,name):
 a=s.to_mesh();m=trimesh.Trimesh(np.asarray(a.vert_properties)[:,:3],np.asarray(a.tri_verts),process=True)
 assert m.is_watertight and m.is_winding_consistent and m.volume>0
 assert len(s.decompose())==1
 m.apply_translation((0,0,-m.bounds[0,2]));m.export(OUT/(name+'.stl'))
 c=trimesh.load(OUT/(name+'.stl'),force='mesh');assert c.is_watertight
 return m
# Assembly coordinates: lamp base pad top Z5. Socket mounting face X-50.
# Socket rim Z75; original hardware clamps a 3 mm PETG plate with 40 mm bore.
base=box(85,54,5,-12.5,0,5)
plate=box(3,52,70,-48.5,0,10)
ring=(cyl(52,3)-cyl(40,3.2,z=-.1)).rotate((0,90,0)).translate((-50,0,75))
bracket=base+plate+ring
# Clear the socket bore through the overlapping upright plate.
bracket-=cyl(40,3.4).rotate((0,90,0)).translate((-50.2,0,75))
# Two triangular webs end below the reserved socket/bulb cylinder.
tri=md.CrossSection([np.array([[-47,10],[-12,10],[-47,42]])])
for y in (-23,23):bracket+=tri.extrude(3).rotate((90,0,0)).translate((0,y+1.5,0))
for x in (-20,20):
 for y in (-12,12):bracket-=cyl(3.4,6,x,y,4.5)
m=export(bracket,'socket_bracket_40mm_PETG')
# Full delivered socket clearance envelope, excluding clamped threaded interface.
socket=cyl(58,73).rotate((0,90,0)).translate((-98,0,75))
bulb=cyl(60,123).rotate((0,90,0)).translate((-25,0,75))
# Broad cylinder is conservative; at the mounting plane actual threads fit 40 mm.
# Exclude 3 mm mounting slab from socket collision check.
socket_free=socket-box(3.4,80,100,-48.5,0,25)
# Forward cylinder overlaps ring beyond mounting interface, so permit threaded
# neck area X-47..-25 only as a 40mm envelope. Rear body begins X-53.
socket_free=socket-box(25,80,100,-38.5,0,25)
socket_free-=box(3,80,100,-51.5,0,25)
assert (bracket^socket_free).volume()<.01
assert (bracket^bulb).volume()<.01
report={'units':'mm','bore_mm':40,'clamping_plate_thickness_mm':3,'bulb_axis_height_mm':75,'mounting_face_x_mm':-50,'base_holes_mm':[[x,y]for x in (-20,20)for y in (-12,12)],'base_holes_diameter_mm':3.4,'assembly_base_z_mm':5,'extents_mm':m.extents.tolist(),'watertight':True,'socket_clearance_estimate_mm':{'rear_x':-98,'front_x':-25,'diameter':58},'bulb_envelope_mm':{'rear_x':-25,'front_x':98,'diameter':60},'mount_interface_fit_confirmed':True,'complete_bracket_fit_confirmed':False,'socket_shape_assumptions':'Photo-based overall allowance; reduced 40 mm threaded neck near mounting face. Verify supplied socket shoulder and neck position.','thermal_validation_completed':False,'cord_restraint_finalized':False}
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
(OUT/'PRINT_AND_FIT.txt').write_text('Socket bracket V1 — unpowered fit prototype\n\nPrint socket_bracket_40mm_PETG.stl upright on its broad base, PETG, 100% scale. Use supports beneath the horizontal ring overhang and inspect the 40 mm hole bridge in Bambu Studio. Remove supports fully. The small gauge was support-free; this taller bracket is not.\n\nWith the cord unplugged, remove the original retaining ring. Slide the socket through the 40 mm mounting hole from the gusset-free/back side, until its shoulder meets the plate. Reinstall the original retaining ring on the bulb side. Hand tighten. Confirm no rocking, shoulder interference or damaged threads. The hole and clamping plate match the accepted 40 mm / 3 mm gauge.\n\nInsert the Govee bulb while unplugged. Check the socket cord grip, bulb and cord clear the base and webs. Confirm the bracket stays stable while gently installing/removing the bulb. Send a side photo of the assembled bracket with bulb before printing the lamp body.\n\nFinal assembly uses four M3 bolts and nuts through the existing 40 x 24 mm pad pattern. Bracket base thickness 5 mm plus lamp pad 5 mm: M3 x 16 mm is a starting length with washers/nuts, verify actual hardware. Install from the open underside. Hardware is not included.\n\nLamp assembly: bracket base bottom sits on pad at Z5; mounting face X-50, bulb axis Z75. Base holes align with existing pad. This STL is shifted to Z0 for printing; mount it on the pad without changing its orientation.\n\nCord routes behind the socket down to the rear opening. Keep cord slack away from the bulb. Cord thickness is not established; do not clamp or pinch insulation. Separate cord restraint still needs finalizing before power-up. This bracket fit test is not thermal or electrical validation. Do not energize the prototype yet.\n')
# Orthographic geometry preview with depth sorted CAD triangles.
from PIL import Image,ImageDraw,ImageFont
im=Image.new('RGB',(1100,900),'#f6f3e9');draw=ImageDraw.Draw(im)
f=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',30)
draw.text((35,25),'Socket bracket V1 — actual CAD',font=f,fill='#263029')
draw.text((35,70),'40 mm hole / 3 mm clamping plate',font=f,fill='#263029')
a=bracket.to_mesh();v=np.asarray(a.vert_properties)[:,:3];faces=np.asarray(a.tri_verts)
right=np.array([.72,-.69,0]);up=np.array([-.25,-.26,.93]);depth=np.cross(right,up)
xy=np.column_stack((v@right,v@up));lo=xy.min(axis=0);hi=xy.max(axis=0);scale=min(900/(hi[0]-lo[0]),650/(hi[1]-lo[1]));xy=(xy-(lo+hi)/2)*scale
xy[:,0]+=550;xy[:,1]=500-xy[:,1]
for face in sorted(faces,key=lambda t:float((v[t]@depth).mean())):
 t=v[face];n=np.cross(t[1]-t[0],t[2]-t[0]);n=n/max(np.linalg.norm(n),1e-8)
 shade=.65+.35*abs(n@np.array([.3,.2,.93]));color=tuple(int(c*shade)for c in (142,157,84))
 draw.polygon([tuple(x)for x in xy[face]],fill=color)
draw.text((35,830),'Print upright in PETG with supports; test unplugged.',font=f,fill='#263029')
im.save(OUT/'bracket-preview.png')
print(json.dumps(report,indent=2))
