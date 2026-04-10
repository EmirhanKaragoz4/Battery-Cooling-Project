# =============================================================================
#  SpaceClaim IronPython Automation Script
#  Task: Open SLDPRT, create Named Selections by face area/Z-position,
#        rename bodies, export as .scdoc
# =============================================================================
#
#  HOW TO RUN  (IMPORTANT — read before running):
#  ------------------------------------------------
#  This script MUST be run from INSIDE SpaceClaim's script editor.
#  It will NOT work with a regular Python or CPython interpreter.
#
#  Method 1 — Script Editor (recommended):
#    SpaceClaim ribbon  ->  File  ->  Scripting  ->  Open Script Editor
#    Paste this code into the editor, then press the green Run button.
#
#  Method 2 — Run Script file:
#    SpaceClaim ribbon  ->  File  ->  Scripting  ->  Run Script...
#    Browse to this .py file and click Open.
#
#  WHY clr IS REMOVED:
#    "import clr" is a pythonnet (CPython) construct.  SpaceClaim embeds
#    IronPython 2.7 which has the .NET bridge built in — clr is available
#    automatically and does NOT need to be imported.  Importing it explicitly
#    causes ModuleNotFoundError in IronPython.
#    The SpaceClaim API (DocumentHelper, NamedSelection, etc.) is also
#    pre-loaded by the host, so no clr.AddReference calls are needed either.
# =============================================================================

import os
import sys

# 'math' is available in IronPython's standard library
import math

# SpaceClaim pre-loads its API into the IronPython globals.
# The classes below (DocumentHelper, NamedSelection, Selection, etc.) are
# accessible as bare names without any import statement.
# The from-imports below are only needed for geometry sub-namespace access.
# If they fail on your version, remove them — the bare names still work.
try:
    from SpaceClaim.Api.V241.Geometry import Point, Vector, Matrix
except ImportError:
    try:
        from SpaceClaim.Api.V23.Geometry import Point, Vector, Matrix
    except ImportError:
        pass  # Matrix etc. will still be available as bare globals


# -----------------------------------------------------------------------------
# 0.  CONFIGURATION  — only edit this block
# -----------------------------------------------------------------------------

SLDPRT_PATH = r"C:\Users\emrkr\OneDrive\Desktop\Yeni klasör (2)\part1.SLDPRT"

# Export path is auto-derived: same folder, .scdoc extension
EXPORT_PATH = os.path.join(
    os.path.dirname(SLDPRT_PATH), "part1.scdoc")

# Face area to match.
# SpaceClaim API returns areas in m², so we convert mm² here.
TARGET_AREA_MM2 = 49.691
TARGET_AREA_M2  = TARGET_AREA_MM2 * 1.0e-6   # 4.9691e-5 m²
AREA_TOL_M2     = 1.0e-8                      # ±0.01 mm² tolerance

# Body renames:  { "InstanceName": ("oldBodyName", "newBodyName") }
BODY_RENAMES = {
    "Instance1": ("solid1", "fluid"),
    "Instance2": ("solid1", "fluid"),
    "Instance3": ("solid1", "fluid"),
    "Instance4": ("solid1", "fluid"),
    "Instance5": ("solid1", "coldplate"),
}

# Named Selection names per group, ordered bottom→top (ascending Y)
FAR_Z_NAMES   = ["outlet4", "inlet3",  "outlet2", "inlet1"]
CLOSE_Z_NAMES = ["inlet4",  "outlet3", "inlet2",  "outlet1"]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def open_sldprt(path):
    """Open a file via DocumentHelper and return the active Window."""
    if not os.path.isfile(path):
        raise IOError("File not found: " + path)
    # ImportOptions.Create() is a bare global provided by SpaceClaim
    opts = ImportOptions.Create()
    DocumentHelper.OpenDocument(path, opts)
    win = Window.ActiveWindow
    if win is None:
        raise RuntimeError("OpenDocument succeeded but ActiveWindow is None.")
    return win


def iter_bodies_and_components(part):
    """
    Yield (DesignBody, DesignComponent) tuples for every body in the
    component tree, including nested sub-components.
    """
    def _walk(component):
        for body in component.Content.Bodies:
            yield body, component
        for sub in component.Content.Components:
            for item in _walk(sub):
                yield item

    for top_comp in part.Components:
        for item in _walk(top_comp):
            yield item


def bbox_center(design_face):
    """
    Return the bounding-box center of a DesignFace as a Point.
    Matrix.Identity is available as a bare global in SpaceClaim IronPython.
    """
    bb = design_face.Shape.GetBoundingBox(Matrix.Identity)
    return bb.Center


def get_face_area_m2(design_face):
    """Return face area in m²."""
    return design_face.Shape.Area


def make_named_selection(name, face_list):
    """
    Create a Named Selection from a list of DesignFace objects.
    Deletes any existing NS with the same name first so the script is
    safely re-runnable.
    """
    # Remove duplicates if any
    for existing_ns in NamedSelection.GetAll():
        if existing_ns.Name == name:
            existing_ns.Delete()

    # Selection.Create accepts an IEnumerable of IDesignFace
    sel = Selection.Create(face_list)
    result = NamedSelection.Create(sel, Selection.Empty())

    if result.CreatedNamedSelection is None:
        raise RuntimeError("NamedSelection.Create returned None for: " + name)

    result.CreatedNamedSelection.Name = name
    print("    [NS] " + name + "  (" + str(len(face_list)) + " face)")


def find_top_component(part, comp_name):
    """Return the first top-level DesignComponent whose Master.Name matches."""
    for comp in part.Components:
        if comp.Master.Name == comp_name:
            return comp
    return None


def rename_body_in_component(component, old_name, new_name):
    """
    Find a body named old_name inside component and rename it.
    Returns True if found and renamed.
    SpaceClaim requires a WriteAction context for any model mutation.
    """
    for db in component.Content.Bodies:
        if db.Master.Name == old_name:
            # WriteAction is a bare global context manager in SpaceClaim
            result = RenameObject.Execute(db, new_name)
            if result.Succeeded:
                print("    [RENAME] " + component.Master.Name +
                      " :: " + old_name + "  ->  " + new_name)
                return True
            else:
                # Fallback: direct property assignment
                db.Master.Name = new_name
                print("    [RENAME-fallback] " + component.Master.Name +
                      " :: " + old_name + "  ->  " + new_name)
                return True
    return False


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("SpaceClaim Automation Script")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Step 1: Open the SLDPRT
    # ------------------------------------------------------------------
    print("\n[1] Opening: " + SLDPRT_PATH)
    try:
        win  = open_sldprt(SLDPRT_PATH)
        doc  = win.Document
        part = doc.MainPart
        print("    Opened OK.")
    except Exception as ex:
        print("ERROR in Step 1: " + str(ex))
        return

    # ------------------------------------------------------------------
    # Step 2: Find all faces with area ≈ TARGET_AREA_MM2
    # ------------------------------------------------------------------
    print("\n[2] Scanning faces for area ≈ {:.3f} mm² ...".format(
        TARGET_AREA_MM2))

    matching = []
    try:
        for db, comp in iter_bodies_and_components(part):
            for df in db.Faces:
                a = get_face_area_m2(df)
                if abs(a - TARGET_AREA_M2) <= AREA_TOL_M2:
                    matching.append(df)
    except Exception as ex:
        print("ERROR in Step 2: " + str(ex))
        return

    print("    Found " + str(len(matching)) + " matching face(s).")
    if len(matching) == 0:
        print("    No faces found — check TARGET_AREA_MM2 or AREA_TOL_M2.")
        return
    if len(matching) != 8:
        print("    WARNING: expected 8 faces but found " +
              str(len(matching)) + ". Continuing anyway.")

    # ------------------------------------------------------------------
    # Step 3: Split into far-Z and close-Z groups
    # ------------------------------------------------------------------
    print("\n[3] Splitting by Z coordinate ...")

    # Sort all matching faces by Z descending, split at midpoint
    matching_sorted = sorted(matching,
                             key=lambda f: bbox_center(f).Z,
                             reverse=True)
    mid         = len(matching_sorted) // 2
    far_z_group   = matching_sorted[:mid]   # highest Z  ->  "far"
    close_z_group = matching_sorted[mid:]   # lowest  Z  ->  "close"

    # Within each group sort by Y ascending (bottom → top)
    far_z_group   = sorted(far_z_group,   key=lambda f: bbox_center(f).Y)
    close_z_group = sorted(close_z_group, key=lambda f: bbox_center(f).Y)

    def z_range_str(group):
        zs = [bbox_center(f).Z * 1000 for f in group]   # metres -> mm
        return "[{:.3f}, {:.3f}] mm".format(min(zs), max(zs))

    print("    Far-Z   group: " + str(len(far_z_group))   +
          " faces  Z=" + z_range_str(far_z_group))
    print("    Close-Z group: " + str(len(close_z_group)) +
          " faces  Z=" + z_range_str(close_z_group))

    # ------------------------------------------------------------------
    # Step 4: Create Named Selections
    # ------------------------------------------------------------------
    print("\n[4] Creating Named Selections ...")
    try:
        for name, face in zip(FAR_Z_NAMES, far_z_group):
            make_named_selection(name, [face])
        for name, face in zip(CLOSE_Z_NAMES, close_z_group):
            make_named_selection(name, [face])
    except Exception as ex:
        print("ERROR in Step 4: " + str(ex))
        return

    # ------------------------------------------------------------------
    # Step 5: Rename bodies
    # ------------------------------------------------------------------
    print("\n[5] Renaming bodies ...")
    try:
        for inst_name, (old, new) in BODY_RENAMES.items():
            comp = find_top_component(part, inst_name)
            if comp is None:
                print("    WARNING: Component '" + inst_name +
                      "' not found — skipping.")
                continue
            found = rename_body_in_component(comp, old, new)
            if not found:
                print("    WARNING: Body '" + old + "' not found in '" +
                      inst_name + "' — skipping.")
    except Exception as ex:
        print("ERROR in Step 5: " + str(ex))
        return

    # ------------------------------------------------------------------
    # Step 6: Save as .scdoc
    # ------------------------------------------------------------------
    print("\n[6] Saving as: " + EXPORT_PATH)
    try:
        options = ExportOptions.Create()
        DocumentHelper.SaveAsDocument(EXPORT_PATH, options)
        print("    Saved OK.")
    except Exception as ex:
        print("ERROR in Step 6: " + str(ex))
        return

    print("\n" + "=" * 60)
    print("Script completed successfully.")
    print("Output: " + EXPORT_PATH)
    print("=" * 60)


main()