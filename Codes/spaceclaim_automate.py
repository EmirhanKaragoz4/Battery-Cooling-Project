import ansys.fluent.core as pyfluent

solver = pyfluent.launch_fluent(
    product_version="25.2", mode="solver", precision="double",
    processor_count=1, ui_mode="no_gui", cleanup_on_exit=True)

solver.tui.file.read_case(
    r"C:\Users\emrkr\OneDrive\Desktop\spaceclaimauto\Radius_0.4.msh.h5")

print("p_v_coupling attrs:")
print([a for a in dir(solver.tui.solve.set.p_v_coupling) if not a.startswith("_")])

print("\nMesh summary:")
print(solver.settings.mesh.get_summary())

solver.exit()