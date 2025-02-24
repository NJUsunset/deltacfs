import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 读取数据文件
file_path = './output/coseis-gps.dat'
columns = ['Lat', 'Lon', 'Ux', 'Uy', 'Uz', 'Sxx', 'Syy', 'Szz', 'Sxy', 'Syz', 'Szx', 'Tx', 'Ty', 'Rot', 'Gd', 'Gr']
data = pd.read_csv(file_path, sep=r'\s', skiprows=1, names=columns)

# 提取必要数据
lat = data['Lat']
lon = data['Lon']
ux = data['Ux']
uy = data['Uy']
uz = data['Uz']
sxx = data['Sxx']
syy = data['Syy']
szz = data['Szz']

# 计算应力第一不变量 (I1 = Sxx + Syy + Szz)
stress_invariant = sxx + syy + szz


# 绘制位移分布
plt.figure(figsize=(10, 8))
plt.quiver(lon, lat, ux, uy, np.sqrt(ux**2 + uy**2), cmap='viridis', scale=10, width=0.01)
plt.colorbar(label='Horizontal Displacement Magnitude')
plt.title('horizontal displacement field')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.grid(True)

# 显示图形
plt.tight_layout()
plt.savefig('./figure/hor_displace.png', dpi=300)

# 绘制应力第一不变量分布
plt.figure(figsize=(10, 8))
sc = plt.scatter(lon, lat, c=stress_invariant, cmap='plasma', s=40, edgecolor='k')
plt.colorbar(sc, label='Stress First Invariant (I1)')
plt.title('I1 distribution')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.grid(True)

# 显示图形
plt.tight_layout()
plt.savefig('./figure/I1.png', dpi=300)
