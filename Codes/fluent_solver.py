"""
Fluent Solver Automation
=========================
Resmi PyFluent CHT ornegi baz alinarak yazilmistir:
https://examples.fluent.docs.pyansys.com/version/dev/examples/00-released_examples/03-CHT.html

Calistir:
    python fluent_solver.py
"""

import os
import glob
import json
import ansys.fluent.core as pyfluent

INPUT_DIR = r"C:\Users\emrkr\OneDrive\Desktop\spaceclaimauto"


def run_case(mesh_file, output_file):
    radius = os.path.basename(mesh_file).replace("Radius_","").replace(".msh.h5","")
    print("\n  Mesh  : " + os.path.basename(mesh_file))
    print("  Radius: " + radius)

    print("\n  [1] Fluent baslatiliyor...")
    solver = pyfluent.launch_fluent(
        product_version="25.2",
        mode="solver",
        precision="double",
        processor_count=1,
        show_gui=False,
        cleanup_on_exit=True,
    )

    try:
        # ── 2. Mesh ──────────────────────────────────────────────────────────
        print("  [2] Mesh okunuyor...")
        # CHT example: solver.tui.file.read_case(path)
        solver.tui.file.read_case(mesh_file)

        # ── 3. Modeller ──────────────────────────────────────────────────────
        print("  [3] Modeller...")
        solver.settings.setup.models.viscous.model = "laminar"
        solver.settings.setup.models.energy.enabled = True

        # ── 4. Malzemeler ────────────────────────────────────────────────────
        print("  [4] Malzemeler...")

        # Fluid: air -> water-glycol
        solver.settings.setup.materials.fluid["air"].name = "water-glycol"
        wg = solver.settings.setup.materials.fluid["water-glycol"]
        wg.density.option              = "constant"
        wg.density.value               = 1060
        wg.specific_heat.option        = "constant"
        wg.specific_heat.value         = 3250
        wg.thermal_conductivity.option = "constant"
        wg.thermal_conductivity.value  = 0.4
        wg.viscosity.option            = "constant"
        wg.viscosity.value             = 0.0035

        # Solid: battery-cell (rho=2600, cp=1000, k=2)
        try:
            solver.settings.setup.materials.solid.create("battery-cell")
        except Exception:
            pass
        bm = solver.settings.setup.materials.solid["battery-cell"]
        bm.density.option              = "constant"
        bm.density.value               = 2600
        bm.specific_heat.option        = "constant"
        bm.specific_heat.value         = 1000
        bm.thermal_conductivity.option = "constant"
        bm.thermal_conductivity.value  = 2.0

        # ── 5. Solid zones merge -> battery1 ─────────────────────────────────
        print("  [5] Merge zones...")
        zone_names = ["y-kseklik-ekstr-zyon1-{}-".format(i) for i in range(1, 25)]
        solver.settings.mesh.modify_zones.merge_zones(zone_names=zone_names)
        solver.settings.mesh.modify_zones.zone_name(
            zone_name="y-kseklik-ekstr-zyon1-1-",
            new_name="battery1")

        # ── 6. Zone kosullari ─────────────────────────────────────────────────
        print("  [6] Zone kosullari...")

        # battery1: material
        solver.settings.setup.cell_zone_conditions.solid["battery1"].general.material = "battery-cell"

        # battery1: heat source - Fluent log'dan onerildi
        solver.settings.setup.cell_zone_conditions.solid["battery1"] = {
            "sources": {"terms": {"energy": [500000.0]}, "enable": True}
        }

        # fluid1-4: water-glycol
        for zone in ["fluid1", "fluid2", "fluid3", "fluid4"]:
            solver.settings.setup.cell_zone_conditions.fluid[zone].general.material = "water-glycol"

        # ── 7. Boundary conditions ────────────────────────────────────────────
        print("  [7] Sinir kosullari...")
        for inlet in ["inlet1", "inlet2", "inlet3", "inlet4"]:
            bc = solver.settings.setup.boundary_conditions.velocity_inlet[inlet]
            bc.momentum.velocity.value   = 0.4
            bc.thermal.temperature.value = 295

        # ── 8. Report definitions ─────────────────────────────────────────────
        print("  [8] Raporlar...")
        rds = solver.settings.solution.report_definitions

        rds.volume.create(name="max-temp-bat")
        rds.volume["max-temp-bat"].report_type = "volume-max"
        rds.volume["max-temp-bat"].field       = "temperature"
        rds.volume["max-temp-bat"].cell_zones  = ["battery1"]

        rds.volume.create(name="avg-temp-bat")
        rds.volume["avg-temp-bat"].report_type = "volume-average"
        rds.volume["avg-temp-bat"].field       = "temperature"
        rds.volume["avg-temp-bat"].cell_zones  = ["battery1"]

        rds.surface.create(name="out-pres")
        rds.surface["out-pres"].report_type   = "surface-areaavg"
        rds.surface["out-pres"].field         = "pressure"
        rds.surface["out-pres"].surface_names = ["outlet1","outlet2","outlet3","outlet4"]

        rds.surface.create(name="in-pres")
        rds.surface["in-pres"].report_type   = "surface-areaavg"
        rds.surface["in-pres"].field         = "pressure"
        rds.surface["in-pres"].surface_names = ["inlet1","inlet2","inlet3","inlet4"]

        # Report file: her iterasyonda degerleri CSV'ye yaz
        report_file = output_file.replace(".cas.h5", "_reports.csv")
        solver.settings.solution.monitor.report_files.create(name="all-reports")
        rf = solver.settings.solution.monitor.report_files["all-reports"]
        rf.report_defs = ["max-temp-bat", "avg-temp-bat", "out-pres", "in-pres"]
        rf.file_name   = report_file
        rf.print = True

        # ── 9. Initialize ─────────────────────────────────────────────────────
        print("  [9] Initialize...")
        # CHT example: solver.tui.solve.initialize.hyb_initialization()
        solver.tui.solve.initialize.hyb_initialization()

        # ── 10. Loosely Coupled CHT
        print("  [10] CHT...")
        solver.scheme.eval('(ti-menu-load-string "/solve/set/loosely-coupled-cht yes implicit 5")')

        # ── 11. 300 iterasyon ─────────────────────────────────────────────────
        print("  [11] 300 iterasyon...")
        # CHT example: solver.tui.solve.iterate("250")
        solver.tui.solve.iterate("300")

        # ── 12. Sonuclar ──────────────────────────────────────────────────────
        print("  [12] Sonuclar...")
        max_temp = avg_temp = out_pres = in_pres = 0.0
        try:
            import csv
            report_file = output_file.replace(".cas.h5", "_reports.csv")
            if os.path.isfile(report_file):
                with open(report_file, "r") as f:
                    lines = [l.strip() for l in f.readlines()
                             if l.strip() and not l.startswith("(")]
                # Header satirini bul
                header = None
                data_rows = []
                for line in lines:
                    parts = line.split()
                    if parts and parts[0] == "iter":
                        header = parts
                    elif header and parts and parts[0].lstrip("!").isdigit():
                        data_rows.append(parts)
                if data_rows and header:
                    last = data_rows[-1]
                    # lstrip("!") ile converged marker kaldir
                    def get_col(name):
                        for i, h in enumerate(header):
                            if name in h and i < len(last):
                                return float(last[i].lstrip("!"))
                        return 0.0
                    max_temp = get_col("max-temp")
                    avg_temp = get_col("avg-temp")
                    out_pres = get_col("out-pres")
                    in_pres  = get_col("in-pres")
            else:
                print("       Report CSV bulunamadi: " + report_file)
        except Exception as ex:
            print("       Sonuc parse hatasi: " + str(ex))

        print("       max_temp = {:.2f} K".format(max_temp))
        print("       avg_temp = {:.2f} K".format(avg_temp))
        print("       delta_P  = {:.2f} Pa".format(in_pres - out_pres))
        print("  [13] Kaydediliyor...")
        # CHT example: solver.tui.file.write_case_data(path)
        solver.tui.file.write_case_data(output_file)

        return {
            "radius":   float(radius),
            "max_temp": max_temp,
            "avg_temp": avg_temp,
            "in_pres":  in_pres,
            "out_pres": out_pres,
        }

    finally:
        solver.exit()


def update_results_json(entry):
    results_file = os.path.join(INPUT_DIR, "results.json")
    results = []
    if os.path.isfile(results_file):
        with open(results_file, "r", encoding="utf-8") as f:
            try:
                results = json.load(f)
            except Exception:
                results = []

    updated = False
    for r in results:
        if abs(r["radius"] - entry["radius"]) < 0.001:
            r.update(entry)
            updated = True
            break
    if not updated:
        results.append(entry)

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("  results.json guncellendi.")


def main():
    print("=" * 60)
    print("  Fluent Solver Automation")
    print("=" * 60)

    files = sorted(glob.glob(os.path.join(INPUT_DIR, "Radius_*.msh.h5")))
    if not files:
        print("Radius_*.msh.h5 bulunamadi: " + INPUT_DIR)
        input("Enter...")
        return

    print("  {} dosya bulundu.\n".format(len(files)))

    for i, mesh_file in enumerate(files, start=1):
        radius      = os.path.basename(mesh_file).replace("Radius_","").replace(".msh.h5","")
        output_file = os.path.join(INPUT_DIR, "Radius_{}.cas.h5".format(radius))

        print("\n[{}/{}] Radius={}".format(i, len(files), radius))
        print("-" * 60)

        try:
            entry = run_case(mesh_file, output_file)
            update_results_json(entry)
            print("  [OK] Radius_{} tamamlandi.".format(radius))
        except Exception as ex:
            print("  [HATA] Radius_{}: ".format(radius) + str(ex))
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("  TUM DOSYALAR TAMAMLANDI")
    print("=" * 60)
    input("Enter...")


if __name__ == "__main__":
    main()
