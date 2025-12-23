from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon
import rasterio
from rasterio.mask import mask
import numpy as np
from pyproj import Transformer
import os
from datetime import datetime
from work.tools.base_tool import BaseTool

BASE_DIR = Path(__file__).parent.parent.parent
DEM_PATH = BASE_DIR / "data" / "dem.tif"
RESULT_DIR = BASE_DIR / "result"


class SlopeFilterTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="slope_filter_tool",
            description="根据坡度范围筛选GeoJSON区域"
        )
        self.parameters = {
            "input_geojson_path": {"type": "string", "description": "输入GeoJSON文件路径"},
            "min_slope": {"type": "number", "description": "最小坡度（度，0-90，可选）"},
            "max_slope": {"type": "number", "description": "最大坡度（度，0-90，可选）"}
        }
    
    def _get_slope_from_dem(self, geometry: Polygon, min_slope: Optional[float] = None, max_slope: Optional[float] = None) -> Tuple[bool, Optional[float]]:
        try:
            with rasterio.open(str(DEM_PATH)) as src:
                geometry_transformed = geometry
                if src.crs is not None:
                    try:
                        if src.crs.to_epsg() != 4326:
                            transformer = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
                            coords = list(geometry.exterior.coords)
                            transformed_coords = [transformer.transform(x, y) for x, y in coords]
                            geometry_transformed = Polygon(transformed_coords)
                    except Exception:
                        geometry_transformed = geometry
                
                try:
                    out_image, out_transform = mask(src, [geometry_transformed], crop=True, filled=False)
                    elev_data = out_image[0].astype("float64")
                except Exception:
                    elev_data = None
                    out_transform = None
                
                if elev_data is None:
                    bounds = geometry.bounds
                    center = geometry.centroid
                    
                    sample_points_ll = [
                        (center.x, center.y),
                        (bounds[0], bounds[1]),
                        (bounds[2], bounds[1]),
                        (bounds[0], bounds[3]),
                        (bounds[2], bounds[3]),
                    ]
                    
                    sample_points = sample_points_ll
                    if src.crs is not None and src.crs.to_epsg() != 4326:
                        try:
                            transformer = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
                            sample_points = [transformer.transform(x, y) for x, y in sample_points_ll]
                        except Exception:
                            sample_points = sample_points_ll
                    
                    elevations = []
                    for x, y in sample_points:
                        try:
                            for val in src.sample([(x, y)]):
                                v = float(val[0])
                                if src.nodata is not None and v == float(src.nodata):
                                    continue
                                if np.isfinite(v):
                                    elevations.append(v)
                        except Exception:
                            continue
                    
                    if len(elevations) < 2:
                        return True, None
                    
                    elev_diff = max(elevations) - min(elevations)
                    
                    if src.crs is not None and getattr(src.crs, "is_geographic", False):
                        lat = center.y
                        lon_diff = abs(bounds[2] - bounds[0])
                        lat_diff = abs(bounds[3] - bounds[1])
                        lon_m = lon_diff * 111320.0 * np.cos(np.radians(lat))
                        lat_m = lat_diff * 111320.0
                        dist_m = float(np.sqrt(lon_m * lon_m + lat_m * lat_m))
                    else:
                        b = geometry_transformed.bounds
                        dist_m = float(np.sqrt((b[2] - b[0]) ** 2 + (b[3] - b[1]) ** 2))
                    
                    if dist_m < 1.0:
                        return True, None
                    
                    slope_deg = float(np.degrees(np.arctan(elev_diff / dist_m)))
                    avg_slope = slope_deg
                    
                    if min_slope is not None and avg_slope < min_slope:
                        return False, avg_slope
                    if max_slope is not None and avg_slope >= max_slope:
                        return False, avg_slope
                    return True, avg_slope
                
                if np.ma.isMaskedArray(elev_data):
                    elev_data = elev_data.filled(np.nan)
                
                if src.nodata is not None:
                    elev_data[elev_data == float(src.nodata)] = np.nan
                
                if elev_data.size == 0 or np.all(np.isnan(elev_data)):
                    return True, None
                
                pixel_x = abs(out_transform.a)
                pixel_y = abs(out_transform.e)
                
                if src.crs is not None and getattr(src.crs, "is_geographic", False):
                    center_lat = geometry.centroid.y
                    pixel_x_m = pixel_x * 111320.0 * np.cos(np.radians(center_lat))
                    pixel_y_m = pixel_y * 111320.0
                else:
                    pixel_x_m = pixel_x
                    pixel_y_m = pixel_y
                
                if pixel_x_m <= 0 or pixel_y_m <= 0:
                    return True, None
                
                dy, dx = np.gradient(elev_data, pixel_y_m, pixel_x_m)
                
                slope_rad = np.arctan(np.sqrt(dx * dx + dy * dy))
                slope_deg = np.degrees(slope_rad)
                
                if np.all(np.isnan(slope_deg)):
                    return True, None
                
                valid = np.isfinite(slope_deg) & (slope_deg >= 0.0) & (slope_deg <= 90.0)
                if not np.any(valid):
                    return True, None
                
                avg_slope = float(np.mean(slope_deg[valid]))
                
                if min_slope is not None and avg_slope < min_slope:
                    return False, avg_slope
                if max_slope is not None and avg_slope >= max_slope:
                    return False, avg_slope
                
                return True, avg_slope
                
        except Exception as e:
            return True, None
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        input_path = kwargs.get("input_geojson_path")
        min_slope = kwargs.get("min_slope")
        max_slope = kwargs.get("max_slope")
        
        os.makedirs(RESULT_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slope_range = f"_{min_slope if min_slope else 'min'}_{max_slope if max_slope else 'max'}"
        output_path = RESULT_DIR / f"slope_filter{slope_range}_{timestamp}.geojson"
        
        if not input_path or (min_slope is None and max_slope is None):
            gdf = gpd.read_file(input_path) if input_path else gpd.GeoDataFrame()
            if not gdf.empty:
                gdf.to_file(output_path, driver='GeoJSON')
            return {
                "success": True,
                "result_path": str(output_path),
                "region_count": len(gdf),
                "total_area_m2": float(gdf['area_m2'].sum()) if not gdf.empty and 'area_m2' in gdf.columns else 0.0
            }
        
        gdf = gpd.read_file(input_path)
        
        if gdf.empty:
            return {
                "success": True,
                "result_path": str(output_path),
                "region_count": 0,
                "total_area_m2": 0.0
            }
        
        valid_indices = []
        slopes = []
        
        for idx, row in gdf.iterrows():
            is_valid, slope = self._get_slope_from_dem(row.geometry, min_slope, max_slope)
            if is_valid:
                valid_indices.append(idx)
                slopes.append(slope)
            else:
                slopes.append(None)
        
        filtered_gdf = gdf.loc[valid_indices].copy()
        
        if slopes:
            slope_series = pd.Series(slopes, index=gdf.index)
            filtered_gdf["slope_deg"] = slope_series.loc[valid_indices].values
        
        filtered_gdf.to_file(output_path, driver='GeoJSON')
        
        return {
            "success": True,
            "result_path": str(output_path),
            "region_count": len(filtered_gdf),
            "total_area_m2": float(filtered_gdf['area_m2'].sum()) if not filtered_gdf.empty and 'area_m2' in filtered_gdf.columns else 0.0
        }
    
    def validate_params(self, **kwargs) -> bool:
        return kwargs.get("input_geojson_path") is not None