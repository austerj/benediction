from __future__ import annotations

import typing
from dataclasses import dataclass, field

from benediction import errors

OverflowBoundary = typing.Literal["inner", "outer"]

# map width / height to shift in position
HorizontalAnchor = typing.Literal["left", "center", "right"]
VerticalAnchor = typing.Literal["top", "middle", "bottom"]
_XANCHOR: dict[HorizontalAnchor, typing.Callable[[int], int]] = {
    "left": lambda width: 0,
    "center": lambda width: (1 - width) // 2,
    "right": lambda width: 1 - width,
}
_YANCHOR: dict[VerticalAnchor, typing.Callable[[int], int]] = {
    "top": lambda height: 0,
    "middle": lambda height: (1 - height) // 2,
    "bottom": lambda height: 1 - height,
}

# match positions to default anchors
HorizontalPosition = typing.Literal["left", "center", "right", "left-outer", "center-outer", "right-outer"]
VerticalPosition = typing.Literal["top", "middle", "bottom", "top-outer", "middle-outer", "bottom-outer"]
_XDEFAULTANCHOR: dict[HorizontalPosition, HorizontalAnchor] = {
    "left": "left",
    "left-outer": "left",
    "center": "center",
    "center-outer": "center",
    "right": "right",
    "right-outer": "right",
}
_YDEFAULTANCHOR: dict[VerticalPosition, VerticalAnchor] = {
    "top": "top",
    "top-outer": "top",
    "middle": "middle",
    "middle-outer": "middle",
    "bottom": "bottom",
    "bottom-outer": "bottom",
}

# match positions to property names
_XTOPROP: dict[HorizontalPosition, str] = {key: key.replace("-", "_") for key in _XDEFAULTANCHOR.keys()}
_YTOPROP: dict[VerticalPosition, str] = {key: key.replace("-", "_") for key in _YDEFAULTANCHOR.keys()}


@dataclass(slots=True, repr=False)
class Frame:
    """A class with assigned static dimensions and methods for positioning within those."""

    # dimensions assigned on on set_dimensions call
    _top: int | None = field(default=None, init=False)
    _left: int | None = field(default=None, init=False)
    _height: int | None = field(default=None, init=False)
    _width: int | None = field(default=None, init=False)
    _padding_top: int = field(default=0, init=False)
    _padding_left: int = field(default=0, init=False)
    _padding_bottom: int = field(default=0, init=False)
    _padding_right: int = field(default=0, init=False)

    def __repr__(self):
        if self.is_ready:
            return f"{self.__class__.__name__}(y={self.top_abs}, x={self.left_abs}, w={self.width_outer}, h={self.height_outer})"
        else:
            return f"{self.__class__.__name__}()"

    def set_dimensions(
        self,
        top: int,
        left: int,
        width: int,
        height: int,
        padding_top: int = 0,
        padding_bottom: int = 0,
        padding_left: int = 0,
        padding_right: int = 0,
    ):
        """Assign static dimensions to Frame."""
        # validate outer dimensions
        if top <= 0:
            raise errors.FrameError(f"Invalid {top=}: must be strictly positive")
        elif left <= 0:
            raise errors.FrameError(f"Invalid {left=}: must be strictly positive")
        elif width <= 0:
            raise errors.FrameError(f"Invalid {width=}: must be strictly positive")
        elif height <= 0:
            raise errors.FrameError(f"Invalid {height=}: must be strictly positive")
        # validate padding
        elif padding_top + padding_bottom >= height:
            raise errors.FrameError(f"Invalid vertical padding: must be greater than height")
        elif padding_left + padding_right >= width:
            raise errors.FrameError(f"Invalid horizontal padding: must be greater than width")
        # set outer dimensional attributes
        self._left = left
        self._top = top
        self._width = width
        self._height = height
        # set padding
        self._padding_left = padding_left
        self._padding_top = padding_top
        self._padding_right = padding_right
        self._padding_bottom = padding_bottom

    @property
    def is_ready(self) -> bool:
        """Flag denoting if dimensions have been assigned."""
        return self._width is not None

    # dimensions
    @property
    def width_outer(self) -> int:
        """Width of outer Frame (ignoring padding)."""
        if self._width is None:
            raise errors.FrameError("Width must be assigned with 'set_dimensions' before being accessed.")
        return self._width

    @property
    def height_outer(self) -> int:
        """Height of outer Frame (ignoring padding)."""
        if self._height is None:
            raise errors.FrameError("Height must be assigned with 'set_dimensions' before being accessed.")
        return self._height

    @property
    def width(self) -> int:
        """Width of inner Frame (with padding)."""
        return self.width_outer - (self._padding_left + self._padding_right)

    @property
    def height(self) -> int:
        """Height of inner Frame (with padding)."""
        return self.height_outer - (self._padding_top + self._padding_bottom)

    # absolute positions
    @property
    def top_abs(self) -> int:
        """Top (y-coordinate, absolute)."""
        if self._top is None:
            raise errors.FrameError("Vertical offset must be set before being accessed.")
        return self._top

    @property
    def middle_abs(self) -> int:
        """Middle (y-coordinate, absolute)."""
        return self.top_abs + (self.height_outer - 1) // 2

    @property
    def bottom_abs(self) -> int:
        """Bottom (y-coordinate, absolute)."""
        return self.top_abs + self.height_outer - 1

    @property
    def left_abs(self) -> int:
        """Left (x-coordinate, absolute)."""
        if self._left is None:
            raise errors.FrameError("Horizontal offset must be set before being accessed.")
        return self._left

    @property
    def center_abs(self) -> int:
        """Center (x-coordinate, absolute)."""
        return self.left_abs + (self.width_outer - 1) // 2

    @property
    def right_abs(self) -> int:
        """Right (x-coordinate, absolute)."""
        return self.left_abs + self.width_outer - 1

    # outer relative positions
    @property
    def top_outer(self) -> int:
        """Top (y-coordinate, relative unpadded)."""
        return 0

    @property
    def middle_outer(self) -> int:
        """Middle (y-coordinate, relative unpadded)."""
        return (self.height_outer - 1) // 2

    @property
    def bottom_outer(self) -> int:
        """Bottom (y-coordinate, relative unpadded)."""
        return self.height_outer - 1

    @property
    def left_outer(self) -> int:
        """Left (x-coordinate, relative unpadded)."""
        return 0

    @property
    def center_outer(self) -> int:
        """Center (x-coordinate, relative unpadded)."""
        return (self.width_outer - 1) // 2

    @property
    def right_outer(self) -> int:
        """Right (x-coordinate, relative unpadded)."""
        return self.width_outer - 1

    # padded relative positions
    @property
    def top(self) -> int:
        """Top (y-coordinate, relative padded)."""
        return self._padding_top

    @property
    def middle(self) -> int:
        """Middle (y-coordinate, relative padded)."""
        return self.top + (self.height - 1) // 2

    @property
    def bottom(self) -> int:
        """Bottom (y-coordinate, relative padded)."""
        return self.top + self.height - 1

    @property
    def left(self) -> int:
        """Left (x-coordinate, relative padded)."""
        return self._padding_left

    @property
    def center(self) -> int:
        """Center (x-coordinate, relative padded)."""
        return self.left + (self.width - 1) // 2

    @property
    def right(self) -> int:
        """Right (x-coordinate, relative padded)."""
        return self.left + self.width - 1

    # utility methods
    @staticmethod
    def _infer_overflow_boundary(*yxs: int | float | HorizontalPosition | VerticalPosition | None) -> OverflowBoundary:
        """Infer overflow boundary from positions."""
        # drop None params
        yxs_ = (xy for xy in yxs if xy is not None)
        return (
            # assume outer boundary if all values are ints or any are explicit outer coordinates
            "outer"
            if (any(isinstance(xy, str) and xy.endswith("outer") for xy in yxs_))
            or all(isinstance(xy, int) for xy in yxs_)
            # else default to inner boundary
            else "inner"
        )

    def y(self, y: int | float | VerticalPosition, y_shift: int = 0, inner: bool = True) -> int:
        """Get vertical coordinate."""
        if isinstance(y, float):
            # interpret float as relative to (inner or outer) dimensions
            t, h = (self.top, self.height) if inner else (self.top_outer, self.height_outer)
            return t + round(y * (h - 1)) + y_shift
        else:
            # otherwise either absolute int or named position
            return (y if isinstance(y, int) else getattr(self, _YTOPROP[y])) + y_shift

    def x(self, x: int | float | HorizontalPosition, x_shift: int = 0, inner: bool = True) -> int:
        """Get horizontal coordinate."""
        if isinstance(x, float):
            # interpret float as relative to (inner or outer) dimensions
            l, w = (self.left, self.width) if inner else (self.left_outer, self.width_outer)
            return l + round(x * (w - 1)) + x_shift
        return (x if isinstance(x, int) else getattr(self, _XTOPROP[x])) + x_shift

    @staticmethod
    def y_anchor(y: int | float | VerticalPosition) -> VerticalAnchor:
        """Get default vertical anchor."""
        return _YDEFAULTANCHOR[y] if isinstance(y, str) else "top"

    @staticmethod
    def x_anchor(x: int | float | HorizontalPosition) -> HorizontalAnchor:
        """Get default horizontal anchor."""
        return _XDEFAULTANCHOR[x] if isinstance(x, str) else "left"

    @staticmethod
    def anchor_y(y: int, height: int, anchor: VerticalAnchor) -> int:
        """Apply a shift based on the chosen anchor to an element at y of a given height."""
        return y + _YANCHOR[anchor](height)

    @staticmethod
    def anchor_x(x: int, width: int, anchor: HorizontalAnchor) -> int:
        """Apply a shift based on the chosen anchor to an element at x of a given width."""
        return x + _XANCHOR[anchor](width)

    def clip_y(self, *ys: int, boundary: OverflowBoundary = "inner") -> tuple[int, ...]:
        """Clip y coordinates to overflow boundary."""
        t, b = (self.top, self.bottom) if boundary == "inner" else (self.top_outer, self.bottom_outer)
        return tuple(t if y < t else b if y > b else y for y in ys)

    def clip_x(self, *xs: int, boundary: OverflowBoundary = "inner") -> tuple[int, ...]:
        """Clip x coordinates to overflow boundary."""
        l, r = (self.left, self.right) if boundary == "inner" else (self.left_outer, self.right_outer)
        return tuple(l if x < l else r if x > r else x for x in xs)

    def y_overflows(self, *ys: int | VerticalPosition, boundary: OverflowBoundary = "inner") -> bool:
        """Test if y coordinates overflow the inner or outer boundary."""
        if boundary == "inner":
            return not all((self.top <= self.y(y) <= self.bottom) for y in ys)
        else:
            return not all((self.top_outer <= self.y(y) <= self.bottom_outer) for y in ys)

    def x_overflows(self, *xs: int | HorizontalPosition, boundary: OverflowBoundary = "inner") -> bool:
        """Test if x coordinates overflow the inner or outer boundary."""
        if boundary == "inner":
            return not all((self.left <= self.x(x) <= self.right) for x in xs)
        else:
            return not all((self.left_outer <= self.x(x) <= self.right_outer) for x in xs)
