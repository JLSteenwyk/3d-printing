# R27 corner fit trial

Print [tray_corner_coupon_R27.stl](../../models/tray_corner_coupon_R27.stl) flat in PETG using the same settings as the original coupon. This replaces the original corner coupon for the next fit check.

Photos suggested an approximately 4–6 mm corner gap; this was a visual estimate, not a precise measurement. The trial changes the assumed tray corner radius from 15 to 27 mm (pocket radius 27.6 mm), reducing the nominal diagonal opening by 4.97 mm. Straight-side clearance remains 0.6 mm per side. The original exterior and 80 × 80 × 10 mm coupon envelope are retained.

The exported STL is watertight, consistently wound, and one connected solid. Physical fit is pending. The full test rim and lamp have not been updated to this trial radius; confirm this coupon before propagating the change.

Regenerate with the project's dependencies installed: `python generate_coupon.py`. Outputs are written beside this script.
