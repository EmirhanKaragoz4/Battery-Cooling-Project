import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# ── Data ──────────────────────────────────────────────────────────────────────
velocity = np.array([0.01, 0.02, 0.03, 0.04, 0.05,
                     0.125, 0.2, 0.4, 0.6, 0.8, 1.0])
dP       = np.array([9.468, 20.334, 32.489, 45.873, 60.643,
                     214.150, 444.522, 1408.892,
                     2877.008, 4729.840, 6961.127])
T_max    = np.array([349.753, 330.241, 325.493, 323.180, 322.035,
                     318.903, 317.903, 316.917, 316.553, 316.364, 316.254])
T_avg    = np.array([335.638, 318.108, 312.982, 310.470, 309.166,
                     305.663, 304.590, 303.597, 303.253, 303.075, 302.967])
T_out    = np.array([316.431, 305.892, 302.320, 300.517, 299.728,
                     297.455, 296.688, 295.886, 295.596, 295.447, 295.357])

# ── Derived: 4-channel total pump power ───────────────────────────────────────
inlet_area   = 50e-6          # m²  (4 × 12.5 mm channels)
Q            = velocity * inlet_area          # m³/s per channel
power_single = dP * Q                         # W  (single channel)
power_total  = 4 * power_single               # W  (4 channels total)

# ── Global style ──────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":       "DejaVu Sans",
    "font.size":         11,
    "axes.titlesize":    13,
    "axes.titleweight":  "bold",
    "axes.labelsize":    11,
    "axes.spines.top":   False,
    "axes.grid":         True,
    "grid.linestyle":    "--",
    "grid.alpha":        0.4,
    "legend.fontsize":   10,
    "legend.framealpha": 0.9,
    "xtick.labelsize":   9.5,
    "ytick.labelsize":   9.5,
    "figure.dpi":        150,
})

C_TMAX  = "#E63946"
C_TAVG  = "#457B9D"
C_TOUT  = "#2A9D8F"
C_DP    = "#1A6FBF"
C_PWR   = "#C0392B"

def annotate_points(ax, x, y, color, fmt="{:.1f}", offset=(4, 8)):
    for xi, yi in zip(x, y):
        label = fmt.format(yi)
        ax.annotate(label, xy=(xi, yi),
                    xytext=offset, textcoords="offset points",
                    color=color, fontsize=7.2, ha="left",
                    bbox=dict(boxstyle="round,pad=0.15",
                              fc="white", ec="none", alpha=0.65))

# ═══════════════════════════════════════════════════════════════════════════════
# PLOT 1 – Temperature Analysis
# ═══════════════════════════════════════════════════════════════════════════════
fig1, ax = plt.subplots(figsize=(11, 6))

ax.plot(velocity, T_max, color=C_TMAX, marker="o", linewidth=2.2,
        markersize=7, markerfacecolor="white", markeredgewidth=2,
        label="$T_{max}$")
ax.plot(velocity, T_avg, color=C_TAVG, marker="s", linewidth=2.2,
        markersize=7, markerfacecolor="white", markeredgewidth=2,
        label="$T_{avg}$")
ax.plot(velocity, T_out, color=C_TOUT, marker="^", linewidth=2.2,
        markersize=7, markerfacecolor="white", markeredgewidth=2,
        label="$T_{out}$")

ax.fill_between(velocity, T_max, T_out, alpha=0.07, color=C_TMAX)

annotate_points(ax, velocity, T_max, C_TMAX, fmt="{:.2f}", offset=(4,  8))
annotate_points(ax, velocity, T_avg, C_TAVG, fmt="{:.2f}", offset=(4, -14))
annotate_points(ax, velocity, T_out, C_TOUT, fmt="{:.2f}", offset=(4,  8))

ax.set_title("Battery 1 – Temperature Analysis vs. Inlet Velocity")
ax.set_xlabel("Inlet Velocity (m/s)")
ax.set_ylabel("Temperature (K)")
ax.set_xlim(-0.02, 1.08)
ax.legend(loc="upper right")
ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())

fig1.text(0.99, 0.01, "CFD Simulation Data – Battery Cooling System",
          ha="right", va="bottom", fontsize=8, color="#888888")
fig1.tight_layout()
fig1.savefig("battery1_temperature.png", dpi=150, bbox_inches="tight")
print("Saved → battery1_temperature.png")

# ═══════════════════════════════════════════════════════════════════════════════
# PLOT 2 – Pressure Drop & 4-Channel Total Pump Power
# ═══════════════════════════════════════════════════════════════════════════════
fig2, ax1 = plt.subplots(figsize=(13, 6))
ax2 = ax1.twinx()

l1, = ax1.plot(velocity, dP,
               color=C_DP, marker="o", linewidth=2.2, markersize=7,
               markerfacecolor="white", markeredgewidth=2,
               label=r"Pressure Drop $\Delta P$ (Pa)")
l2, = ax2.plot(velocity, power_total,
               color=C_PWR, marker="s", linewidth=2.2, markersize=7,
               linestyle="--", markerfacecolor="white", markeredgewidth=2,
               label="Total Pump Power – 4 Channels (W)")

# Value labels – ΔP above, Power below each marker
for v, dp in zip(velocity, dP):
    lbl = f"{dp:.1f}" if dp < 100 else f"{dp:.0f}"
    ax1.annotate(lbl, xy=(v, dp), xytext=(4, 8),
                 textcoords="offset points", color=C_DP, fontsize=7.2,
                 ha="left",
                 bbox=dict(boxstyle="round,pad=0.15",
                           fc="white", ec="none", alpha=0.65))

for v, pw in zip(velocity, power_total):
    pw_mw = pw * 1000
    lbl = f"{pw_mw:.3f} mW" if pw_mw < 1 else f"{pw_mw:.2f} mW"
    ax2.annotate(lbl, xy=(v, pw), xytext=(4, -14),
                 textcoords="offset points", color=C_PWR, fontsize=7.2,
                 ha="left",
                 bbox=dict(boxstyle="round,pad=0.15",
                           fc="white", ec="none", alpha=0.65))

ax1.set_xlabel("Inlet Velocity (m/s)", labelpad=8)
ax1.set_ylabel(r"Pressure Drop $\Delta P$ (Pa)",  color=C_DP,  labelpad=8)
ax2.set_ylabel("Total Pump Power (W)",             color=C_PWR, labelpad=8)
ax1.tick_params(axis="y", labelcolor=C_DP)
ax2.tick_params(axis="y", labelcolor=C_PWR)
ax2.spines["top"].set_visible(False)

ax1.set_xlim(-0.02, 1.08)
ax1.xaxis.set_minor_locator(ticker.AutoMinorLocator())
ax1.yaxis.set_minor_locator(ticker.AutoMinorLocator())
ax2.yaxis.set_minor_locator(ticker.AutoMinorLocator())

ax1.set_title(
    "Battery 1 – Pressure Drop & Total Pump Power vs. Inlet Velocity\n"
    r"(4-Channel Total Power: $P_{total} = 4 \times \Delta P \times Q$, "
    r"$A_{inlet}$ = 50×10$^{-6}$ m²)",
    pad=12)

lines  = [l1, l2]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc="upper left", frameon=True, edgecolor="#cccccc")

fig2.text(0.99, 0.01, "CFD Simulation Data – Battery Cooling System",
          ha="right", va="bottom", fontsize=8, color="#888888")
fig2.tight_layout()
fig2.savefig("battery1_pressure_power.png", dpi=150, bbox_inches="tight")
print("Saved → battery1_pressure_power.png")

plt.show()