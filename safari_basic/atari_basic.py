"""Shim for backward compatibility. Use safari_basic.interpreter instead."""

from safari_basic.interpreter import BasicError
from safari_basic.interpreter import SafariBasic as AtariBasic

__all__ = ["AtariBasic", "BasicError"]
