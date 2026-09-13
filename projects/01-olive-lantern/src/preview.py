#!/usr/bin/env python3
"""Dimensionally faithful preview from the model parameters; requires matplotlib/numpy."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from generate import P, ROOT, section

def draw_cap(ax, seat):
    profile = section('cap')
    a = np.linspace(0,2*np.pi,145)
    for p,q in zip(profile,profile[1:]+profile[:1]):
        r,z,_ = np.array([p,q]).T
        rr,aa = np.meshgrid(r,a)
        zz = np.broadcast_to(seat+P.cap_seat-z,rr.shape)
        ax.plot_surface(rr*np.cos(aa),rr*np.sin(aa),zz,
                        color='#748c45',linewidth=0,antialiased=False,shade=True)

fig = plt.figure(figsize=(12,9), facecolor='#f4f0e7')
fig.text(.055,.925,'OLIVE LANTERN',fontsize=27,color='#343d2b',weight='bold')
fig.text(.055,.884,'Mid-century rhythm · translucent PETG · fine fuzzy finish',fontsize=12,color='#646952')

def draw(ax, count):
    a,z = np.meshgrid(np.linspace(0,2*np.pi,145),np.linspace(0,P.height,81))
    f = np.sin(np.pi*z/P.height)**2
    r = P.neck_radius+(P.belly+P.flute_depth*np.cos(P.flutes*a))*f
    for i in range(count):
        ax.plot_surface(r*np.cos(a),r*np.sin(a),z+i*P.height,
                        color='#748c45',linewidth=0,antialiased=False,rcount=81,ccount=145,shade=True)
        if i < count-1:
            ax.plot(P.neck_radius*np.cos(a[0]),P.neck_radius*np.sin(a[0]),
                    np.full(145,(i+1)*P.height),color='#465633',lw=.5)
    draw_cap(ax,P.height*count)
    ax.set_box_aspect((244,244,P.height*count+P.cap_seat))
    ax.view_init(elev=8 if count>1 else 22,azim=35)
    ax.set_axis_off()
    ax.set_xlim(-130,130); ax.set_ylim(-130,130); ax.set_zlim(0,P.height*count+P.cap_seat)

ax = fig.add_axes([.02,.08,.40,.78],projection='3d')
ax.set_facecolor('#f4f0e7'); draw(ax,P.sections)
ax2 = fig.add_axes([.48,.39,.43,.43],projection='3d')
ax2.set_facecolor('#f4f0e7'); draw(ax2,1)
fig.text(.13,.06,f'ASSEMBLED · {P.height*P.sections+P.cap_seat:,.1f} mm tall',fontsize=11,color='#343d2b')
fig.text(.53,.39,'12 soft flutes · Ø243.6 mm maximum',fontsize=12,color='#343d2b')
fig.text(.53,.32,f'{P.sections} sections / {P.height:.0f} mm visible height each',fontsize=12,color='#343d2b')
fig.text(.53,.275,'1.2 mm shell / concealed 6 mm slip joints',fontsize=12,color='#343d2b')
fig.text(.53,.23,'Removable saucer cap / Ø60 mm top vent',fontsize=12,color='#343d2b')
fig.text(.53,.135,'Geometry preview; fuzz and transmitted light\nare not simulated. Physical fit remains unverified.',
         fontsize=10,color='#777969',linespacing=1.5)
fig.savefig(ROOT/'docs'/'preview.png',dpi=160,facecolor=fig.get_facecolor())
