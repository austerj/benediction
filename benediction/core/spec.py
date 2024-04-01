import typing
from dataclasses import dataclass

from benediction.style.style import Style, WindowStyleKwargs


# spec kwargs grouped by context
class StyleKwargs(WindowStyleKwargs):
    """Keys related to Node styling."""

    style: typing.NotRequired[Style | typing.Literal["default"]]


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
class ColumnKwargs(typing.TypedDict):
    """Keys related to constraints on Column height and spacing."""

    h: typing.NotRequired[int | float | None]
    min_h: typing.NotRequired[int | float | None]
    max_h: typing.NotRequired[int | float | None]
    gap_x: typing.NotRequired[int | float]


class RowKwargs(typing.TypedDict):
    """Keys related to constraints on Row width and spacing."""

    w: typing.NotRequired[int | float | None]
    min_w: typing.NotRequired[int | float | None]
    max_w: typing.NotRequired[int | float | None]
    gap_y: typing.NotRequired[int | float]


class BaseNodeSpecKwargs(StyleKwargs, MarginKwargs, PaddingKwargs):
    """Keys related to all Nodes (excluding Column / Row specific keys)."""

    ...


# row / column kwargs (to only show spec kwargs that will apply at initial orientation)
class RowSpecKwargs(BaseNodeSpecKwargs, ColumnKwargs):
    """Keys related to Row NodeSpecs."""

    ...


class ColumnSpecKwargs(BaseNodeSpecKwargs, ColumnKwargs):
    """Keys related to Column NodeSpecs."""

    ...


# general NodeSpec kwargs (for all NodeSpecs)
class NodeSpecKwargs(BaseNodeSpecKwargs, ColumnKwargs, RowKwargs):
    """Keys related to NodeSpecs."""

    gap: typing.NotRequired[int | float]


@dataclass(slots=True, frozen=True)
class NodeSpec:
    """Attributes related to Node styling and spacing constraints."""

    default: typing.ClassVar["NodeSpec"]
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
    # style
    style: Style

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
        style: Style | typing.Literal["default"] = Style.default,
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
            gap_x=gap_x if gap_x is not None else gap if gap is not None else 0,
            gap_y=gap_y if gap_y is not None else gap if gap is not None else 0,
            # margins with priority given to most specific keyword
            margin_top=mt if mt is not None else my if my is not None else m if m is not None else 0,
            margin_bottom=mb if mb is not None else my if my is not None else m if m is not None else 0,
            margin_left=ml if ml is not None else mx if mx is not None else m if m is not None else 0,
            margin_right=mr if mr is not None else mx if mx is not None else m if m is not None else 0,
            # padding with priority given to most specific keyword
            padding_top=pt if pt is not None else py if py is not None else p if p is not None else 0,
            padding_bottom=pb if pb is not None else py if py is not None else p if p is not None else 0,
            padding_left=pl if pl is not None else px if px is not None else p if p is not None else 0,
            padding_right=pr if pr is not None else px if px is not None else p if p is not None else 0,
            # style
            style=(Style.default if style == "default" else style).derive(**style_kwargs),
        )


NodeSpec.default = NodeSpec.from_kwargs()
