"""
SolidWorks Automation Script
=============================
For each iteration:
  1. Writes the new radius value into equations.txt
  2. Opens AutoTest.SLDPRT, rebuilds, and exports as Parasolid (.x_t)
  3. Names each file  Channel_<value>.step  in the output folder

Example with defaults (3 iterations, step = 0.15):
  Channel_4.0.step
  Channel_4.5.step
  Channel_5.0.step
"""

import re
import time
import os
import sys

import win32com.client

# =============================================================================
#  USER CONFIGURATION  -  edit this block only
# =============================================================================

SW_BASE_DIR    = r"C:\Users\emrkr\OneDrive\Desktop\Solidworks phyton"
EQUATIONS_FILE = os.path.join(SW_BASE_DIR, "equations2.txt")
SOURCE_PART    = os.path.join(SW_BASE_DIR, "AutoTest.SLDPRT")

# Folder where Channel_X.step files will be saved
OUTPUT_DIR = r"C:\Users\emrkr\OneDrive\Desktop\spaceclaimauto"

# Number of iterations
NUM_ITERATIONS = 10

# Starting Channel_x value (iteration 1)
PARAM_START = {
    "Channel_x": 4.1,
}

# Step added each iteration
# 10 iterations from 4.1 to 5.0: step = 0.1
# Results: 4.1 -> 4.2 -> 4.3 -> 4.4 -> 4.5 -> 4.6 -> 4.7 -> 4.8 -> 4.9 -> 5.0
PARAM_STEP = {
    "Channel_x": 0.1,
}

# =============================================================================
#  END OF USER CONFIGURATION
# =============================================================================

SW_DOC_PART          = 1   # swDocPART
SW_OPEN_DOC_SILENT   = 1   # swOpenDocOptions_Silent

# SolidWorks save/export format constants
SW_SAVE_AS_PARASOLID = 39  # swSaveAsFormat_Parasolid (.x_t)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def param_values_for_iteration(iteration):
    step = iteration - 1
    result = {}
    for param in PARAM_START:
        raw     = PARAM_START[param] + step * PARAM_STEP[param]
        rounded = round(raw, 10)
        result[param] = f"{rounded:g}"
    return result


def output_path(iteration):
    """Returns OUTPUT_DIR/Channel_<value>.step for this iteration."""
    vals      = param_values_for_iteration(iteration)
    channel_x = vals["Channel_x"]
    channel_x = vals["Channel_x"]
    return os.path.join(OUTPUT_DIR, f"Channel_{channel_x}.step")


def update_equations_file(filepath, targets):
    with open(filepath, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    changed      = 0
    result_lines = []
    for line in lines:
        modified = line
        for param, new_val in targets.items():
            pattern = rf'("{re.escape(param)}"\s*=\s*)([\d.]+)'
            m = re.search(pattern, modified)
            if m:
                old_val  = m.group(2)
                modified = re.sub(
                    pattern,
                    lambda mx, nv=new_val: mx.group(1) + nv,
                    modified
                )
                print(f"    BEFORE: {line.rstrip()}")
                print(f"    AFTER : {modified.rstrip()}")
                print(f"    [OK] '{param}': {old_val} -> {new_val}")
                changed += 1
        result_lines.append(modified)

    for param in targets:
        if not re.search(rf'"{re.escape(param)}"\s*=', "".join(result_lines)):
            print(f"    [!] WARNING - '{param}' not found in equations.txt!")

    with open(filepath, "w", encoding="utf-8") as fh:
        fh.writelines(result_lines)
    return changed


def connect_to_solidworks():
    print("[SETUP] Connecting to SolidWorks ...")
    sw_app = None

    # Try attaching to an already-running SolidWorks instance first.
    # This works without elevation and is always preferred.
    try:
        sw_app = win32com.client.GetActiveObject("SldWorks.Application")
        print("       Attached to running instance.")
    except Exception:
        print("       No running instance found.")

    # If not running, try to launch it.
    # NOTE: if this raises 'elevation required' (-2147024156), it means
    # SolidWorks must be started manually as Administrator first.
    # Once it is open, re-run this script and it will attach via GetActiveObject.
    if sw_app is None:
        try:
            sw_app = win32com.client.Dispatch("SldWorks.Application")
            print("       Launched via Dispatch.")
        except Exception as exc:
            err_str = str(exc)
            if "-2147024156" in err_str or "elevation" in err_str.lower() or "yukseltme" in err_str.lower():
                print()
                print("  !! ELEVATION ERROR !!")
                print("  SolidWorks requires Administrator privileges to launch via COM.")
                print("  Please do ONE of the following, then re-run this script:")
                print("    1. Right-click your terminal / VS Code -> Run as Administrator")
                print("    2. Open SolidWorks manually (right-click -> Run as Administrator)")
                print("       then re-run this script - it will attach automatically.")
                print()
                sys.exit(1)
            else:
                raise RuntimeError(f"Dispatch failed: {exc}") from exc

    if sw_app is None:
        raise RuntimeError("SolidWorks COM object is None.")

    sw_app.Visible = True
    print(f"       Connected. Revision: {sw_app.RevisionNumber}\n")
    return sw_app


def open_part(sw_app, filepath):
    import pythoncom
    errors_h   = win32com.client.VARIANT(
        pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    warnings_h = win32com.client.VARIANT(
        pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    model = sw_app.OpenDoc6(
        str(filepath), SW_DOC_PART, SW_OPEN_DOC_SILENT, "",
        errors_h, warnings_h)
    if model is None:
        raise RuntimeError(
            f"OpenDoc6 returned None. "
            f"ErrorCode={errors_h.value}, WarningCode={warnings_h.value}")
    print(f"       Opened OK. ErrorCode={errors_h.value}, "
          f"WarningCode={warnings_h.value}")
    return model


def force_rebuild(model):
    ok = model.ForceRebuild3(True)
    print("       Rebuild OK." if ok else "       [!] ForceRebuild3 returned False.")


def export_parasolid(sw_app, model, dest_path):
    """
    Export as STEP.

    Extension.SaveAs fails on Turkish locale Windows with DISP_E_TYPEMISMATCH.
    Workaround: use the SolidWorks Task Scheduler / eDrawings converter approach:
      1. Save as SLDPRT (proven working)
      2. Open the SLDPRT via a NEW sw_app.OpenDoc6 call
      3. Use SaveAs3 with the STEP path on the freshly opened doc
         (Opening fresh resets the COM dispatch state which avoids the locale bug)
    If that also fails, keep the SLDPRT and convert via subprocess using
    SolidWorks own sldworks.exe /r switch.
    """
    import shutil
    import pythoncom
    import time

    dest_str   = str(dest_path)
    sldprt_tmp = dest_str.replace(".step", "_tmp.SLDPRT")
    sldprt_dst = dest_str.replace(".step", ".SLDPRT")

    print(f"       Exporting STEP: {os.path.basename(dest_str)}")
    os.makedirs(os.path.dirname(dest_str), exist_ok=True)

    # ── Step 1: Save rebuilt model to a temp SLDPRT ──────────────────────────
    try:
        err_v  = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
        warn_v = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
        model.Save3(int(1), err_v, warn_v)
    except Exception:
        try:
            model.Save()
        except Exception as exc:
            print(f"       Save failed: {exc}")
            return False

    # Close to flush
    sw_app.CloseDoc(str(SOURCE_PART))
    time.sleep(2)

    # Copy AutoTest.SLDPRT -> temp SLDPRT
    shutil.copy2(str(SOURCE_PART), sldprt_tmp)
    print(f"       SLDPRT saved: {os.path.basename(sldprt_tmp)}")

    # ── Step 2: Re-open the temp SLDPRT and SaveAs3 to STEP ──────────────────
    errors_h   = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    warnings_h = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    try:
        tmp_model = sw_app.OpenDoc6(
            sldprt_tmp, 1, 1, "", errors_h, warnings_h)
    except Exception as exc:
        print(f"       Could not reopen temp SLDPRT: {exc}")
        tmp_model = None

    if tmp_model:
        try:
            result = tmp_model.SaveAs3(dest_str, int(0), int(1))
            sw_app.CloseDoc(sldprt_tmp)
            if result and os.path.isfile(dest_str):
                size_kb = os.path.getsize(dest_str) / 1024
                print(f"       [OK] STEP exported ({size_kb:.1f} KB)")
                os.remove(sldprt_tmp)
                return True
            else:
                print(f"       SaveAs3 to STEP returned False")
                sw_app.CloseDoc(sldprt_tmp)
        except Exception as exc:
            print(f"       SaveAs3 to STEP threw: {exc}")
            try:
                sw_app.CloseDoc(sldprt_tmp)
            except Exception:
                pass

    # ── Step 3: Keep SLDPRT, rename temp to final SLDPRT name ────────────────
    print(f"       STEP export failed - keeping as SLDPRT")
    try:
        os.rename(sldprt_tmp, sldprt_dst)
        size_kb = os.path.getsize(sldprt_dst) / 1024
        print(f"       Saved: {os.path.basename(sldprt_dst)} ({size_kb:.1f} KB)")
    except Exception:
        shutil.copy2(sldprt_tmp, sldprt_dst)
        os.remove(sldprt_tmp)
    return True
def close_part(sw_app):
    # Part may already be closed by Method B inside export_parasolid — that is fine
    try:
        sw_app.CloseDoc(str(SOURCE_PART))
        print("       Part closed.")
    except Exception:
        print("       Part already closed.")


# =============================================================================
# MAIN
# =============================================================================

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.isfile(EQUATIONS_FILE):
        sys.exit(f"[ERROR] equations.txt not found: {EQUATIONS_FILE}")
    if not os.path.isfile(SOURCE_PART):
        sys.exit(f"[ERROR] Source part not found: {SOURCE_PART}")

    # Print run plan
    print("=" * 65)
    print(f"  SolidWorks Parasolid Export  -  {NUM_ITERATIONS} iterations")
    print("=" * 65)
    print(f"  {'Iter':<6}  {'Output file':<30}  radius")
    print(f"  {'-'*6}  {'-'*30}  ------")
    for i in range(1, NUM_ITERATIONS + 1):
        vals  = param_values_for_iteration(i)
        fname = os.path.basename(output_path(i))
        print(f"  {i:<6}  {fname:<30}  {vals['Channel_x']}")
    print("=" * 65)
    print()

    sw_app  = connect_to_solidworks()
    results = []

    for iteration in range(1, NUM_ITERATIONS + 1):
        dest   = output_path(iteration)
        vals   = param_values_for_iteration(iteration)
        radius = vals['Channel_x']

        print(f"-- Iteration {iteration}/{NUM_ITERATIONS}  ->  "
              f"{os.path.basename(dest)}  (radius={radius})")

        # 1. Write equations.txt
        print("  [1] Updating equations.txt ...")
        update_equations_file(EQUATIONS_FILE, vals)
        print()
        time.sleep(2)

        # 2. Open part fresh
        print("  [2] Opening part ...")
        try:
            model = open_part(sw_app, SOURCE_PART)
        except RuntimeError as exc:
            print(f"      [ERROR] {exc}")
            results.append((dest, radius, False))
            continue
        print()

        # 3. Full rebuild
        print("  [3] Rebuilding ...")
        force_rebuild(model)
        print()

        # 4. Export as Parasolid
        print("  [4] Exporting as Parasolid ...")
        ok = export_parasolid(sw_app, model, dest)
        results.append((dest, radius, ok))
        print()

        # 5. Close part for next iteration
        # (Step C inside export_parasolid may have already closed it - that's fine,
        #  close_part handles the case where it's already closed gracefully)
        print("  [5] Closing part ...")
        close_part(sw_app)
        print()

    # Final report
    print("=" * 65)
    print("  COMPLETED  -  output files:")
    print(f"  {'File':<32}  {'radius':<8}  Status")
    print(f"  {'-'*32}  {'-'*8}  ------")
    for path, radius, ok in results:
        exists = os.path.isfile(path)
        tag    = "OK  " if ok and exists else "FAIL"
        print(f"  {os.path.basename(path):<32}  {radius:<8}  {tag}")
    print("=" * 65)


if __name__ == "__main__":
    main()