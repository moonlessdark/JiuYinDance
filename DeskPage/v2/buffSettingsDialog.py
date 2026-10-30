# coding: utf-8
"""
BUFF 识别设置对话框。

功能与原 BUFF 调试工具一致：
1. 调整状态面板的大图标尺寸、布局模式、属性名显示和背景透明度；
2. 按“内功 / 武学”勾选需要参与识别的模板组；
3. 设置修改时实时预览面板效果；
4. 点击确定后由菜单层写回 buff_config.json。

模板勾选在下次开始 BUFF 监控时生效；面板外观会立即应用到当前面板。
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog,
                               QDialogButtonBox, QFormLayout, QGroupBox,
                               QHBoxLayout, QLabel, QScrollArea, QSpinBox,
                               QVBoxLayout, QWidget)

from DeskFunc.v2.TaskBussinese.buffConfig import (
    TEMPLATE_CATEGORIES,
    enabled_template_map,
    is_template_enabled,
)
from DeskPage.v2.buffPanel import (BuffState, ICON_SIZE_MAX, ICON_SIZE_MIN,
                                   PanelSettings, bgr_to_qimage,
                                   load_show_icons, render_state_panel)

# 设置预览使用的示例数据，覆盖内功/武学、叠层/增伤和倒计时进度条
_PREVIEW_STATES = [
    BuffState("花开", "内功", "叠层", stack=4, seconds=30,
              has_countdown=True),
    BuffState("花开有时", "内功", "增伤", stack=1),
    BuffState("仓海", "武学", "叠层", stack=3, seconds=12,
              has_countdown=True),
    BuffState("云天", "武学", "增伤", stack=1, seconds=8,
              has_countdown=True),
]
_PREVIEW_MAX_SECONDS = {"花开": 30, "仓海": 15, "云天": 10}


class BuffSettingsDialog(QDialog):
    """BUFF 面板设置对话框：外观 + 模板选择 + 实时预览。"""

    def __init__(self, settings: PanelSettings, config: Optional[dict] = None,
                 showbuff_dir: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("BUFF 识别设置")
        self.resize(430, 560)
        self._config = config or {}
        self._template_checks: dict[tuple[str, str], QCheckBox] = {}
        self._icons = load_show_icons(showbuff_dir) if showbuff_dir else {}

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        form = QFormLayout()
        form.setHorizontalSpacing(8)
        form.setVerticalSpacing(4)
        form.setContentsMargins(0, 0, 0, 0)

        self._size_spin = QSpinBox(self)
        self._size_spin.setRange(ICON_SIZE_MIN, ICON_SIZE_MAX)
        self._size_spin.setSuffix(" px")
        self._size_spin.setValue(settings.icon_size)
        form.addRow("图标尺寸：", self._size_spin)

        self._layout_combo = QComboBox(self)
        self._layout_combo.addItem("2 行 N 列", "rows")
        self._layout_combo.addItem("N 行 1 列", "column")
        index = self._layout_combo.findData(settings.layout_mode)
        self._layout_combo.setCurrentIndex(max(0, index))
        form.addRow("图标布局：", self._layout_combo)

        form_2 = QFormLayout()
        form_2.setHorizontalSpacing(8)
        form_2.setVerticalSpacing(4)
        form_2.setContentsMargins(0, 0, 0, 0)

        self._show_attr_check = QCheckBox(
            "显示大图标类型", self)
        self._show_attr_check.setChecked(settings.show_attr_label)
        form_2.addRow("图标类型：", self._show_attr_check)

        self._alpha_spin = QSpinBox(self)
        self._alpha_spin.setRange(0, 100)
        self._alpha_spin.setSuffix(" %")
        self._alpha_spin.setValue(
            max(0, min(100, int(round(settings.background_alpha / 255 * 100)))))
        form_2.addRow("背景明度：", self._alpha_spin)

        # 重点！两个form都放进同一个水平布局 row_1
        row_1 = QHBoxLayout()
        row_1.addLayout(form, stretch=1)
        row_1.addLayout(form_2, stretch=1)

        root.addLayout(row_1)

        root.addWidget(self._build_template_selector())

        preview_box = QGroupBox("效果预览", self)
        preview_layout = QVBoxLayout(preview_box)
        preview_layout.setContentsMargins(4, 4, 4, 4)
        preview_layout.setSpacing(2)
        self._preview_scroll = QScrollArea(preview_box)
        self._preview_scroll.setWidgetResizable(False)
        self._preview_scroll.setStyleSheet("background: #0d1117;")
        self._preview_label = QLabel(self._preview_scroll)
        self._preview_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self._preview_scroll.setWidget(self._preview_label)
        preview_layout.addWidget(self._preview_scroll)
        root.addWidget(preview_box, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self._size_spin.valueChanged.connect(self._update_preview)
        self._layout_combo.currentIndexChanged.connect(self._update_preview)
        self._show_attr_check.toggled.connect(self._update_preview)
        self._alpha_spin.valueChanged.connect(self._update_preview)
        self._update_preview()

    def _build_template_selector(self) -> QGroupBox:
        """构建“内功选择 / 武学选择”两组复选框。"""
        selection_box = QGroupBox("识别模板选择", self)
        selection_layout = QHBoxLayout(selection_box)
        selection_layout.setContentsMargins(4, 4, 4, 4)
        selection_layout.setSpacing(6)

        enabled_map = enabled_template_map(self._config)
        buffs = self._config.get("buffs", {})
        if not isinstance(buffs, dict):
            buffs = {}

        for category in TEMPLATE_CATEGORIES:
            group = QGroupBox(f"{category}选择", selection_box)
            group_layout = QVBoxLayout(group)
            group_layout.setContentsMargins(4, 4, 4, 4)
            group_layout.setSpacing(2)

            scroll = QScrollArea(group)
            scroll.setWidgetResizable(True)
            scroll.setFixedHeight(100)
            content = QWidget(scroll)
            content_layout = QVBoxLayout(content)
            content_layout.setContentsMargins(2, 2, 2, 2)
            content_layout.setSpacing(1)

            templates = buffs.get(category, {})
            if not isinstance(templates, dict):
                templates = {}
            if templates:
                for template_name in templates:
                    check = QCheckBox(str(template_name), content)
                    check.setChecked(is_template_enabled(
                        enabled_map, category, str(template_name)))
                    content_layout.addWidget(check)
                    self._template_checks[(category, str(template_name))] = check
            else:
                content_layout.addWidget(QLabel("无可用模板", content))
            content_layout.addStretch(1)

            scroll.setWidget(content)
            group_layout.addWidget(scroll)
            selection_layout.addWidget(group, 1)
        return selection_box

    def enabled_templates(self) -> dict[str, list[str]]:
        """读取勾选的模板，按模版类型分组返回。"""
        result: dict[str, list[str]] = {
            category: [] for category in TEMPLATE_CATEGORIES}
        for (category, template_name), check in self._template_checks.items():
            if check.isChecked():
                result.setdefault(category, []).append(template_name)
        return result

    def panel_settings(self) -> PanelSettings:
        """读取对话框中当前选择的设置。"""
        return PanelSettings(
            icon_size=self._size_spin.value(),
            layout_mode=self._layout_combo.currentData(),
            show_attr_label=self._show_attr_check.isChecked(),
            background_alpha=max(
                0, min(255, int(round(self._alpha_spin.value() * 255 / 100)))),
        )

    def _update_preview(self) -> None:
        """按当前设置渲染示例面板并显示在预览区。"""
        if not self._icons:
            self._preview_label.setText("未找到 ShowBuff 大图标")
            self._preview_label.adjustSize()
            return
        pixel_ratio = max(1.0, self.devicePixelRatioF())
        image = render_state_panel(
            _PREVIEW_STATES, self._icons, _PREVIEW_MAX_SECONDS, "效果预览",
            self.panel_settings(), pixel_ratio=pixel_ratio)
        pixmap = QPixmap.fromImage(bgr_to_qimage(image))
        pixmap.setDevicePixelRatio(pixel_ratio)
        self._preview_label.setPixmap(pixmap)
        self._preview_label.setFixedSize(
            max(1, int(round(pixmap.width() / pixel_ratio))),
            max(1, int(round(pixmap.height() / pixel_ratio))))
