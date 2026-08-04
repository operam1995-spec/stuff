# -*- coding: utf-8 -*-
"""
Created on Sun Aug  2 22:41:43 2026

@author: user0
"""


import pandas as pd
import matplotlib
matplotlib.use("Agg")   # remove/comment this line if running interactively in Spyder and you want plots to pop up
import matplotlib.pyplot as plt
from matplotlib.ticker import EngFormatter
import io, os, glob, itertools

import plotly.graph_objects as go
import plotly.colors as pc
from plotly.subplots import make_subplots

# %% Cell 1 - CONFIGURATION -- change these to match your dataset's column names
DEVICE_VAR = "DeviceId"          # column identifying the device
SEG_VARS   = ["VGS", "t11"]      # segregation/grouping variables -- e.g. ["SIM1.VGS", "SIM1.t11"] elsewhere
X_VAR      = "VDS"               # sweep variable used as the x-axis -- e.g. "SIM1.VDS" elsewhere
GROUP_VAR  = SEG_VARS[0]         # which SEG_VAR becomes the trace/legend color grouping
                                  # (all other SEG_VARS become linestyle overlays)

# %% Cell 2 - load ALL parquet files from a folder
folder_path = r"K:\Parquet"    # <-- CHANGE THIS to your folder if needed

parquet_files = glob.glob(os.path.join(folder_path, "*.parquet"))
print(f"Found {len(parquet_files)} parquet files")
for f in parquet_files:
    print(" -", os.path.basename(f))

df_list = []
for file in parquet_files:
    temp = pd.read_parquet(file)
    temp["SourceFile"] = os.path.basename(file)
    df_list.append(temp)

data = pd.concat(df_list, ignore_index=True)

# clean up floating point noise on the sweep + segregation variables
for col in [X_VAR] + SEG_VARS:
    if pd.api.types.is_float_dtype(data[col]):
        data[col] = data[col].round(6)

print("Combined shape:", data.shape)

# %% Cell 3 - what's available
device_list = sorted(data[DEVICE_VAR].unique().tolist())
seg_values = {var: sorted(data[var].unique().tolist()) for var in SEG_VARS}

print("Devices available:", device_list)
for var in SEG_VARS:
    print(f"{var} values available:", seg_values[var])

# %% Cell 3b - print all available variables + build a separate DataFrame per variable
print(f"Total variables in data: {len(data.columns)}")
print("Available variables:")
for col in data.columns:
    print(" -", col)

# one standalone DataFrame per variable, keyed by column name
var_dfs = {col: data[[col]].copy() for col in data.columns}

print(f"\nBuilt {len(var_dfs)} separate DataFrames in var_dfs")
print("Access example: var_dfs['ids']  ->")
print(var_dfs["ids"].head())

# %% Cell 4 - pick a device (used to scope the overlay report)
device_id = device_list[0]

# %% Cell 5 - dict of every device x (all SEG_VARS combo) -- handy for ad-hoc lookups
segregated_dict = {}
seg_value_lists = [seg_values[v] for v in SEG_VARS]
for dev in device_list:
    for combo in itertools.product(*seg_value_lists):
        m = (data[DEVICE_VAR] == dev)
        for var, val in zip(SEG_VARS, combo):
            m &= (data[var] == val)
        subset = data[m]
        if len(subset):
            segregated_dict[(dev,) + combo] = subset.reset_index(drop=True)
print(f"Built {len(segregated_dict)} segregated subsets in segregated_dict")
print(f"Key format: (DeviceId, {', '.join(SEG_VARS)})")

# %% Cell 8 - generic plotter: write plot_vs(...) ONCE, get the all-combos
#             overlay report (SVG + interactive Plotly) automatically

_plot_calls = []   # records every plot_vs(...) call -> replayed into the overlay report

_overlay_vars = [v for v in SEG_VARS if v != GROUP_VAR]
_overlay_combos = list(itertools.product(*[seg_values[v] for v in _overlay_vars])) if _overlay_vars else [()]


def plot_vs(x_col, y_col, x_unit="", y_unit="", ylim=None):
    """
    Write this ONCE per (x, y) pair you want plotted. Just records the
    request -- actual rendering happens in generate_all_reports().
    """
    _plot_calls.append(dict(x_col=x_col, y_col=y_col, x_unit=x_unit, y_unit=y_unit, ylim=ylim))


def _fig_to_svg_markup(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight")
    buf.seek(0)
    svg_text = buf.read()
    buf.close()
    start = svg_text.find("<svg")
    return svg_text[start:]


def _write_html_report(cards, html_path, title, subtitle, n_columns=2):
    if not cards:
        print(f"Nothing to save for '{title}' -- no plots recorded.")
        return
    card_divs = [f'<div class="plot-card">{svg}</div>' for svg in cards]
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
    body {{ font-family: Arial, Helvetica, sans-serif; background: #f5f5f7; margin: 24px; }}
    h1 {{ margin-bottom: 4px; text-align: center; }}
    .subtitle {{ color: #555; margin-top: 0; margin-bottom: 20px; text-align: center; }}
    .grid {{ display: grid; grid-template-columns: repeat({n_columns}, 1fr); gap: 20px; }}
    .plot-card {{ background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
    .plot-card svg {{ width: 100%; height: auto; display: block; }}
    @media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
    <h1>{title}</h1>
    <p class="subtitle">{subtitle}</p>
    <div class="grid">
        {''.join(card_divs)}
    </div>
</body>
</html>
"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved {len(cards)} SVG plots into HTML report: {os.path.abspath(html_path)}")


def _build_combined_fig(x_col, y_col, x_unit="", y_unit=""):
    """Overlay ALL combos of the overlay variables. Color=GROUP_VAR, linestyle=overlay combo."""
    fig, ax = plt.subplots()
    linestyles = ["-", "--", "-.", ":"]
    color_cycle = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    for g_idx, g in enumerate(seg_values[GROUP_VAR]):
        color = color_cycle[g_idx % len(color_cycle)]
        for c_idx, combo in enumerate(_overlay_combos):
            m = (data[DEVICE_VAR] == device_id) & (data[GROUP_VAR] == g)
            for var, val in zip(_overlay_vars, combo):
                m &= (data[var] == val)
            subset = data[m]
            if len(subset):
                combo_label = ", ".join(f"{v}={val}" for v, val in zip(_overlay_vars, combo))
                label = f"{GROUP_VAR}={round(g, 3)}" + (f", {combo_label}" if combo_label else "")
                ax.plot(subset[x_col], subset[y_col], color=color,
                         linestyle=linestyles[c_idx % len(linestyles)], label=label)

    ax.xaxis.set_major_formatter(EngFormatter(unit=x_unit))
    ax.yaxis.set_major_formatter(EngFormatter(unit=y_unit))
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    overlay_title = ", ".join(_overlay_vars) if _overlay_vars else ""
    ax.set_title(f"{y_col} vs {x_col} | {DEVICE_VAR}={device_id} | color={GROUP_VAR}, style={overlay_title}")
    ax.grid(True)
    ax.legend(fontsize=7, loc="center left", bbox_to_anchor=(1.02, 0.5), borderaxespad=0)
    fig.tight_layout()
    return fig, ax


def _plotly_combined_subplots(calls, n_cols, title):
    """Full overlay across all SEG_VARS combos: color=GROUP_VAR, dash=overlay combo."""
    n_plots = len(calls)
    n_rows = -(-n_plots // n_cols)
    subplot_titles = [f"{c['y_col']} vs {c['x_col']}" for c in calls]
    fig = make_subplots(rows=n_rows, cols=n_cols, subplot_titles=subplot_titles)

    color_cycle = pc.qualitative.Plotly
    dash_styles = ["solid", "dash", "dot", "dashdot"]
    seen_legend = set()

    for idx, call in enumerate(calls):
        row = idx // n_cols + 1
        col = idx % n_cols + 1
        x_col, y_col = call["x_col"], call["y_col"]

        for g_idx, g in enumerate(seg_values[GROUP_VAR]):
            color = color_cycle[g_idx % len(color_cycle)]
            for c_idx, combo in enumerate(_overlay_combos):
                m = (data[DEVICE_VAR] == device_id) & (data[GROUP_VAR] == g)
                for var, val in zip(_overlay_vars, combo):
                    m &= (data[var] == val)
                subset = data[m]
                if len(subset) == 0:
                    continue
                combo_label = ", ".join(f"{v}={val}" for v, val in zip(_overlay_vars, combo))
                legend_key = f"{GROUP_VAR}={round(g, 3)}" + (f", {combo_label}" if combo_label else "")
                show_legend = legend_key not in seen_legend
                seen_legend.add(legend_key)
                fig.add_trace(go.Scatter(
                    x=subset[x_col], y=subset[y_col], mode="lines",
                    name=legend_key, legendgroup=legend_key, showlegend=show_legend,
                    line=dict(color=color, dash=dash_styles[c_idx % len(dash_styles)]),
                    hovertemplate=f"{x_col}=%{{x}}<br>{y_col}=%{{y}}<br>{legend_key}<extra></extra>"
                ), row=row, col=col)

        fig.update_xaxes(title_text=f"{x_col} ({call['x_unit']})" if call['x_unit'] else x_col, row=row, col=col)
        fig.update_yaxes(title_text=f"{y_col} ({call['y_unit']})" if call['y_unit'] else y_col, row=row, col=col)
        if call.get("ylim"):
            fig.update_yaxes(range=list(call["ylim"]), row=row, col=col)

    overlay_title = ", ".join(_overlay_vars) if _overlay_vars else ""
    fig.update_layout(
        title=f"{title} | {DEVICE_VAR}={device_id} | color={GROUP_VAR}, style={overlay_title}",
        template="plotly_white",
        height=450 * n_rows,
        legend=dict(font=dict(size=9)),
        hovermode="closest",
    )
    return fig


def generate_all_reports(prefix=None, n_cols=2, open_browser=True, clear=True):
    """
    Call this ONCE after your plot_vs(...) calls. Generates the all-combos
    overlay report in both formats:
      1. <prefix>_all_combos.html         (static SVG)
      2. <prefix>_all_combos_plotly.html  (interactive Plotly)
    """
    if not _plot_calls:
        print("Nothing to plot -- call plot_vs(...) first.")
        return

    if prefix is None:
        prefix = f"{device_id}"

    # static SVG - all combos overlaid
    combo_cards = []
    for call in _plot_calls:
        fig, ax = _build_combined_fig(call["x_col"], call["y_col"], call["x_unit"], call["y_unit"])
        combo_cards.append(_fig_to_svg_markup(fig))
        plt.close(fig)
    overlay_title = ", ".join(_overlay_vars) if _overlay_vars else ""
    path1 = os.path.join(folder_path, f"plots_{prefix}_all_combos.html")
    _write_html_report(combo_cards, path1,
                        title=f"BSIM-CMG - {device_id} - all combos",
                        subtitle=f"{DEVICE_VAR} = {device_id} | color={GROUP_VAR}, style={overlay_title}",
                        n_columns=n_cols)

    # interactive Plotly - all combos overlaid
    fig_combined = _plotly_combined_subplots(_plot_calls, n_cols=n_cols,
                                              title="BSIM-CMG")
    path2 = os.path.join(folder_path, f"plotly_{prefix}_all_combos.html")
    fig_combined.write_html(path2, auto_open=open_browser)
    print(f"Saved: {os.path.abspath(path2)}")

    if clear:
        _plot_calls.clear()


# %% Cell 9 - write plot_vs(...) ONCE -- this list drives the overlay report below
plot_vs(X_VAR, "ids", x_unit="V", y_unit="A")
plot_vs(X_VAR, "gm", x_unit="V", y_unit="S")
plot_vs(X_VAR, "vth", x_unit="V", y_unit="V")
plot_vs(X_VAR, "vdssat", x_unit="V", y_unit="V")

# %% Cell 10 - generate everything (SVG + Plotly, all-combos overlay) from Cell 9
generate_all_reports(n_cols=2)