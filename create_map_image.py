"""
Create a static PNG map visualization in FTM editorial style.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
from matplotlib.lines import Line2D
from shapely.geometry import Polygon, Point
import geopandas as gpd
import contextily as cx
import numpy as np


# ============================================================
# FONT CONFIGURATION
# Preferred → Fallback
#   Pilat Compressed Bold   → Franklin Gothic Demi Cond
#   Pilat Condensed         → Franklin Gothic Medium Cond
#   Lyon Text               → Georgia
#   GT America Medium       → Gill Sans MT
#   GT America Mono Medium  → Consolas
# ============================================================
def find_font(*names):
    available = {f.name for f in fm.fontManager.ttflist}
    for name in names:
        if name in available:
            return name
    return names[-1]


FONT_LOGO = find_font('Pilat Compressed', 'Franklin Gothic Demi Cond',
                       'Gill Sans MT Ext Condensed Bold', 'Arial')
FONT_TITLE = find_font('Pilat Condensed', 'Franklin Gothic Medium Cond',
                        'Gill Sans MT Condensed', 'Arial')
FONT_BODY = find_font('Lyon Text', 'Georgia')
FONT_UI = find_font('GT America', 'Gill Sans MT', 'Franklin Gothic Book', 'Arial')
FONT_MONO = find_font('GT America Mono', 'Consolas', 'DejaVu Sans Mono')


# ============================================================
# FTM COLOR PALETTE — per spec
# ============================================================
C = {
    # Primair
    'rood':        '#FF5725',   # merkaccent, highlights, key data
    'zwart':       '#000000',   # tekst, assen
    'offwhite':    '#F5F1ED',   # achtergrond
    # Neutraal / UI
    'goud':        '#B48559',
    'zilver':      '#A49B93',
    'dollargroen': '#706F5F',
    'duifgrijs':   '#204951',
    # Categoriekleuren (eurobiljetten)
    'bruinrood':   '#B43C09',
    'blauw':       '#0068AF',
    'lichtoranje': '#FFC882',
    'mosgroen':    '#505C12',
    'fluorgeel':   '#D5E43B',
    'paars':       '#A7057D',
}


# ============================================================
# DATA
# ============================================================
GOAT_FARM = Point(6.1801997, 52.2742744)

polygons = {
    '400 woningen': {
        'coords': [(6.1672178, 52.2786201), (6.1673895, 52.2777274),
                    (6.1659732, 52.2772547), (6.1676469, 52.2754692),
                    (6.1698142, 52.2752329), (6.1693636, 52.2743795),
                    (6.1722818, 52.2743926), (6.173462, 52.2776617),
                    (6.1702219, 52.2783313), (6.1672178, 52.2786201)],
        'color': C['blauw'],
        'label': 'Reeds gebouwd (400)'
    },
    '800 woningen': {
        'coords': [(6.173462, 52.2776617), (6.1763947, 52.277302),
                    (6.1776822, 52.2797701), (6.1705368, 52.2807153),
                    (6.1703222, 52.2801509), (6.1678117, 52.2804397),
                    (6.1671679, 52.2787068), (6.1701505, 52.2784442),
                    (6.173462, 52.2776617)],
        'color': C['paars'],
        'label': 'Wordt nu gebouwd (800)'
    },
    '1600 woningen': {
        'coords': [(6.17936, 52.2762582), (6.1783729, 52.2739343),
                    (6.1967192, 52.2736454), (6.1963759, 52.2754442),
                    (6.1973415, 52.276954), (6.1911402, 52.2777417),
                    (6.1872993, 52.2771115), (6.183158, 52.2762582),
                    (6.17936, 52.2762582)],
        'color': C['lichtoranje'],
        'label': 'Nog te bouwen (1.640)'
    },
    '40 woningen': {
        'coords': [(6.1865383, 52.2710481), (6.1868674, 52.2699887),
                    (6.1879484, 52.269978), (6.1883829, 52.2704245),
                    (6.1883922, 52.2711852), (6.1865383, 52.2710481)],
        'color': C['lichtoranje'],
        'label': None
    }
}

varkens = Point(6.1886441, 52.2772935)
koeien = Point(6.192552, 52.2759297)


# ============================================================
# BUILD GEODATAFRAMES
# ============================================================
gdf_list = []
for name, data in polygons.items():
    poly = Polygon(data['coords'])
    gdf_list.append({
        'name': name,
        'geometry': poly,
        'color': data['color'],
        'label': data['label']
    })

gdf_polygons = gpd.GeoDataFrame(gdf_list, crs='EPSG:4326')
gdf_polygons_mercator = gdf_polygons.to_crs(epsg=3857)

goat_gdf = gpd.GeoDataFrame([{'geometry': GOAT_FARM}], crs='EPSG:4326').to_crs(epsg=3857)
varkens_gdf = gpd.GeoDataFrame([{'geometry': varkens}], crs='EPSG:4326').to_crs(epsg=3857)
koeien_gdf = gpd.GeoDataFrame([{'geometry': koeien}], crs='EPSG:4326').to_crs(epsg=3857)

goat_point = goat_gdf.geometry.iloc[0]
circle_geometry = goat_point.buffer(1000)


# ============================================================
# COMPUTE FIGURE SIZE from data aspect ratio
# ============================================================
bounds = gdf_polygons_mercator.total_bounds
margin = 500
x_min, x_max = bounds[0] - margin, bounds[2] + margin
y_min, y_max = bounds[1] - margin, bounds[3] + margin

data_w = x_max - x_min
data_h = y_max - y_min
map_aspect = data_w / data_h   # width / height in meters

fig_w = 14.0                   # inches
# Compute header height from actual text content (in points → inches)
_logo = 11 + 5           # logo + gap
_title = 36 + 8          # title + gap
_subtitle = 3 * 12 * 1.3 # 3 lines at 12pt, 1.3 linespacing
_pad = 4 + 2             # top + bottom pad
header_inches = (_pad + _logo + _title + _subtitle) / 72 - (1 / 2.54) - (0.25 / 2.54)  # cut 1.25cm from top
source_inches = 0.25           # source line
map_inches = fig_w / map_aspect
fig_h = header_inches + map_inches + source_inches

# Fractions for axes positioning
header_frac = header_inches / fig_h
source_frac = source_inches / fig_h
map_frac = map_inches / fig_h

fig = plt.figure(figsize=(fig_w, fig_h), facecolor=C['offwhite'])
ax = fig.add_axes([0.0, source_frac, 1.0, map_frac])
ax.set_facecolor(C['offwhite'])


# ============================================================
# PLOT MAP ELEMENTS
# ============================================================

# Housing polygons
for idx, row in gdf_polygons_mercator.iterrows():
    ax.add_patch(mpatches.Polygon(
        list(row['geometry'].exterior.coords),
        facecolor=row['color'],
        edgecolor=row['color'],
        alpha=0.30,
        linewidth=1.8,
        zorder=3
    ))

    # Percentage labels for areas inside risk zone
    intersection = row['geometry'].intersection(circle_geometry)
    if not intersection.is_empty and intersection.area > 0:
        percentage = (intersection.area / row['geometry'].area) * 100
        centroid = intersection.centroid
        ax.text(centroid.x, centroid.y, f'{percentage:.0f}%',
                fontsize=18, fontweight='bold', color=C['zwart'],
                fontfamily=FONT_UI,
                ha='center', va='center',
                bbox=dict(facecolor='white', edgecolor='none',
                          alpha=0.85, boxstyle='round,pad=0.3'),
                zorder=6)

# 1km radius circle — FTM Rood (key data highlight)
circle_x, circle_y = circle_geometry.exterior.xy
ax.plot(circle_x, circle_y, color=C['rood'], linewidth=2.2, linestyle='--',
        dashes=(10, 6), alpha=0.85, zorder=4)
ax.fill(circle_x, circle_y, color=C['rood'], alpha=0.025, zorder=2)

# Goat farm marker — FTM Rood (merkaccent)
goat_gdf.plot(ax=ax, color=C['rood'], markersize=250, zorder=5,
              edgecolor='white', linewidth=2.5, marker='o')

# Other farms — neutral
varkens_gdf.plot(ax=ax, color=C['dollargroen'], markersize=140, zorder=5,
                 edgecolor='white', linewidth=2, marker='o')
koeien_gdf.plot(ax=ax, color=C['dollargroen'], markersize=140, zorder=5,
                edgecolor='white', linewidth=2, marker='o')

# Basemap — no labels for clean editorial look
cx.add_basemap(ax, crs=gdf_polygons_mercator.crs,
               source=cx.providers.CartoDB.PositronNoLabels, zoom=14)

# Set bounds to exact data extent
ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)

# Remove axes
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)


# ============================================================
# HEADER — chained positions, top-down
# ============================================================
map_top = source_frac + map_frac

# Convert point sizes to figure fractions for spacing
def pts(pt):
    return (pt / 72) / fig_h

# Shift header + legend down by 2 cm
shift = (1.50 / 2.54) / fig_h  # 1.50 cm → figure fraction
y = 1.0 - pts(4) - shift

# Logo — GT America Mono Medium, ALL CAPS
fig.text(0.04, y, 'FOLLOW THE MONEY',
         fontsize=11, fontweight='bold', fontfamily=FONT_MONO,
         color=C['zilver'], ha='left', va='top',
         transform=fig.transFigure)
y -= pts(16)

# Title — Pilat Condensed
fig.text(0.04, y, 'Nieuwbouw rondom geitenboerderij',
         fontsize=36, fontweight='bold', fontfamily=FONT_TITLE,
         color=C['zwart'], ha='left', va='top',
         transform=fig.transFigure)
y -= pts(44)

# Subtitle — GT America Regular
fig.text(0.04, y,
         'Binnen 1 kilometer van deze geitenhouderij zijn al 400 woningen\n'
         'gebouwd. Als drie andere bouwplannen doorgaan, komen daar nog\n'
         '2.440 woningen bij.',
         fontsize=12, fontfamily=FONT_UI,
         color=C['dollargroen'], ha='left', va='top',
         transform=fig.transFigure, linespacing=1.3)


# ============================================================
# LEGEND — 2 columns × 3 rows, top-right, no frame
# ============================================================
sw_w = 0.016
sw_h = 0.010
leg_step = pts(22)

# Column 1: polygon categories (left col)
col1_x = 0.55
col1_items = [
    ('swatch', C['blauw'],       'Reeds gebouwd (400)'),
    ('swatch', C['paars'],       'Wordt nu gebouwd (800)'),
    ('swatch', C['lichtoranje'], 'Nog te bouwen (1.640)'),
]

# Column 2: markers (right col)
col2_x = 0.80
col2_items = [
    ('dash',   C['rood'],        '1 km risicozone'),
    ('circle', C['rood'],        'Geitenhouderij'),
    ('circle', C['dollargroen'], 'Overige veehouderij'),
]

# Top of legend aligns with title
leg_y = 1.0 - pts(4) - shift - pts(16)  # same as title top

for col_x, items in [(col1_x, col1_items), (col2_x, col2_items)]:
    for i, (kind, color, label) in enumerate(items):
        yi = leg_y - i * leg_step

        if kind == 'swatch':
            fig.patches.append(mpatches.FancyBboxPatch(
                (col_x, yi - sw_h / 2), sw_w, sw_h,
                boxstyle="square,pad=0",
                facecolor=color, edgecolor='none', alpha=0.6,
                transform=fig.transFigure, figure=fig, zorder=10
            ))
        elif kind == 'dash':
            fig.lines.append(Line2D(
                [col_x + 0.001, col_x + sw_w - 0.001], [yi, yi],
                color=color, linewidth=2, linestyle='--',
                dashes=(4, 3), transform=fig.transFigure, figure=fig
            ))
        elif kind == 'circle':
            fig.patches.append(mpatches.Circle(
                (col_x + sw_w / 2, yi), radius=0.005,
                facecolor=color, edgecolor='white', linewidth=1.5,
                transform=fig.transFigure, figure=fig, zorder=10
            ))

        fig.text(col_x + sw_w + 0.008, yi, label,
                 fontsize=11, fontfamily=FONT_UI, color=C['zwart'],
                 va='center', transform=fig.transFigure)


# ============================================================
# SOURCE — GT America Mono Medium, ALL CAPS
# ============================================================
fig.text(0.04, 0.01, 'BRON: FTM / OMROEP GELDERLAND / NRC',
         fontsize=9, fontfamily=FONT_MONO, fontweight='bold',
         color=C['zilver'], ha='left', va='bottom',
         transform=fig.transFigure)


# ============================================================
# SAVE
# ============================================================
output_path = 'map_visualization.png'
plt.savefig(output_path, dpi=300, facecolor=C['offwhite'])
print(f"Map saved to: {output_path}")
plt.close()
