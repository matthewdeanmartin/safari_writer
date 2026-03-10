"""Shim for backward compatibility. Use safari_basic.interpreter instead."""

from safari_basic.interpreter import SafariBasic as AtariBasic, BasicError

__all__ = ["AtariBasic", "BasicError"]
