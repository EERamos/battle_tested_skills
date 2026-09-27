import build


def test_contrast_black_white_is_21() -> None:
    assert round(build.contrast("#000000", "#FFFFFF"), 2) == 21.0


def test_contrast_is_symmetric() -> None:
    assert build.contrast("#12716B", "#FBFCFE") == build.contrast("#FBFCFE", "#12716B")


def test_oklch_round_trip() -> None:
    for hexv in ("#FBFCFE", "#151B33", "#12716B", "#8A4FD3"):
        L, C, H = build.to_oklch(hexv)
        assert build.from_oklch(L, C, H) == hexv
