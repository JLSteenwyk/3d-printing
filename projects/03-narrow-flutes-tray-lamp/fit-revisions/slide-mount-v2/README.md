# Slide receiver V2 — corrected insertion clearance

Print only [slide_receiver_test_v2_PETG.3mf](../../models/slide_receiver_test_v2_PETG.3mf), flat in PETG at 100% scale. Reuse existing bracket, anchor and pins. Geometry-only 3MF: choose printer/material/support settings in Bambu Studio; inspect the rail lips before printing.

V1 was blocked by the upright plate: the guide lips overlapped its insertion path, and the tooth extended slightly above the bracket base. V2 moves the lips outward to provide 0.35 mm nominal clearance to the 52 mm upright and lowers the tooth to 7.5 mm, below the upright's 8 mm assembled starting height. Rail overlap over the base is now 0.65 mm; lift retention must be physically tested.

Full bracket rigid-guide insertion checks passed at 91 positions, with the flexible latch area excluded to represent manual release. Seated full-bracket overlap is zero. These are geometric checks, not a simulated flexible latch, slicer test or physical fit confirmation.

Follow the [original fit procedure](../slide-mount/PRINT_AND_TEST.txt): slide upright plate first, hold latch outward, seat at closed stop and release. Check sliding, locking, release and lift-out retention before adding anchor/pins. Stop if anything binds. Keep unplugged. Full lamp integration remains pending acceptance.
