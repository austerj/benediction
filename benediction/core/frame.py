from __future__ import annotations

import typing
from dataclasses import dataclass, field

from benediction import errors

if typing.TYPE_CHECKING:
    from benediction.core.node.spec import NodeSpec

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
    """Representation of a fixed region of space with associated methods for positioning."""

    # attributes assigned on set_dimensions call
    __top: int | None = field(default=None, init=False)
    __left: int | None = field(default=None, init=False)
    __height: int | None = field(default=None, init=False)
    __width: int | None = field(default=None, init=False)
    __padding_top: int = field(default=0, init=False)
    __padding_bottom: int = field(default=0, init=False)
    __padding_left: int = field(default=0, init=False)
    __padding_right: int = field(default=0, init=False)

    def __repr__(self):
        if self.is_ready:
            return f"{self.__class__.__name__}(y={self.top_abs}, x={self.left_abs}, w={self.width_outer}, h={self.height_outer})"
        else:
            return f"{self.__class__.__name__}()"

    def set_dimensions(
        self,
        top: int,
        left: int,
        height: int,
        width: int,
        padding_top: int = 0,
        padding_bottom: int = 0,
        padding_left: int = 0,
        padding_right: int = 0,
    ):
        """Assign static dimensions."""
        # validate outer dimensions
        if top < 0:
            raise errors.FrameError(f"Invalid {top=}: must be positive")
        elif left < 0:
            raise errors.FrameError(f"Invalid {left=}: must be positive")
        elif height <= 0:
            raise errors.FrameError(f"Invalid {height=}: must be strictly positive")
        elif width <= 0:
            raise errors.FrameError(f"Invalid {width=}: must be strictly positive")
        # validate padding
        elif padding_top + padding_bottom >= height:
            raise errors.FrameError(f"Invalid vertical padding: must be strictly less than height")
        elif padding_left + padding_right >= width:
            raise errors.FrameError(f"Invalid horizontal padding: must be strictly less than width")
        # set outer dimensional attributes
        self.__top = top
        self.__left = left
        self.__height = height
        self.__width = width
        # set padding
        self.__padding_top = padding_top
        self.__padding_bottom = padding_bottom
        self.__padding_left = padding_left
        self.__padding_right = padding_right

    @property
    def is_ready(self) -> bool:
        """Flag denoting if dimensions have been assigned."""
        return self.__width is not None

    # dimensions
    @property
    def height_outer(self) -> int:
        """Height of outer region (ignoring padding)."""
        if self.__height is None:
            raise errors.FrameError("Height must be assigned with 'set_dimensions' before being accessed.")
        return self.__height

    @property
    def width_outer(self) -> int:
        """Width of outer region (ignoring padding)."""
        if self.__width is None:
            raise errors.FrameError("Width must be assigned with 'set_dimensions' before being accessed.")
        return self.__width

    @property
    def height(self) -> int:
        """Height of inner region (with padding)."""
        return self.height_outer - (self.__padding_top + self.__padding_bottom)

    @property
    def width(self) -> int:
        """Width of inner region (with padding)."""
        return self.width_outer - (self.__padding_left + self.__padding_right)

    # absolute positions
    @property
    def top_abs(self) -> int:
        """Top (y-coordinate, absolute)."""
        if self.__top is None:
            raise errors.FrameError("Vertical offset must be set before being accessed.")
        return self.__top

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
        if self.__left is None:
            raise errors.FrameError("Horizontal offset must be set before being accessed.")
        return self.__left

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
        return self.__padding_top

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
        return self.__padding_left

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


@dataclass(frozen=True, slots=True, repr=False)
class ConstrainedFrame:
    """Container object holding a Frame along with constraints and relevant methods."""

    # inner frame
    frame: Frame = field(default_factory=Frame, init=False)
    # height / width
    height: int | float | None = field(default=None, kw_only=True)
    height_min: int | float | None = field(default=None, kw_only=True)
    height_max: int | float | None = field(default=None, kw_only=True)
    width: int | float | None = field(default=None, kw_only=True)
    width_min: int | float | None = field(default=None, kw_only=True)
    width_max: int | float | None = field(default=None, kw_only=True)
    # margins
    margin_top: int | float = field(default=0, kw_only=True)
    margin_bottom: int | float = field(default=0, kw_only=True)
    margin_left: int | float = field(default=0, kw_only=True)
    margin_right: int | float = field(default=0, kw_only=True)
    # padding
    padding_top: int | float = field(default=0, kw_only=True)
    padding_bottom: int | float = field(default=0, kw_only=True)
    padding_left: int | float = field(default=0, kw_only=True)
    padding_right: int | float = field(default=0, kw_only=True)

    def __post_init__(self):
        for attr in ("width", "height"):
            x: int | float | None
            x_min: int | float | None
            x_max: int | float | None
            x, x_min, x_max = (getattr(self, a) for a in [attr, f"{attr}_min", f"{attr}_max"])
            # validate non-negativity
            if x is not None and x <= 0:
                raise errors.FrameConstraintError(f"Cannot use non-strictly positive {attr}.")
            if (x_min is not None and x_min <= 0) or (x_max is not None and x_max <= 0):
                raise errors.FrameConstraintError(f"Cannot use non-strictly positive bounds.")
            # validate bound types
            if isinstance(x, int) and not (x_min is None and x_max is None):
                raise errors.FrameConstraintError(f"Cannot use bounds with absolute (integer) {attr}.")
            elif isinstance(x, float) and (isinstance(x_min, float) or isinstance(x_max, float)):
                raise errors.FrameConstraintError(f"Cannot use relative bounds with relative (float) {attr}.")
            # validate consistency of bounds
            if (isinstance(x_min, float) and x_min > 1) or (isinstance(x_max, float) and x_max > 1):
                raise errors.FrameConstraintError(f"Relative bounds must be strictly between 0 and 1.")
            elif x_min is not None and x_max is not None and type(x_max) == type(x_max) and x_min >= x_max:
                raise errors.FrameConstraintError(f"Lower bound must be strictly less than upper bound.")

    def __repr__(self):
        attrs = [
            f"{alias}={f'{100 * value:.0f}%' if isinstance(value, float) else value}"
            for alias, attr in [
                # height / width
                ("h", "height"),
                ("min_h", "height_min"),
                ("max_h", "height_max"),
                ("w", "width"),
                ("min_w", "width_min"),
                ("max_w", "width_max"),
                # margins
                ("mt", "margin_top"),
                ("mb", "margin_bottom"),
                ("ml", "margin_left"),
                ("mr", "margin_right"),
                # padding
                ("pt", "padding_top"),
                ("pb", "padding_bottom"),
                ("pl", "padding_left"),
                ("pr", "padding_right"),
            ]
            if ((value := getattr(self, attr)) is not None and value != 0)
        ]
        return f"{self.__class__.__name__}({', '.join(attrs)})"

    @typing.overload
    @staticmethod
    def abs(units: int | float, outer_space: int) -> int:
        ...

    @typing.overload
    @staticmethod
    def abs(units: None, outer_space: int) -> None:
        ...

    @staticmethod
    def abs(units: int | float | None, outer_space: int):
        """Interpret as absolute units if integer, otherwise as rounded-down ratio of space."""
        return int(units * outer_space) if isinstance(units, float) else units

    def height_bounds(self, outer_height: int) -> tuple[int | None, int | None]:
        """Get height bounds for outer height."""
        return self.abs(self.height_min, outer_height), self.abs(self.height_max, outer_height)

    def width_bounds(self, outer_width: int) -> tuple[int | None, int | None]:
        """Get width bounds for outer width."""
        return self.abs(self.width_min, outer_width), self.abs(self.width_max, outer_width)

    def margins(self, outer_height: int, outer_width: int):
        """Get (top, bottom, left, right)-margins for outer height and width."""
        return (
            self.abs(self.margin_top, outer_height),
            self.abs(self.margin_bottom, outer_height),
            self.abs(self.margin_left, outer_width),
            self.abs(self.margin_right, outer_width),
        )

    def dimensions(self, top: int, left: int, height: int, width: int, outer_height: int, outer_width: int):
        """Get post-margined (top, left, height, width)-dimensions for outer height and width."""
        mt, mb, ml, mr = self.margins(outer_height, outer_width)
        return top + mt, left + ml, height - (mt + mb), width - (ml + mr)

    def padding(self, outer_height: int, outer_width: int):
        """Get (top, bottom, left, right)-padding for outer height and width."""
        return (
            self.abs(self.padding_top, outer_height),
            self.abs(self.padding_bottom, outer_height),
            self.abs(self.padding_left, outer_width),
            self.abs(self.padding_right, outer_width),
        )

    def set_dimensions(
        self,
        top: int,
        left: int,
        height: int,
        width: int,
        outer_height: int,
        outer_width: int,
    ):
        """Assign dimensions to inner Frame."""
        if not self.height is None and height != self.abs(self.height, outer_height):
            cons = "absolute" if isinstance(self.height, int) else "relative"
            raise errors.FrameConstraintError(f"Height violates exact ({cons}) height constraint.")
        if not self.width is None and width != self.abs(self.width, outer_width):
            cons = "absolute" if isinstance(self.height, int) else "relative"
            raise errors.FrameConstraintError(f"Width violates exact ({cons}) width constraint.")
        # validate against min/max constraints
        h_min, h_max = self.height_bounds(outer_height)
        w_min, w_max = self.width_bounds(outer_width)
        if h_min is not None and height < h_min:
            raise errors.FrameConstraintError("Height violates lower bound.")
        if h_max is not None and height > h_max:
            raise errors.FrameConstraintError("Height violates upper bound.")
        if w_min is not None and width < w_min:
            raise errors.FrameConstraintError("Width violates lower bound.")
        if w_max is not None and width > w_max:
            raise errors.FrameConstraintError("Width violates upper bound.")
        # let Frame validate dimensions
        self.frame.set_dimensions(
            *self.dimensions(top, left, height, width, outer_height, outer_width),
            *self.padding(outer_height, outer_width),
        )
        return self

    @classmethod
    def from_spec(cls, spec: NodeSpec):
        return cls(
            # height / width
            height=spec.height,
            height_min=spec.height_min,
            height_max=spec.height_max,
            width=spec.width,
            width_min=spec.width_min,
            width_max=spec.width_max,
            # margins
            margin_top=spec.margin_top,
            margin_bottom=spec.margin_bottom,
            margin_left=spec.margin_left,
            margin_right=spec.margin_right,
            # padding
            padding_top=spec.padding_top,
            padding_bottom=spec.padding_bottom,
            padding_left=spec.padding_left,
            padding_right=spec.padding_right,
        )
