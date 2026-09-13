#!/usr/bin/env python3
"""Generate watertight, mm-scale lantern STLs using only Python's standard library.

Edit Parameters to resize. Fuzz belongs in the slicer, never on the mating rings.
The mesh is a closed cross-section swept around Z, with tapered axial fluting.
"""
from collections import Counter
from dataclasses import dataclass, asdict
import json
import math
from pathlib import Path
import struct


@dataclass(frozen=True)
class Parameters:
    neck_radius: float = 110.0
    belly: float = 10.0
    flute_depth: float = 1.8
    flutes: int = 12
    wall: float = 1.2
    height: float = 210.0
    collar_height: float = 6.0
    radial_clearance: float = 0.35
    sections: int = 7
    angular_steps: int = 360
    vertical_steps: int = 105
    cable_height: float = 10.0
    cable_top_width: float = 8.0
    cable_slope: float = 1.5
    cap_radius: float = 112.0
    cap_vent_radius: float = 30.0
    cap_roof: float = 1.6
    cap_seat: float = 3.2


P = Parameters()
ROOT = Path(__file__).resolve().parents[1]


def section(kind):
    """Ordered (radius, z, flute amplitude) around the material cross-section."""
    male = P.neck_radius - P.wall - P.radial_clearance
    if kind == 'cap':
        # Print exterior face down. Flip for assembly: the 6 mm collar enters
        # top.stl and its rim seats on the annulus at cap_seat. Central vent
        # stays open. The bevel prints inward, so there are no roof bridges.
        return [(P.cap_radius, 0, 0), (P.cap_radius, 1.2, 0),
                (P.neck_radius, P.cap_seat, 0), (male, P.cap_seat, 0),
                (male, P.cap_seat+P.collar_height, 0),
                (male-P.wall, P.cap_seat+P.collar_height, 0),
                (male-P.wall, P.cap_roof, 0),
                (P.cap_vent_radius, P.cap_roof, 0), (P.cap_vent_radius, 0, 0)]
    if kind == 'fit_female':
        return [(P.neck_radius, 0, 0), (P.neck_radius, 12, 0),
                (P.neck_radius-P.wall, 12, 0), (P.neck_radius-P.wall, 0, 0)]
    if kind == 'fit_male':
        return [(P.neck_radius, 0, 0), (P.neck_radius, 6, 0),
                (male, 6, 0), (male, 12, 0), (male-P.wall, 12, 0),
                (male-P.wall, 0, 0)]
    zs = [P.height*i/P.vertical_steps for i in range(P.vertical_steps+1)]
    def body(z, inner=False):
        f = math.sin(math.pi*z/P.height)**2
        return (P.neck_radius+P.belly*f-(P.wall if inner else 0), z, P.flute_depth*f)
    outline = [body(z) for z in zs]
    if kind != 'top':
        outline += [(male, P.height, 0), (male, P.height+P.collar_height, 0),
                    (male-P.wall, P.height+P.collar_height, 0),
                    (male-P.wall, P.height, 0)]
        # Inner taper over the final 2 mm supports the collar without a bridge.
        outline += [body(z, True) for z in reversed(zs[:-1])]
    else:
        outline += [body(z, True) for z in reversed(zs)]
    return outline


def mesh(kind):
    profile = section(kind)
    n = P.angular_steps
    vertices = []
    for r, z, amplitude in profile:
        for j in range(n):
            a = math.tau*j/n
            radius = r+amplitude*math.cos(P.flutes*a)
            # Rear cable arch is open to the floor; it is not a sealed hole.
            # Blend the displacement to zero by Z=14 so rings never cross.
            arc = abs((a-math.pi+math.pi) % math.tau-math.pi)*P.neck_radius
            arch = max(0, P.cable_height-max(0, arc-P.cable_top_width/2)*P.cable_slope)
            zz = z + (arch*max(0, 1-z/14) if kind == 'base' else 0)
            vertices.append((radius*math.cos(a), radius*math.sin(a), zz))
    faces = []
    for k in range(len(profile)):
        nxt = (k+1) % len(profile)
        for j in range(n):
            a, b = k*n+j, k*n+(j+1) % n
            c, d = nxt*n+(j+1) % n, nxt*n+j
            faces.extend([(a,b,c), (a,c,d)])
    return vertices, faces


def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def validate(vertices, faces):
    edges = Counter()
    directed = Counter()
    volume = 0.0
    for face in faces:
        a,b,c = [vertices[i] for i in face]
        normal = cross(tuple(b[i]-a[i] for i in range(3)), tuple(c[i]-a[i] for i in range(3)))
        assert sum(x*x for x in normal) > 1e-16, 'Degenerate triangle'
        volume += sum(a[i]*cross(b,c)[i] for i in range(3))/6
        for u,v in zip(face, face[1:]+face[:1]):
            edges[tuple(sorted((u,v)))] += 1
            directed[(u,v)] += 1
    assert all(n == 2 for n in edges.values()), 'Non-manifold edge'
    assert all(directed[(v,u)] == n for (u,v),n in directed.items()), 'Inconsistent winding'
    assert volume > 0, 'Inverted mesh'
    low = [min(v[i] for v in vertices) for i in range(3)]
    high = [max(v[i] for v in vertices) for i in range(3)]
    size = [high[i]-low[i] for i in range(3)]
    assert all(x <= 256 for x in size), 'Exceeds P2S nominal build volume'
    return {'triangles': len(faces), 'bounds_mm': [low,high],
            'size_mm': size, 'volume_cm3': volume/1000,
            'closed_manifold': True, 'consistent_winding': True}


def write_stl(path, vertices, faces):
    with path.open('wb') as out:
        out.write(b'Olive Lantern | units mm'.ljust(80, b'\0'))
        out.write(struct.pack('<I', len(faces)))
        for face in faces:
            a,b,c = [vertices[i] for i in face]
            normal = cross(tuple(b[i]-a[i] for i in range(3)),tuple(c[i]-a[i] for i in range(3)))
            length = math.sqrt(sum(x*x for x in normal))
            out.write(struct.pack('<12fH', *(x/length for x in normal), *a,*b,*c,0))


def main():
    assert P.height/P.vertical_steps == 2, 'Inner collar taper requires 2 mm axial sampling'
    assert P.wall > 0 and P.radial_clearance > 0
    models = ROOT/'models'
    models.mkdir(exist_ok=True)
    results = {'parameters': asdict(P), 'parts': {}}
    assert 0 < P.cap_vent_radius < P.neck_radius-2*P.wall-P.radial_clearance
    assert 0 < P.cap_roof < P.cap_seat
    for kind in ['base','middle','top','cap','fit_male','fit_female']:
        vertices,faces = mesh(kind)
        results['parts'][kind] = validate(vertices,faces)
        write_stl(models/f'{kind}.stl', vertices,faces)
    (ROOT/'docs'/'mesh-report.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))


if __name__ == '__main__':
    main()
