import pefile


def GetFileVersion(filename: str) -> str:
    pe = pefile.PE(filename, fast_load=True)
    try:
        if not getattr(pe, "VS_FIXEDFILEINFO", None):
            raise ValueError("No fixed file version information found")

        info = pe.VS_FIXEDFILEINFO[0]
        ms = info.FileVersionMS
        ls = info.FileVersionLS

        major = ms >> 16
        minor = ms & 0xFFFF
        build = ls >> 16
        revision = ls & 0xFFFF
        return f"{major}.{minor}.{build}.{revision}"
    finally:
        pe.close()
