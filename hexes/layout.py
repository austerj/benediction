from __future__ import annotations

from dataclasses import dataclass, field

from hexes import errors
from hexes.window import AbstractWindow


def _compute_margins(
    m: int | None = None,
    my: int | None = None,
    mx: int | None = None,
    mt: int | None = None,
    mb: int | None = None,
    ml: int | None = None,
    mr: int | None = None,
    **kwargs,
):
    # compute margins with priority given to most specific keyword
    return dict(
        _margin_top=mt if mt is not None else my if my is not None else m if m is not None else 0,
        _margin_bottom=mb if mb is not None else my if my is not None else m if m is not None else 0,
        _margin_left=ml if ml is not None else mx if mx is not None else m if m is not None else 0,
        _margin_right=mr if mr is not None else mx if mx is not None else m if m is not None else 0,
    )


@dataclass
class Column:
    """Layout column."""

    _parent: Row | Layout = field(repr=False)
    _window: AbstractWindow | None
    width: int | None  # None for dynamic allocation of available space
    _rows: list[Row] = field(default_factory=list, init=False)
    # margins
    _margin_left: int = field(default=0, repr=False)
    _margin_top: int = field(default=0, repr=False)
    _margin_right: int = field(default=0, repr=False)
    _margin_bottom: int = field(default=0, repr=False)

    def refresh(self):
        if self._window:
            self._window.refresh()
        for row in self._rows:
            row.refresh()

    def update(self, left: int, top: int, width: int, height: int):
        # incorporate margins
        left += self._margin_left
        top += self._margin_top
        width -= self._margin_left + self._margin_right
        height -= self._margin_top + self._margin_bottom

        # track allocation of height
        top_ = top
        n_free_rows = sum(row.height is None for row in self._rows)
        free_height = height - sum(row.height if row.height is not None else 0 for row in self._rows)
        free_rows_allocated = 0

        # raise if unable to allocate at least 1 height unit per row
        if free_height < n_free_rows:
            raise errors.InsufficientSpaceError()

        if self._window:
            self._window.set_dimensions(left, top, width, height)

        # allocate height across rows
        for row in self._rows:
            if row.height is None:
                # assign all remaining free height if last free row
                if free_rows_allocated == n_free_rows - 1:
                    row_height = free_height
                # else assign fraction of total free height if not the last free row
                else:
                    free_height_frac = free_height // (n_free_rows - free_rows_allocated)
                    free_height -= free_height_frac
                    row_height = free_height_frac
                free_rows_allocated += 1
            else:
                row_height = row.height
            row.update(left, top_, width, row_height)
            top_ += row_height

    def row(self, window: AbstractWindow | None = None, height: int | None = None, **kwargs):
        """Add new row with fixed or dynamic height."""
        if self._window:
            raise RuntimeError("Cannot split column with a window attached into rows.")
        new_row = Row(self, window, height, **_compute_margins(**kwargs))
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

    _parent: Column = field(repr=False)
    _window: AbstractWindow | None
    height: int | None  # None for dynamic allocation of available space
    _cols: list[Column] = field(default_factory=list, init=False)
    # margins
    _margin_left: int = field(default=0, repr=False)
    _margin_top: int = field(default=0, repr=False)
    _margin_right: int = field(default=0, repr=False)
    _margin_bottom: int = field(default=0, repr=False)

    def refresh(self):
        if self._window:
            self._window.refresh()
        for col in self._cols:
            col.refresh()

    def update(self, left: int, top: int, width: int, height: int):
        # incorporate margins
        left += self._margin_left
        top += self._margin_top
        width -= self._margin_left + self._margin_right
        height -= self._margin_top + self._margin_bottom

        # track allocation of width
        left_ = left
        n_free_cols = sum(col.width is None for col in self._cols)
        free_width = width - sum(col.width if col.width is not None else 0 for col in self._cols)
        free_cols_allocated = 0

        # raise if unable to allocate at least 1 width unit per col
        if free_width < n_free_cols:
            raise errors.InsufficientSpaceError()

        if self._window:
            self._window.set_dimensions(left, top, width, height)

        # allocate width across cols
        for col in self._cols:
            if col.width is None:
                # assign all remaining free width if last free col
                if free_cols_allocated == n_free_cols - 1:
                    col_width = free_width
                # else assign fraction of total free width if not the last free col
                else:
                    free_width_frac = free_width // (n_free_cols - free_cols_allocated)
                    free_width -= free_width_frac
                    col_width = free_width_frac
                free_cols_allocated += 1
            else:
                col_width = col.width
            col.update(left_, top, col_width, height)
            left_ += col_width

    def col(self, window: AbstractWindow | None = None, width: int | None = None, **kwargs):
        """Add new column with fixed or dynamic width."""
        if self._window:
            raise RuntimeError("Cannot split row with a window attached into columns.")
        new_col = Column(self, window, width, **_compute_margins(**kwargs))
        self._cols.append(new_col)
        return new_col

    def subd(self):
        """Subdivide row into columns via chained methods."""
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

    def col(self, window: AbstractWindow | None = None, width: int | None = None, **kwargs):
        """Add new column with fixed or dynamic width."""
        new_col = self._row.col(window, width, **kwargs)
        self._col = new_col
        return self

    def row(self, window: AbstractWindow | None = None, height: int | None = None, **kwargs):
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

    def col(self, window: AbstractWindow | None = None, width: int | None = None, **kwargs):
        """Add new column with fixed or dynamic width."""
        return self.parent.col(window, width, **kwargs)

    def row(self, window: AbstractWindow | None = None, height: int | None = None, **kwargs):
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

    # root layout column
    __col: Column = field(init=False)

    def __post_init__(self):
        self.__col = Column(self, None, None)

    def row(self, window: AbstractWindow | None = None, height: int | None = None, **kwargs):
        """Add new row with fixed or dynamic height."""
        return self.__col.row(window, height, **kwargs)

    def update(self, height: int, width: int):
        """Update rows and columns of layout."""
        self.__col.update(0, 0, width, height)

    def refresh(self):
        """Refresh all windows in layout."""
        self.__col.refresh()

    @property
    def rows(self):
        """Rows of root layout."""
        return self.__col.rows
