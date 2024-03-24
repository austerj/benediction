from __future__ import annotations

import typing
from abc import ABC, abstractmethod, abstractproperty
from dataclasses import dataclass, field

from hexes import errors
from hexes.style import Style, StyleKwargs
from hexes.window import AbstractWindow, ScreenWindow


class LayoutKwargs(StyleKwargs, typing.TypedDict):
    style: typing.NotRequired[Style]
    # margins
    m: typing.NotRequired[int | None]
    my: typing.NotRequired[int | None]
    mx: typing.NotRequired[int | None]
    mt: typing.NotRequired[int | None]
    mb: typing.NotRequired[int | None]
    ml: typing.NotRequired[int | None]
    mr: typing.NotRequired[int | None]
    # padding
    p: typing.NotRequired[int | None]
    py: typing.NotRequired[int | None]
    px: typing.NotRequired[int | None]
    pt: typing.NotRequired[int | None]
    pb: typing.NotRequired[int | None]
    pl: typing.NotRequired[int | None]
    pr: typing.NotRequired[int | None]


def _map_kwargs(
    # margins
    m: int | None = None,
    my: int | None = None,
    mx: int | None = None,
    mt: int | None = None,
    mb: int | None = None,
    ml: int | None = None,
    mr: int | None = None,
    # padding
    p: int | None = None,
    py: int | None = None,
    px: int | None = None,
    pt: int | None = None,
    pb: int | None = None,
    pl: int | None = None,
    pr: int | None = None,
    # style
    style: Style = Style.default,
    **style_kwargs: typing.Unpack[StyleKwargs],
) -> dict[str, typing.Any]:
    return dict(
        # margins with priority given to most specific keyword
        _margin_top=mt if mt is not None else my if my is not None else m if m is not None else 0,
        _margin_bottom=mb if mb is not None else my if my is not None else m if m is not None else 0,
        _margin_left=ml if ml is not None else mx if mx is not None else m if m is not None else 0,
        _margin_right=mr if mr is not None else mx if mx is not None else m if m is not None else 0,
        # padding with priority given to most specific keyword
        _padding_top=pt if pt is not None else py if py is not None else p if p is not None else 0,
        _padding_bottom=pb if pb is not None else py if py is not None else p if p is not None else 0,
        _padding_left=pl if pl is not None else px if px is not None else p if p is not None else 0,
        _padding_right=pr if pr is not None else px if px is not None else p if p is not None else 0,
        # style
        _style=style.inherit(**style_kwargs),
    )


@dataclass(frozen=True, slots=True)
class LayoutItem(ABC):
    _parent: LayoutItem | Layout
    _window: AbstractWindow | None
    # margins
    _margin_left: int = field(default=0, repr=False, kw_only=True)
    _margin_top: int = field(default=0, repr=False, kw_only=True)
    _margin_right: int = field(default=0, repr=False, kw_only=True)
    _margin_bottom: int = field(default=0, repr=False, kw_only=True)
    # padding
    _padding_left: int = field(default=0, repr=False, kw_only=True)
    _padding_top: int = field(default=0, repr=False, kw_only=True)
    _padding_right: int = field(default=0, repr=False, kw_only=True)
    _padding_bottom: int = field(default=0, repr=False, kw_only=True)
    # style
    _style: Style = field(default=Style.default, repr=False, kw_only=True)

    def __post_init__(self):
        if self._window is not None:
            self._window.set_style(self._style)

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

    @abstractproperty
    def _items(self) -> list[LayoutItem]:
        """Nested layout items."""
        raise NotImplementedError

    @abstractmethod
    def update(self, left: int, top: int, width: int, height: int):
        """Update all nested layout items."""
        raise NotImplementedError

    @abstractmethod
    def col(
        self,
        window: AbstractWindow | None = None,
        width: int | float | None = None,
        **kwargs: typing.Unpack[LayoutKwargs],
    ):
        """Add new column with fixed or dynamic height."""
        raise NotImplementedError

    @abstractmethod
    def row(
        self,
        window: AbstractWindow | None = None,
        height: int | float | None = None,
        **kwargs: typing.Unpack[LayoutKwargs],
    ):
        """Add new row with fixed or dynamic height."""
        raise NotImplementedError

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


@dataclass(frozen=True, slots=True)
class Column(LayoutItem):
    """Layout column."""

    _parent: Row | Layout = field(repr=False)
    width: int | float | None  # None or float for dynamic allocation of available space
    _rows: list[Row] = field(default_factory=list, init=False)

    def update(self, left: int, top: int, width: int, height: int):
        # incorporate margins
        left += self._margin_left
        top += self._margin_top
        width -= self._margin_left + self._margin_right
        height -= self._margin_top + self._margin_bottom

        # track allocation of height
        top_ = top

        # initialize dynamic height allocation
        dynamic_height = height - sum(row.height if isinstance(row.height, int) else 0 for row in self._rows)
        remaining_dynamic_height = dynamic_height
        n_implicit_rows = sum(row.height is None for row in self._rows)
        n_dynamic_rows = sum(not isinstance(row.height, int) for row in self._rows)
        dynamic_rows_allocated = 0

        # explicit and implicit ratios
        explicit_ratio = sum(row.height if isinstance(row.height, float) else 0.0 for row in self._rows)
        if not (0.0 <= explicit_ratio <= 1.0):
            raise errors.InsufficientSpaceError("Cannot dynamically allocate more height than available.")
        implicit_ratio = (1.0 - explicit_ratio) / n_implicit_rows if n_implicit_rows > 0 else 0.0

        # raise if unable to allocate at least 1 height unit per row
        if dynamic_height < n_dynamic_rows:
            raise errors.InsufficientSpaceError()

        if self._window and not isinstance(self._window, ScreenWindow):
            self._window.set_dimensions(
                left,
                top,
                width,
                height,
                self._padding_left,
                self._padding_top,
                self._padding_right,
                self._padding_bottom,
            )

        # allocate height across rows
        for row in self._rows:
            if isinstance(row.height, int):
                row_height = row.height
            else:
                # assign all remaining height if last dynamic row
                if dynamic_rows_allocated == n_dynamic_rows - 1:
                    row_height = remaining_dynamic_height
                else:
                    # else assign ratio of dynamic height
                    row_ratio = implicit_ratio if row.height is None else row.height
                    row_height = round(dynamic_height * row_ratio)
                    remaining_dynamic_height -= row_height
                dynamic_rows_allocated += 1
            row.update(left, top_, width, row_height)
            top_ += row_height

    def col(self, window: AbstractWindow | None = None, width: int | float | None = None, **kwargs):
        if isinstance(self._parent, Layout):
            raise TypeError("Cannot add columns to root layout.")
        return self._parent.col(window, width, **kwargs)

    def row(self, window: AbstractWindow | None = None, height: int | float | None = None, **kwargs):
        new_row = Row(self, window, height, **_map_kwargs(style=kwargs.pop("style", self._style), **kwargs))  # type: ignore
        self._rows.append(new_row)
        return new_row

    def subd(self):
        """Subdivide column into rows via chained methods."""
        if isinstance(self._parent, Layout):
            raise TypeError("Cannot subdivide root column.")
        return ColumnSubdivider(self._parent, self)

    @property
    def rows(self):
        """Rows nested in column."""
        return self._rows

    @property
    def _items(self):
        return self._rows


@dataclass(frozen=True, slots=True)
class Row(LayoutItem):
    """Layout row."""

    _parent: Column | Layout
    height: int | float | None  # None or float for dynamic allocation of available space
    _cols: list[Column] = field(default_factory=list, init=False)

    def update(self, left: int, top: int, width: int, height: int):
        # incorporate margins
        left += self._margin_left
        top += self._margin_top
        width -= self._margin_left + self._margin_right
        height -= self._margin_top + self._margin_bottom

        # track allocation of width
        left_ = left

        # initialize dynamic width allocation
        dynamic_width = width - sum(col.width if isinstance(col.width, int) else 0 for col in self._cols)
        remaining_dynamic_width = dynamic_width
        n_implicit_cols = sum(col.width is None for col in self._cols)
        n_dynamic_cols = sum(not isinstance(col.width, int) for col in self._cols)
        dynamic_cols_allocated = 0

        # explicit and implicit ratios
        explicit_ratio = sum(col.width if isinstance(col.width, float) else 0.0 for col in self._cols)
        if not (0.0 <= explicit_ratio <= 1.0):
            raise errors.InsufficientSpaceError("Cannot dynamically allocate more width than available.")
        implicit_ratio = (1.0 - explicit_ratio) / n_implicit_cols if n_implicit_cols > 0 else 0.0

        # raise if unable to allocate at least 1 width unit per row
        if dynamic_width < n_dynamic_cols:
            raise errors.InsufficientSpaceError()

        if self._window and not isinstance(self._window, ScreenWindow):
            self._window.set_dimensions(
                left,
                top,
                width,
                height,
                self._padding_left,
                self._padding_top,
                self._padding_right,
                self._padding_bottom,
            )

        # allocate width across cols
        for col in self._cols:
            if isinstance(col.width, int):
                col_width = col.width
            else:
                # assign all remaining width if last dynamic col
                if dynamic_cols_allocated == n_dynamic_cols - 1:
                    col_width = remaining_dynamic_width
                else:
                    # else assign ratio of dynamic width
                    col_ratio = implicit_ratio if col.width is None else col.width
                    col_width = round(dynamic_width * col_ratio)
                    remaining_dynamic_width -= col_width
                dynamic_cols_allocated += 1
            col.update(left_, top, col_width, height)
            left_ += col_width

    def row(self, window: AbstractWindow | None = None, height: int | float | None = None, **kwargs):
        return self._parent.row(window, height, **kwargs)

    def col(self, window: AbstractWindow | None = None, width: int | float | None = None, **kwargs):
        new_col = Column(self, window, width, **_map_kwargs(style=kwargs.pop("style", self._style), **kwargs))  # type: ignore
        self._cols.append(new_col)
        return new_col

    def subd(self):
        """Subdivide row into columns via chained methods."""
        if isinstance(self._parent, Layout):
            raise TypeError("Cannot subdivide root row.")
        return RowSubdivider(self._parent, self)

    @property
    def cols(self):
        """Columns nested in row."""
        return self._cols

    @property
    def _items(self):
        return self._cols


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
        **kwargs: typing.Unpack[LayoutKwargs],
    ):
        """Add new column with fixed or dynamic width."""
        raise NotImplementedError

    @abstractmethod
    def row(
        self,
        window: AbstractWindow | None = None,
        height: int | float | None = None,
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

    def col(self, window: AbstractWindow | None = None, width: int | float | None = None, **kwargs):
        new_col = self._row.col(window, width, **kwargs)
        self._col = new_col
        return self

    def row(self, window: AbstractWindow | None = None, height: int | float | None = None, **kwargs):
        return self.parent.row(window, height, **kwargs)

    def subd(self):
        """Subdivide column into rows via chained methods."""
        if self._col is None:
            raise RuntimeError("Cannot subdivide before adding a column.")
        return ColumnSubdivider(self, self._col)


@dataclass(slots=True)
class ColumnSubdivider(LayoutItemSubdivider):
    parent: Row | RowSubdivider
    _col: Column
    _row: Row | None = field(default=None, init=False)

    def col(self, window: AbstractWindow | None = None, width: int | float | None = None, **kwargs):
        return self.parent.col(window, width, **kwargs)

    def row(self, window: AbstractWindow | None = None, height: int | float | None = None, **kwargs):
        new_row = self._col.row(window, height, **kwargs)
        self._row = new_row
        return self

    def subd(self):
        """Subdivide row into columns via chained methods."""
        if self._row is None:
            raise RuntimeError("Cannot subdivide before adding a row.")
        return RowSubdivider(self, self._row)


@dataclass(init=False)
class Layout:
    """Partition screen into a responsive layout of nested rows and columns."""

    # root layout node
    __root: Column | Row | None = field(default=None, init=False)
    __root_window: AbstractWindow | None = field(default=None)

    def __init__(self, __root_window: AbstractWindow | None = None, **kwargs: typing.Unpack[LayoutKwargs]):
        self.__root_window = __root_window
        self.kwargs = kwargs

    def row(
        self,
        window: AbstractWindow | None = None,
        height: int | float | None = None,
        **kwargs: typing.Unpack[LayoutKwargs],
    ):
        """Subdivide layout into rows via chained methods."""
        if self.__root is None:
            self.__root = Column(self, self.__root_window, None, **_map_kwargs(**self.kwargs))
        elif isinstance(self.__root, Row):
            raise errors.LayoutError("Cannot add row to row-major layout.")
        return self.root.row(window, height, **kwargs)

    def col(
        self,
        window: AbstractWindow | None = None,
        width: int | float | None = None,
        **kwargs: typing.Unpack[LayoutKwargs],
    ):
        """Subdivide layout into columns via chained methods."""
        if self.__root is None:
            self.__root = Row(self, self.__root_window, None, **_map_kwargs(**self.kwargs))
        elif isinstance(self.__root, Column):
            raise errors.LayoutError("Cannot add column to column-major layout.")
        return self.__root.col(window, width, **kwargs)

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
            raise errors.LayoutError("No root node in layout.")
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

    @property
    def items(self) -> list[Row | Column]:
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
        return [item._window for item in self.items if item._window is not None]
