"""Custom exceptions for Ophanic parser."""


class OphanicError(Exception):
    """Base exception for parser errors."""

    def __init__(
        self,
        message: str,
        line: int | None = None,
        column: int | None = None,
    ):
        self.line = line
        self.column = column
        location = ""
        if line is not None:
            location = f" at line {line + 1}"
            if column is not None:
                location += f", column {column + 1}"
        super().__init__(f"{message}{location}")


class UnclosedBoxError(OphanicError):
    """A box was started but not properly closed."""

    pass


class InvalidNestingError(OphanicError):
    """Boxes overlap in an invalid way."""

    pass


class MissingBreakpointError(OphanicError):
    """Diagram found without a @breakpoint tag."""

    pass


class UnknownComponentError(OphanicError):
    """Referenced component not found in document."""

    pass
