# coding: utf-8
"""
BUFF 跨帧跟踪。

同一模板会换行或整体前移，槽位坐标变化但目标没有消失；面板倒计时需要
以“目标”为单位连续推进。业务上每种 BUFF 同一时刻只会出现一次，因此直接
按名称关联，给每个目标分配稳定的 track_id，位置只用于展示和排查。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# 轨迹连续丢失多少帧后才删除，用于跨过闪烁低谷和换位过程中的短暂漏检
TRACK_MAX_MISS_FRAMES = 5


@dataclass
class TrackDetection:
    """一帧内的一次检测结果，由识别业务填充后交给 BuffTracker。"""

    name: str
    center: tuple[float, float]
    rect: tuple[int, int, int, int]
    score: float
    category: str
    attribute: str
    stack: Optional[int] = None
    seconds: Optional[int] = None
    has_countdown: bool = False
    # 由 BuffTracker.update 回填，业务层可直接读取
    track_id: int = -1


@dataclass
class TrackState:
    """跟踪器维护的目标状态，也是返回给面板的活跃轨迹。"""

    track_id: int
    name: str
    category: str
    attribute: str
    center: tuple[float, float]
    rect: tuple[int, int, int, int]
    score: float
    stack: Optional[int]
    seconds: Optional[int]
    has_countdown: bool
    misses: int = 0
    # 本帧是否真正检测到；False 表示仍在丢失容忍期
    detected: bool = True


class BuffTracker:
    """轻量的多目标跟踪器，按名称分配稳定 track_id。"""

    def __init__(self, max_miss_frames: int = TRACK_MAX_MISS_FRAMES) -> None:
        self._max_miss_frames = max(1, int(max_miss_frames))
        self._tracks: dict[str, TrackState] = {}
        self._next_id = 1

    def update(self, detections: list[TrackDetection]) -> list[TrackState]:
        """
        用当前帧检测结果更新轨迹。

        :param detections: 本帧所有检测结果，调用后其 track_id 会被回填
        :return: 本帧活跃轨迹（包含仍在丢失容忍期的轨迹）
        """
        seen_names: set[str] = set()
        for detection in detections:
            # 业务层已经保证每个模板只选一个结果，这里再做一次防御性去重
            if detection.name in seen_names:
                continue
            seen_names.add(detection.name)

            track = self._tracks.get(detection.name)
            if track is None:
                track = TrackState(
                    track_id=self._next_id,
                    name=detection.name,
                    category=detection.category,
                    attribute=detection.attribute,
                    center=detection.center,
                    rect=detection.rect,
                    score=detection.score,
                    stack=detection.stack,
                    seconds=detection.seconds,
                    has_countdown=detection.has_countdown,
                )
                self._next_id += 1
                self._tracks[detection.name] = track
            self._apply_detection(track, detection)

        # 未匹配轨迹累计丢失次数，超过容忍上限后删除
        for name, track in list(self._tracks.items()):
            if name in seen_names:
                continue
            track.misses += 1
            track.detected = False
            if track.misses > self._max_miss_frames:
                del self._tracks[name]

        return sorted(self._tracks.values(), key=lambda item: item.track_id)

    def reset(self) -> None:
        """清空所有轨迹，重新开始监控时调用。"""
        self._tracks.clear()
        self._next_id = 1

    def _apply_detection(self, track: TrackState,
                         detection: TrackDetection) -> None:
        """把本帧检测结果写入已有轨迹，并回填 track_id。"""
        track.name = detection.name
        track.category = detection.category
        track.attribute = detection.attribute
        track.center = detection.center
        track.rect = detection.rect
        track.score = detection.score
        track.stack = detection.stack
        track.seconds = detection.seconds
        track.has_countdown = detection.has_countdown
        track.misses = 0
        track.detected = True
        detection.track_id = track.track_id
