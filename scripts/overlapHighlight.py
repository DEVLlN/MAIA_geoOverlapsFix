import ROOT
import re
import io
import sys
import csv
import random
import os

def highlight_named_overlaps(
    filename="/home/devlinjenkins/projects/MAIA_GeoOverlapsFixed/MAIA_v0/MAIA_v0.xml.root",
    tolerance=0.001,
    output_root="/home/devlinjenkins/projects/MAIA_GeoOverlapsFixed/highlighted.root",
    output_csv="/home/devlinjenkins/projects/MAIA_GeoOverlapsFixed/overlaps.csv",
    max_overlaps=None
):
    # Import geometry from ROOT file
    ROOT.TGeoManager.Import(filename)
    geom = ROOT.gGeoManager

    # Redirect stdout to capture overlap log output
    buffer = io.StringIO()
    sys.stdout = buffer
    geom.CheckOverlaps(tolerance)
    geom.PrintOverlaps()
    sys.stdout = sys.__stdout__
    log = buffer.getvalue()
    buffer.close()

    # Debug: print raw overlap lines
    print("\n--- DEBUG: Raw overlap lines ---")
    for line in log.splitlines():
        if "Overlap" in line:
            print(line)

    # Updated regex to match leading formatting/spaces
    pattern = r"\s*=\s*Overlap\s+\w+:\s+([\w\d\/_]+)\s+(extruded by|overlapping):\s+([\w\d\/_]+)\s+ovlp=([0-9\.eE\-]+)"
    matches = re.findall(pattern, log)

    print(f"\n--- DEBUG: Regex matched {len(matches)} overlaps ---")

    if not matches:
        print("No overlaps matched — exporting unmodified geometry anyway.")
        geom.Export(output_root)
        return

    print(f"Parsed {len(matches)} overlap records.")

    # Color palette for overlapping volumes
    red_palette = [ROOT.kRed + i for i in range(0, 5)] + \
                  [ROOT.kMagenta + i for i in range(0, 3)] + \
                  [ROOT.kOrange + i for i in range(0, 3)]

    colored_volumes = set()
    label_count = {}

    # Write overlap info to CSV
    with open(output_csv, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Volume", "PartnerVolume", "Overlap(cm)", "ColorIndex", "Label"])

        pair_count = 0

        for full1, relation, full2, ovlp in matches:
            if max_overlaps is not None and pair_count >= max_overlaps:
                break
            pair_count += 1

            volname1 = full1.split("/")[-1]
            volname2 = full2.split("/")[-1]
            overlap_size = float(ovlp)
            color = random.choice(red_palette)

            for volname, partner in [(volname1, volname2), (volname2, volname1)]:
                if volname in colored_volumes:
                    continue

                vol = geom.FindVolumeFast(volname)
                if vol:
                    vol.SetLineColor(color)
                    vol.SetFillColor(color)
                    vol.SetTransparency(70)
                    label_count[volname] = label_count.get(volname, 0) + 1
                    label = f"Overlap#{label_count[volname]} with {partner} (ovlp={overlap_size:.4f})"
                    vol.SetTitle(label)
                    colored_volumes.add(volname)
                    writer.writerow([volname, partner, overlap_size, color, label])
                else:
                    print(f"WARNING: Volume '{volname}' not found.")

    print(f"Colored {len(colored_volumes)} unique volumes.")
    print(f"Overlap data saved to: {output_csv}")
    geom.Export(output_root)
    print(f"Exported updated geometry to: {output_root}")


if __name__ == "__main__":
    highlight_named_overlaps()