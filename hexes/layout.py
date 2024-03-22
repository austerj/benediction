from __future__ import annotations

from dataclasses import dataclass, field

from hexes import errors
from hexes.window import AbstractWindow


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
    **kwargs,
):
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
    )


@dataclass
class Column:
    """Layout column."""

    _parent: Row | Layout = field(repr=False)
    _window: AbstractWindow | None
    width: int | float | None  # None or float for dynamic allocation of available space
    _rows: list[Row] = field(default_factory=list, init=False)
    # margins
    _margin_left: int = field(default=0, repr=False)
    _margin_top: int = field(default=0, repr=False)
    _margin_right: int = field(default=0, repr=False)
    _margin_bottom: int = field(default=0, repr=False)
    # padding
    _padding_left: int = field(default=0, repr=False)
    _padding_top: int = field(default=0, repr=False)
    _padding_right: int = field(default=0, repr=False)
    _padding_bottom: int = field(default=0, repr=False)

    def noutrefresh(self):
        if self._window:
            self._window.noutrefresh()
        for row in self._rows:
            row.noutrefresh()

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

        if self._window:
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
        """Add new column with fixed or dynamic height."""
        if isinstance(self._parent, Layout):
            raise TypeError("Cannot add columns to root layout.")
        return self._parent.col(window, width, **kwargs)

    def row(self, window: AbstractWindow | None = None, height: int | float | None = None, **kwargs):
        """Add new row with fixed or dynamic height."""
        if self._window:
            raise RuntimeError("Cannot split column with a window attached into rows.")
        new_row = Row(self, window, height, **_map_kwargs(**kwargs))
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
    def window(self):
        if self._window is None:
            raise errors.UnboundWindowError("No window has been bound to Column.")
        return self._window


@dataclass
class Row:
    """Layout row."""

    _parent: Column | Layout = field(repr=False)
    _window: AbstractWindow | None
    height: int | float | None  # # None or float for dynamic allocation of available space
    _cols: list[Column] = field(default_factory=list, init=False)
    # margins
    _margin_left: int = field(default=0, repr=False)
    _margin_top: int = field(default=0, repr=False)
    _margin_right: int = field(default=0, repr=False)
    _margin_bottom: int = field(default=0, repr=False)
    # padding
    _padding_left: int = field(default=0, repr=False)
    _padding_top: int = field(default=0, repr=False)
    _padding_right: int = field(default=0, repr=False)
    _padding_bottom: int = field(default=0, repr=False)

    def noutrefresh(self):
        if self._window:
            self._window.noutrefresh()
        for col in self._cols:
            col.noutrefresh()

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

        if self._window:
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
        """Add new row with fixed or dynamic height."""
        return self._parent.row(window, height, **kwargs)

    def col(self, window: AbstractWindow | None = None, width: int | float | None = None, **kwargs):
        """Add new column with fixed or dynamic width."""
        if self._window:
            raise RuntimeError("Cannot split row with a window attached into columns.")
        new_col = Column(self, window, width, **_map_kwargs(**kwargs))
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
    def window(self):
        if self._window is None:
            raise errors.UnboundWindowError("No window has been bound to Column.")
        return self._window


@dataclass
class RowSubdivider:
    parent: Column | ColumnSubdivider
    _row: Row
    _col: Column | None = field(default=None, init=False)

    def col(self, window: AbstractWindow | None = None, width: int | float | None = None, **kwargs):
        """Add new column with fixed or dynamic width."""
        new_col = self._row.col(window, width, **kwargs)
        self._col = new_col
        return self

    def row(self, window: AbstractWindow | None = None, height: int | float | None = None, **kwargs):
        """Add new row with fixed or dynamic height."""
        return self.parent.row(window, height, **kwargs)

    def subd(self):
        """Subdivide column into rows via chained methods."""
        if self._col is None:
            raise RuntimeError("Cannot subdivide before adding a column.")
        return ColumnSubdivider(self, self._col)


@dataclass
class ColumnSubdivider:
    parent: Row | RowSubdivider
    _col: Column
    _row: Row | None = field(default=None, init=False)

    def col(self, window: AbstractWindow | None = None, width: int | float | None = None, **kwargs):
        """Add new column with fixed or dynamic width."""
        return self.parent.col(window, width, **kwargs)

    def row(self, window: AbstractWindow | None = None, height: int | float | None = None, **kwargs):
        """Add new row with fixed or dynamic height."""
        new_row = self._col.row(window, height, **kwargs)
        self._row = new_row
        return self

    def subd(self):
        """Subdivide row into columns via chained methods."""
        if self._row is None:
            raise RuntimeError("Cannot subdivide before adding a row.")
        return RowSubdivider(self, self._row)


@dataclass
class Layout:
    """Partition screen into a responsive layout of nested rows and columns."""

    # root layout node
    __root: Column | Row | None = field(default=None, init=False)

    def __post_init__(self, **kwargs):
        self.kwargs = kwargs

    def row(self, window: AbstractWindow | None = None, height: int | float | None = None, **kwargs):
        """Subdivide layout into rows via chained methods."""
        if self.__root is None:
            self.__root = Column(self, None, None, **_map_kwargs(**self.kwargs))
        elif isinstance(self.__root, Row):
            raise errors.LayoutError("Cannot add row to row-major layout.")
        return self.root.row(window, height, **kwargs)

    def col(self, window: AbstractWindow | None = None, width: int | float | None = None, **kwargs):
        """Subdivide layout into columns via chained methods."""
        if self.__root is None:
            self.__root = Row(self, None, None, **_map_kwargs(**self.kwargs))
        elif isinstance(self.__root, Column):
            raise errors.LayoutError("Cannot add column to column-major layout.")
        return self.__root.col(window, width, **kwargs)

    def update(self, left: int, top: int, height: int, width: int):
        """Update rows and columns of layout."""
        self.root.update(left, top, width, height)

    def noutrefresh(self):
        """Refresh all windows in layout."""
        self.root.noutrefresh()

    @property
    def root(self):
        if self.__root is None:
            raise errors.LayoutError("No root node in layout.")
        return self.__root

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
