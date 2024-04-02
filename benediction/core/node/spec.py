import typing
from dataclasses import dataclass, replace

from benediction.style.style import Style, WindowStyleKwargs


# spec kwargs grouped by context
class StyleKwargs(WindowStyleKwargs):
    """Keys related to Node styling."""

    base_style: typing.NotRequired[Style | typing.Literal["default"]]


class MarginKwargs(typing.TypedDict):
    """Keys related to Node margins."""

    m: typing.NotRequired[int | float | None]
    my: typing.NotRequired[int | float | None]
    mx: typing.NotRequired[int | float | None]
    mt: typing.NotRequired[int | float | None]
    mb: typing.NotRequired[int | float | None]
    ml: typing.NotRequired[int | float | None]
    mr: typing.NotRequired[int | float | None]


class PaddingKwargs(typing.TypedDict):
    """Keys related to Node padding."""

    p: typing.NotRequired[int | float | None]
    py: typing.NotRequired[int | float | None]
    px: typing.NotRequired[int | float | None]
    pt: typing.NotRequired[int | float | None]
    pb: typing.NotRequired[int | float | None]
    pl: typing.NotRequired[int | float | None]
    pr: typing.NotRequired[int | float | None]


# row / column-specific kwargs
class RowKwargs(typing.TypedDict):
    """Keys related to constraints on Row height and spacing."""

    h: typing.NotRequired[int | float | None]
    min_h: typing.NotRequired[int | float | None]
    max_h: typing.NotRequired[int | float | None]
    gap_x: typing.NotRequired[int | float]


class ColumnKwargs(typing.TypedDict):
    """Keys related to constraints on Column width and spacing."""

    w: typing.NotRequired[int | float | None]
    min_w: typing.NotRequired[int | float | None]
    max_w: typing.NotRequired[int | float | None]
    gap_y: typing.NotRequired[int | float]


class BaseNodeSpecKwargs(StyleKwargs, MarginKwargs, PaddingKwargs):
    """Keys related to all Nodes (excluding Column / Row specific keys)."""

    ...


# row / column kwargs (to only show spec kwargs that will apply at initial orientation)
class RowSpecKwargs(BaseNodeSpecKwargs, RowKwargs):
    """Keys related to Row NodeSpecs."""

    ...


class ColumnSpecKwargs(BaseNodeSpecKwargs, ColumnKwargs):
    """Keys related to Column NodeSpecs."""

    ...


# general NodeSpec kwargs (for all NodeSpecs)
class NodeSpecKwargs(BaseNodeSpecKwargs, RowKwargs, ColumnKwargs):
    """Keys related to NodeSpecs."""

    gap: typing.NotRequired[int | float]


@dataclass(slots=True, frozen=True)
class NodeSpec:
    """Attributes related to Node styling and spacing constraints."""

    # style
    base_style: Style | typing.Literal["default", "parent"]  # style to derive from
    style_kwargs: WindowStyleKwargs
    # height
    height: int | float | None
    height_min: int | float | None
    height_max: int | float | None
    # width
    width: int | float | None
    width_min: int | float | None
    width_max: int | float | None
    # gaps
    gap_y: int | float
    gap_x: int | float
    # margins
    margin_top: int | float
    margin_bottom: int | float
    margin_left: int | float
    margin_right: int | float
    # padding
    padding_top: int | float
    padding_bottom: int | float
    padding_left: int | float
    padding_right: int | float

    @property
    def margins(self):
        """Get (top, bottom, left, right) margin parameters."""
        return self.margin_top, self.margin_bottom, self.margin_left, self.margin_right

    @property
    def padding(self):
        """Get (top, bottom, left, right) padding parameters."""
        return self.padding_top, self.padding_bottom, self.padding_left, self.padding_right

    @classmethod
    def from_kwargs(
        cls,
        # height
        h: int | float | None = None,
        min_h: int | float | None = None,
        max_h: int | float | None = None,
        # width
        w: int | float | None = None,
        min_w: int | float | None = None,
        max_w: int | float | None = None,
        # gaps
        gap: int | float | None = None,
        gap_x: int | float | None = None,
        gap_y: int | float | None = None,
        # margins
        m: int | float | None = None,
        my: int | float | None = None,
        mx: int | float | None = None,
        mt: int | float | None = None,
        mb: int | float | None = None,
        ml: int | float | None = None,
        mr: int | float | None = None,
        # padding
        p: int | float | None = None,
        py: int | float | None = None,
        px: int | float | None = None,
        pt: int | float | None = None,
        pb: int | float | None = None,
        pl: int | float | None = None,
        pr: int | float | None = None,
        # style
        base_style: Style | typing.Literal["default", "parent"] = "parent",
        **style_kwargs: typing.Unpack[WindowStyleKwargs],
    ):
        return cls(
            # height
            height=h,
            height_min=min_h,
            height_max=max_h,
            # width
            width=w,
            width_min=min_w,
            width_max=max_w,
            # gaps
            gap_x=_prioritize(gap_x, gap, default=0),
            gap_y=_prioritize(gap_y, gap, default=0),
            # margins with priority given to most specific keyword
            margin_top=_prioritize(mt, my, m, default=0),
            margin_bottom=_prioritize(mb, my, m, default=0),
            margin_left=_prioritize(ml, mx, m, default=0),
            margin_right=_prioritize(mr, mx, m, default=0),
            # padding with priority given to most specific keyword
            padding_top=_prioritize(pt, py, p, default=0),
            padding_bottom=_prioritize(pb, py, p, default=0),
            padding_left=_prioritize(pl, px, p, default=0),
            padding_right=_prioritize(pr, px, p, default=0),
            # style
            base_style=base_style,
            style_kwargs=style_kwargs,
        )

    def update_style(
        self,
        base_style: Style | typing.Literal["default", "parent"] | None = None,
        **style_kwargs: typing.Unpack[WindowStyleKwargs],
    ):
        """Return new NodeSpec with replaced Style options."""
        base_style = self.base_style if base_style is None else base_style
        derived_kwargs = {k: (getattr(self.style_kwargs, k) if v is None else v) for k, v in style_kwargs.items()}
        return replace(self, base_style=base_style, style_kwargs=derived_kwargs)

    def derive_style(self, parent_style: Style | None = None):
        """Derive Style object from NodeSpec."""
        base_style = Style.default if (self.base_style == "default" or parent_style is None) else parent_style
        return base_style.derive(**self.style_kwargs)


def _prioritize(*args, default):
    """Return first not-None arg or the default value."""
    for arg in args:
        if arg is not None:
            return arg
    return default
