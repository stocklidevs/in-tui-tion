"""intui.adapters: engine-free normalizers from third-party producers.

An adapter maps a producer's on-the-wire events onto the canonical in-TUI-tion
vocabulary so the zero-config runner renders them with no producer-specific code
in the console or the kit. Adapters import no terminal engine (layering guard).
"""

from intui.adapters.intentforge import IntentForgeSource, adapt_record

__all__ = ["IntentForgeSource", "adapt_record"]
