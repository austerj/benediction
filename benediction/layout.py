from __future__ import annotations

import typing
from abc import ABC, abstractmethod, abstractproperty
from dataclasses import dataclass, field

from benediction import errors
from benediction._utils.solver import SpaceAllocator
from benediction.style import Style, WindowStyleKwargs
from benediction.window import AbstractWindow, ScreenWindow

T = typing.TypeVar("T")


class LayoutKwargs(WindowStyleKwargs):
    style: typing.NotRequired[Style | typing.Literal["default"]]
    # margins
    m: typing.NotRequired[int | float | None]
    my: typing.NotRequired[int | float | None]
    mx: typing.NotRequired[int | float | None]
    mt: typing.NotRequired[int | float | None]
    mb: typing.NotRequired[int | float | None]
    ml: typing.NotRequired[int | float | None]
    mr: typing.NotRequired[int | float | None]
    # padding
    p: typing.NotRequired[int | float | None]
    py: typing.NotRequired[int | float | None]
    px: typing.NotRequired[int | float | None]
    pt: typing.NotRequired[int | float | None]
    pb: typing.NotRequired[int | float | None]
    pl: typing.NotRequired[int | float | None]
    pr: typing.NotRequired[int | float | None]


def _map_kwargs(
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
) -> dict[str, typing.Any]:
    return {
        # margins with priority given to most specific keyword
        "_margin_top": mt if mt is not None else my if my is not None else m if m is not None else 0,
        "_margin_bottom": mb if mb is not None else my if my is not None else m if m is not None else 0,
        "_margin_left": ml if ml is not None else mx if mx is not None else m if m is not None else 0,
        "_margin_right": mr if mr is not None else mx if mx is not None else m if m is not None else 0,
        # padding with priority given to most specific keyword
        "_padding_top": pt if pt is not None else py if py is not None else p if p is not None else 0,
        "_padding_bottom": pb if pb is not None else py if py is not None else p if p is not None else 0,
        "_padding_left": pl if pl is not None else px if px is not None else p if p is not None else 0,
        "_padding_right": pr if pr is not None else px if px is not None else p if p is not None else 0,
        # style
        "_style": (Style.default if style == "default" else style).derive(**style_kwargs),
    }


@dataclass(frozen=True, slots=True, repr=False)
class LayoutItem(typing.Generic[T], ABC):
    _parent: LayoutItem | Layout
    _window: AbstractWindow | None
    # margins
    _margin_left: int | float = field(default=0, kw_only=True)
    _margin_top: int | float = field(default=0, kw_only=True)
    _margin_right: int | float = field(default=0, kw_only=True)
    _margin_bottom: int | float = field(default=0, kw_only=True)
    # padding
    _padding_left: int | float = field(default=0, kw_only=True)
    _padding_top: int | float = field(default=0, kw_only=True)
    _padding_right: int | float = field(default=0, kw_only=True)
    _padding_bottom: int | float = field(default=0, kw_only=True)
    # style
    _style: Style = field(default=Style.default, kw_only=True)
    # name of space attribute
    _space_name: typing.ClassVar[str]

    def __post_init__(self):
        if self._window is not None:
            self._window.set_style(self._style)
        # validate bounds
        if isinstance(self._space, int):
            if not (self._space_min is None and self._space_max is None):
                raise errors.LayoutError(f"Cannot use bounds with absolute (integer) {self._space_name}.")
        elif self._space_min is not None and self._space_max is not None and self._space_min >= self._space_max:
            raise errors.LayoutError(f"Lower bound must be strictly less than upper bound.")

    def __repr__(self):
        return f"{self.__class__.__name__}({self._items})"

    @typing.overload
    def __getitem__(self, __i: typing.SupportsIndex) -> T:
        ...

    @typing.overload
    def __getitem__(self, __s: slice) -> list[T]:
        ...

    def __getitem__(self, i):
        return self._items.__getitem__(i)

    # properties for agnostic access
    @abstractproperty
    def _items(self) -> list[LayoutItem]:
        """Nested layout items."""
        raise NotImplementedError

    @abstractproperty
    def _space(self) -> int | float | None:
        """Space of item."""
        raise NotImplementedError

    @abstractproperty
    def _space_min(self) -> int | None:
        """Minimum space of item."""
        raise NotImplementedError

    @abstractproperty
    def _space_max(self) -> int | None:
        """Maximum space of item."""
        raise NotImplementedError

    @property
    def window(self):
        if self._window is None:
            raise errors.UnboundWindowError(f"No window has been bound to {self.__class__.__name__}.")
        return self._window

    def noutrefresh(self):
        """Delayed refresh of window and all nested layout items."""
        self.apply(lambda w: w.noutrefresh())

    def clear(self):
        """Clear window and all nested layout items."""
        self.apply(lambda w: w.clear())

    @abstractmethod
    def update(self, left: int, top: int, width: int, height: int):
        """Update all nested layout items."""
        raise NotImplementedError

    @abstractmethod
    def col(
        self,
        window: AbstractWindow | None = None,
        width: int | float | None = None,
        width_min: int | None = None,
        width_max: int | None = None,
        **kwargs: typing.Unpack[LayoutKwargs],
    ):
        """Add new column with fixed or dynamic height."""
        raise NotImplementedError

    @abstractmethod
    def row(
        self,
        window: AbstractWindow | None = None,
        height: int | float | None = None,
        height_min: int | None = None,
        height_max: int | None = None,
        **kwargs: typing.Unpack[LayoutKwargs],
    ):
        """Add new row with fixed or dynamic height."""
        raise NotImplementedError

    def _clip(self, space: int) -> int:
        """Clip to item boundaries."""
        return (
            # lower bound if above
            self._space_min
            if self._space_min is not None and space < self._space_min
            # upper bound if below
            else self._space_max
            if self._space_max is not None and space > self._space_max
            # else return arg
            else space
        )

    @abstractmethod
    def subd(self):
        raise NotImplementedError

    def apply(self, fn: typing.Callable[[AbstractWindow], typing.Any]):
        """Apply function to all nested windows."""
        # exclude root window
        if self._window and not isinstance(self._window, ScreenWindow):
            fn(self._window)
        for item in self._items:
            item.apply(fn)

    # interpret floats as share of space
    def _outer_dims(self, left: int, top: int, width: int, height: int):
        """Compute outer left, top, width and height."""
        ml, mt, mr, mb = (
            self._margin_left if isinstance(self._margin_left, int) else int(self._margin_left * width),
            self._margin_top if isinstance(self._margin_top, int) else int(self._margin_top * height),
            self._margin_right if isinstance(self._margin_right, int) else int(self._margin_right * width),
            self._margin_bottom if isinstance(self._margin_bottom, int) else int(self._margin_bottom * height),
        )
        if width < ml + mr:
            raise errors.InsufficientSpaceError("Margins cannot exceed window width.")
        elif height < mt + mb:
            raise errors.InsufficientSpaceError("Margins cannot exceed window height.")
        left, top, width, height = left + ml, top + mt, width - (ml + mr), height - (mt + mb)
        return left, top, width, height

    def _padding(self, width: int, height: int):
        """Compute window padding for left, top, right and bottom."""
        return (
            self._padding_left if isinstance(self._padding_left, int) else int(self._padding_left * width),
            self._padding_top if isinstance(self._padding_top, int) else int(self._padding_top * height),
            self._padding_right if isinstance(self._padding_right, int) else int(self._padding_right * width),
            self._padding_bottom if isinstance(self._padding_bottom, int) else int(self._padding_bottom * height),
        )

    def _set_dimensions(self, left: int, top: int, width: int, height: int):
        """Set dimensions for item window."""
        if self._window is not None and not isinstance(self._window, ScreenWindow):
            pl, pt, pr, pb = self._padding(width, height)
            if width < pl + pr:
                raise errors.InsufficientSpaceError("Padding cannot exceed window width.")
            elif height < pt + pb:
                raise errors.InsufficientSpaceError("Padding cannot exceed window height.")
            self._window.set_dimensions(left, top, width, height, pl, pt, pr, pb)

    def _allocate_space(self, space: int):
        """Compute allocated space for each item and return iterator of item-space pairs."""
        items = self._items
        idx_to_space: dict[int, int] = {}

        allocated_space = 0
        implicit_items: list[tuple[int, LayoutItem]] = []

        # allocate absolute and relative items
        for idx, item in enumerate(items):
            if item._space is None:
                # delay allocation for implicit items
                implicit_items.append((idx, item))
                continue
            if isinstance(item._space, int):
                # absolute is simple - no bounds, always equals assigned value
                item_space = item._space
            else:
                # relative may have (absolute) bounds
                item_space = item._clip(int(item._space * space))
            # store in dict to retain mapping to original order
            idx_to_space[idx] = item_space
            allocated_space += item_space

        # allocate implicit elements based on remaining space
        if implicit_items:
            bounds = tuple(
                (i[1]._space_min, i[1]._space_max)
                for i in implicit_items
                if not (i[1]._space_min is None and i[1]._space_max is None)
            )
            n_implicit_unconstrained = len(implicit_items) - len(bounds)
            remaining_space = space - allocated_space

            implicit_items_space = SpaceAllocator(bounds, n_implicit_unconstrained).solve(remaining_space)

            for i, (idx, _) in enumerate(implicit_items):
                idx_to_space[idx] = implicit_items_space[i]

        # return items and their allocated space for iteration
        return zip(self._items, (idx_to_space[i] for i in range(len(items))))


@dataclass(frozen=True, slots=True, repr=False)
class Column(LayoutItem["Row"]):
    """Layout column."""

    _parent: Row | Layout
    rows: list[Row] = field(default_factory=list, init=False)
    width: int | float | None  # None or float for dynamic allocation of available space
    width_min: int | None = None
    width_max: int | None = None
    _space_name = "width"

    def update(self, left: int, top: int, width: int, height: int):
        # incorporate margins and set window dimensions
        left, top, width, height = self._outer_dims(left, top, width, height)
        self._set_dimensions(left, top, width, height)

        if not self.rows:
            return

        # allocate height from top to bottom
        top_ = top
        for row, row_height in self._allocate_space(height):
            row.update(left, top_, width, row_height)
            top_ += row_height

    def col(
        self,
        window: AbstractWindow | None = None,
        width: int | float | None = None,
        width_min: int | None = None,
        width_max: int | None = None,
        **kwargs,
    ):
        if isinstance(self._parent, Layout):
            raise TypeError("Cannot add columns to root layout.")
        return self._parent.col(window, width, width_min, width_max, **kwargs)

    def row(
        self,
        window: AbstractWindow | None = None,
        height: int | float | None = None,
        height_min: int | None = None,
        height_max: int | None = None,
        **kwargs,
    ):
        new_row = Row(self, window, height, height_min, height_max, **_map_kwargs(style=kwargs.pop("style", self._style), **kwargs))  # type: ignore
        self.rows.append(new_row)
        return new_row

    def subd(self):
        """Subdivide column into rows via chained methods."""
        if isinstance(self._parent, Layout):
            raise TypeError("Cannot subdivide root column.")
        return ColumnSubdivider(self._parent, self)

    @property
    def _items(self):
        return self.rows

    @property
    def _space(self):
        return self.width

    @property
    def _space_min(self):
        return self.width_min

    @property
    def _space_max(self):
        return self.width_max

    @property
    def height(self):
        return self._parent.height

    @property
    def height_min(self):
        return self._parent.height_min

    @property
    def height_max(self):
        return self._parent.height_max


@dataclass(frozen=True, slots=True, repr=False)
class Row(LayoutItem["Column"]):
    """Layout row."""

    _parent: Column | Layout
    cols: list[Column] = field(default_factory=list, init=False)
    height: int | float | None  # None or float for dynamic allocation of available space
    height_min: int | None = field(default=None)
    height_max: int | None = field(default=None)
    _space_name = "height"

    def update(self, left: int, top: int, width: int, height: int):
        # incorporate margins and set window dimensions
        left, top, width, height = self._outer_dims(left, top, width, height)
        self._set_dimensions(left, top, width, height)

        if not self.cols:
            return

        # allocate width from left to right
        left_ = left
        for col, col_width in self._allocate_space(width):
            col.update(left_, top, col_width, height)
            left_ += col_width

    def row(
        self,
        window: AbstractWindow | None = None,
        height: int | float | None = None,
        height_min: int | None = None,
        height_max: int | None = None,
        **kwargs,
    ):
        return self._parent.row(window, height, height_min, height_max, **kwargs)

    def col(
        self,
        window: AbstractWindow | None = None,
        width: int | float | None = None,
        width_min: int | None = None,
        width_max: int | None = None,
        **kwargs,
    ):
        new_col = Column(self, window, width, width_min, width_max, **_map_kwargs(style=kwargs.pop("style", self._style), **kwargs))  # type: ignore
        self.cols.append(new_col)
        return new_col

    def subd(self):
        """Subdivide row into columns via chained methods."""
        if isinstance(self._parent, Layout):
            raise TypeError("Cannot subdivide root row.")
        return RowSubdivider(self._parent, self)

    @property
    def _items(self):
        return self.cols

    @property
    def _space(self):
        return self.height

    @property
    def _space_min(self):
        return self.height_min

    @property
    def _space_max(self):
        return self.height_max

    @property
    def width(self):
        return self._parent.width

    @property
    def width_min(self):
        return self._parent.width_min

    @property
    def width_max(self):
        return self._parent.width_max


@dataclass(slots=True)
class LayoutItemSubdivider(ABC):
    parent: LayoutItem | LayoutItemSubdivider
    _row: Row | None
    _col: Column | None

    @abstractmethod
    def col(
        self,
        window: AbstractWindow | None = None,
        width: int | float | None = None,
        width_min: int | None = None,
        width_max: int | None = None,
        **kwargs: typing.Unpack[LayoutKwargs],
    ):
        """Add new column with fixed or dynamic width."""
        raise NotImplementedError

    @abstractmethod
    def row(
        self,
        window: AbstractWindow | None = None,
        height: int | float | None = None,
        height_min: int | None = None,
        height_max: int | None = None,
        **kwargs: typing.Unpack[LayoutKwargs],
    ):
        """Add new row with fixed or dynamic height."""
        raise NotImplementedError

    @abstractmethod
    def subd(self):
        raise NotImplementedError


@dataclass(slots=True)
class RowSubdivider(LayoutItemSubdivider):
    parent: Column | ColumnSubdivider
    _row: Row
    _col: Column | None = field(default=None, init=False)

    def col(
        self,
        window: AbstractWindow | None = None,
        width: int | float | None = None,
        width_min: int | None = None,
        width_max: int | None = None,
        **kwargs,
    ):
        new_col = self._row.col(window, width, width_min, width_max, **kwargs)
        self._col = new_col
        return self

    def row(
        self,
        window: AbstractWindow | None = None,
        height: int | float | None = None,
        height_min: int | None = None,
        height_max: int | None = None,
        **kwargs,
    ):
        return self.parent.row(window, height, height_min, height_max, **kwargs)

    def subd(self):
        """Subdivide column into rows via chained methods."""
        if self._col is None:
            raise errors.LayoutError("Cannot subdivide before adding a column.")
        return ColumnSubdivider(self, self._col)


@dataclass(slots=True)
class ColumnSubdivider(LayoutItemSubdivider):
    parent: Row | RowSubdivider
    _col: Column
    _row: Row | None = field(default=None, init=False)

    def col(
        self,
        window: AbstractWindow | None = None,
        width: int | float | None = None,
        width_min: int | None = None,
        width_max: int | None = None,
        **kwargs,
    ):
        return self.parent.col(window, width, width_min, width_max, **kwargs)

    def row(
        self,
        window: AbstractWindow | None = None,
        height: int | float | None = None,
        height_min: int | None = None,
        height_max: int | None = None,
        **kwargs,
    ):
        new_row = self._col.row(window, height, height_min, height_max, **kwargs)
        self._row = new_row
        return self

    def subd(self):
        """Subdivide row into columns via chained methods."""
        if self._row is None:
            raise errors.LayoutError("Cannot subdivide before adding a row.")
        return RowSubdivider(self, self._row)


class Layout:
    """Partition screen into a responsive layout of nested rows and columns."""

    def __init__(self, __root_window: AbstractWindow | None = None, **kwargs: typing.Unpack[LayoutKwargs]):
        self.__root = None
        self.__root_window = __root_window
        self.kwargs = kwargs
        # dimensions
        self.__height = None
        self.__width = None

    def __repr__(self):
        return f"{self.__class__.__name__}({self.root._items if self.__root else '[]'})"

    def row(
        self,
        window: AbstractWindow | None = None,
        height: int | float | None = None,
        height_min: int | None = None,
        height_max: int | None = None,
        **kwargs: typing.Unpack[LayoutKwargs],
    ):
        """Subdivide layout into rows via chained methods."""
        if self.__root is None:
            self.__root = Column(self, self.__root_window, None, **_map_kwargs(**self.kwargs))
        elif isinstance(self.__root, Row):
            raise errors.LayoutError("Cannot add row to row-major layout.")
        return self.root.row(window, height, height_min, height_max, **kwargs)

    def col(
        self,
        window: AbstractWindow | None = None,
        width: int | float | None = None,
        width_min: int | None = None,
        width_max: int | None = None,
        **kwargs: typing.Unpack[LayoutKwargs],
    ):
        """Subdivide layout into columns via chained methods."""
        if self.__root is None:
            self.__root = Row(self, self.__root_window, None, **_map_kwargs(**self.kwargs))
        elif isinstance(self.__root, Column):
            raise errors.LayoutError("Cannot add column to column-major layout.")
        return self.__root.col(window, width, width_min, width_max, **kwargs)

    def update(self, left: int, top: int, width: int, height: int):
        """Update rows and columns of layout."""
        self.root.update(left, top, width, height)

    def noutrefresh(self):
        """Refresh all windows in layout."""
        self.root.noutrefresh()

    def clear(self):
        """Clear all windows in layout."""
        self.root.clear()

    def apply(self, fn: typing.Callable[[AbstractWindow], typing.Any]):
        """Apply function to all windows in layout."""
        self.root.apply(fn)

    @property
    def root(self):
        if self.__root is None:
            raise errors.LayoutError("No root node in layout - add a node with 'col' or 'row' methods.")
        return self.__root

    @property
    def window(self):
        return self.root.window

    @property
    def rows(self) -> list[Row]:
        """Rows of root layout."""
        if isinstance(self.root, Column):
            return self.root.rows
        return []

    @property
    def cols(self) -> list[Column]:
        """Columns of root layout."""
        if isinstance(self.root, Row):
            return self.root.cols
        return []

    @property
    def order(self):
        """Order of layout (row / column major)."""
        return "col" if isinstance(self.__root, Column) else "row" if isinstance(self.__root, Row) else None

    def flatten(self) -> list[Row | Column]:
        """Flattened list of all layout items."""
        items = []

        def append_items(outer_item: LayoutItem):
            items.append(outer_item)
            for inner_item in outer_item._items:
                append_items(inner_item)

        append_items(self.root)
        return items

    @property
    def windows(self) -> list[AbstractWindow]:
        """Flattened list of all layout windows."""
        return [item._window for item in self.flatten() if item._window is not None]

    @typing.overload
    def __getitem__(self, __i: typing.SupportsIndex) -> Row | Column:
        ...

    @typing.overload
    def __getitem__(self, __s: slice) -> list[Row | Column]:
        ...

    def __getitem__(self, i):
        return self.root.__getitem__(i)

    @property
    def height(self):
        if self.__width is None:
            raise errors.LayoutError("Cannot access height before layout has been updated.")
        return self.__height

    @property
    def height_min(self):
        return None

    @property
    def height_max(self):
        return None

    @property
    def width(self):
        if self.__width is None:
            raise errors.LayoutError("Cannot access width before layout has been updated.")
        return self.__width

    @property
    def width_min(self):
        return None

    @property
    def width_max(self):
        return None
