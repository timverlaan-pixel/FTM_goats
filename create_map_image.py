"""
Create a static PNG map using geopandas and matplotlib
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from shapely.geometry import Polygon, Point
import geopandas as gpd
import contextily as cx

# FTM Color Palette
C = {
    'blauw': '#0067AF',
    'roze': '#B0279C',
    'geel': '#D4A535',
    'rood': '#FF5725',
    'zwart': '#000000',
    'dollargroen': '#706F5F',
    'offwhite': '#F5F1ED',
    'zilver': '#A19B89'
}

# Goat farm location
GOAT_FARM = Point(6.1801997, 52.2742744)

# Define all polygons (lon, lat format for shapely)
polygons = {
    '400 woningen': {
        'coords': [(6.1672178, 52.2786201), (6.1673895, 52.2777274), (6.1659732, 52.2772547),
                   (6.1676469, 52.2754692), (6.1698142, 52.2752329), (6.1693636, 52.2743795),
                   (6.1722818, 52.2743926), (6.173462, 52.2776617), (6.1702219, 52.2783313),
                   (6.1672178, 52.2786201)],
        'color': C['blauw'],
        'label': 'Reeds gebouwd (400)'
    },
    '800 woningen': {
        'coords': [(6.173462, 52.2776617), (6.1763947, 52.277302), (6.1776822, 52.2797701),
                   (6.1705368, 52.2807153), (6.1703222, 52.2801509), (6.1678117, 52.2804397),
                   (6.1671679, 52.2787068), (6.1701505, 52.2784442), (6.173462, 52.2776617)],
        'color': C['roze'],
        'label': 'Wordt nu gebouwd (800)'
    },
    '1600 woningen': {
        'coords': [(6.17936, 52.2762582), (6.1783729, 52.2739343), (6.1967192, 52.2736454),
                   (6.1963759, 52.2754442), (6.1973415, 52.276954), (6.1911402, 52.2777417),
                   (6.1872993, 52.2771115), (6.183158, 52.2762582), (6.17936, 52.2762582)],
        'color': C['geel'],
        'label': 'Nog te bouwen (1.640)'
    },
    '40 woningen': {
        'coords': [(6.1865383, 52.2710481), (6.1868674, 52.2699887), (6.1879484, 52.269978),
                   (6.1883829, 52.2704245), (6.1883922, 52.2711852), (6.1865383, 52.2710481)],
        'color': C['geel'],
        'label': None  # Same as 1600, don't add to legend twice
    }
}

# Other farm locations
varkens = Point(6.1886441, 52.2772935)
koeien = Point(6.192552, 52.2759297)

# Create GeoDataFrame for polygons
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

# Create figure
fig, ax = plt.subplots(figsize=(16, 12), facecolor=C['offwhite'])
ax.set_facecolor(C['offwhite'])

# Convert to Web Mercator for contextily
gdf_polygons_mercator = gdf_polygons.to_crs(epsg=3857)

# Plot polygons
for idx, row in gdf_polygons_mercator.iterrows():
    ax.add_patch(mpatches.Polygon(
        list(row['geometry'].exterior.coords),
        facecolor=row['color'],
        edgecolor=row['color'],
        alpha=0.25,
        linewidth=3,
        zorder=3
    ))

# Convert points to Web Mercator
goat_gdf = gpd.GeoDataFrame([{'geometry': GOAT_FARM}], crs='EPSG:4326').to_crs(epsg=3857)
varkens_gdf = gpd.GeoDataFrame([{'geometry': varkens}], crs='EPSG:4326').to_crs(epsg=3857)
koeien_gdf = gpd.GeoDataFrame([{'geometry': koeien}], crs='EPSG:4326').to_crs(epsg=3857)

# Plot farm markers
goat_gdf.plot(ax=ax, color=C['rood'], markersize=300, zorder=5, edgecolor='white', linewidth=2)
varkens_gdf.plot(ax=ax, color=C['dollargroen'], markersize=200, zorder=5, edgecolor='white', linewidth=2)
koeien_gdf.plot(ax=ax, color=C['dollargroen'], markersize=200, zorder=5, edgecolor='white', linewidth=2)

# Draw 1km radius circle
goat_point = goat_gdf.geometry.iloc[0]
circle = goat_point.buffer(1000)  # 1000 meters in Web Mercator
circle_x, circle_y = circle.exterior.xy
ax.plot(circle_x, circle_y, color=C['rood'], linewidth=2.5, linestyle='--',
        dashes=(12, 8), alpha=0.8, zorder=4)
ax.fill(circle_x, circle_y, color=C['rood'], alpha=0.04, zorder=2)

# Add basemap
cx.add_basemap(ax, crs=gdf_polygons_mercator.crs, source=cx.providers.CartoDB.Positron, zoom=14)

# Set bounds
bounds = gdf_polygons_mercator.total_bounds
margin = 500  # meters
ax.set_xlim(bounds[0] - margin, bounds[2] + margin)
ax.set_ylim(bounds[1] - margin, bounds[3] + margin)

# Remove axes
ax.set_xticks([])
ax.set_yticks([])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)

# Add title
fig.text(0.02, 0.98, 'FOLLOW THE MONEY', fontsize=10, fontweight='bold',
         color=C['zilver'], ha='left', va='top', family='monospace',
         transform=fig.transFigure)
fig.text(0.02, 0.95, 'Woningen en geiten in Deventer', fontsize=24, fontweight='bold',
         color=C['zwart'], ha='left', va='top', family='sans-serif',
         transform=fig.transFigure)
fig.text(0.02, 0.925, 'Binnen 1 kilometer van deze geitenhouderij zijn al 400 woningen gebouwd.\n' +
         'Als drie andere bouwplannen doorgaan, komen daar nog 2.440 woningen bij.',
         fontsize=11, color=C['zilver'], ha='left', va='top', family='sans-serif',
         transform=fig.transFigure)

# Add legend
legend_elements = [
    mpatches.Patch(facecolor=C['blauw'], edgecolor=C['blauw'], alpha=0.4, label='Reeds gebouwd (400)'),
    mpatches.Patch(facecolor=C['roze'], edgecolor=C['roze'], alpha=0.4, label='Wordt nu gebouwd (800)'),
    mpatches.Patch(facecolor=C['geel'], edgecolor=C['geel'], alpha=0.4, label='Nog te bouwen (1.640)'),
    plt.Line2D([0], [0], color=C['rood'], linewidth=2, linestyle='--', label='1 km risicozone'),
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=C['rood'],
               markersize=10, label='Geitenhouderij', markeredgecolor='white', markeredgewidth=1),
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=C['dollargroen'],
               markersize=10, label='Overige veehouderij', markeredgecolor='white', markeredgewidth=1)
]

legend = ax.legend(handles=legend_elements, loc='lower left', frameon=True,
                  fancybox=False, shadow=True, fontsize=10,
                  title='LEGENDA', title_fontsize=11)
legend.get_frame().set_facecolor('white')
legend.get_frame().set_edgecolor('none')

plt.tight_layout()

# Save
output_path = 'map_visualization.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=C['offwhite'])
print(f"Map saved to: {output_path}")

plt.close()
