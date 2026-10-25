# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('./Resources/.', './Resources/.'),('./README.MD', './')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 打包裁剪：移除运行时不需要的文件，减小产物体积。
# 这些资源/库均未被代码引用，删除后不影响现有功能。
_EXCLUDE_KEYWORDS = (
    'opencv_videoio_ffmpeg',              # cv2 视频读写，项目只做图像模板匹配
    'resources/readme',                   # 仅说明文档图片，程序不读取
    'resources/imagetemplate/picmoxi',    # 旧漠西风涛背景图，代码未引用
    'qt6qml', 'qt6quick', 'qmltooling',   # 未使用 QML/Quick
    'qt6pdf', 'qt6opengl',                # 未使用的 Qt 模块
    'opengl32sw',                         # 软件 OpenGL 后备，QWidget 不需要
    'pyside6/translations',               # Qt 翻译文件，界面无多语言
    'plugins/tls',                        # 未使用 TLS
    'qdirect2d',                          # 未使用 Direct2D 平台插件
)


def _keep_item(item):
    """按目标路径过滤 PyInstaller 收集的二进制和资源文件。"""
    path = item[0].replace('\\', '/').lower()
    return not any(keyword in path for keyword in _EXCLUDE_KEYWORDS)


a.binaries = [item for item in a.binaries if _keep_item(item)]
a.datas = [item for item in a.datas if _keep_item(item)]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='JiuDancing',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='JiuDancing',
    icon='./Resources/logo/app_logo.ico',
)
