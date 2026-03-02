from app.utils.doc_convert import find_soffice


def test_find_soffice_prefers_soffice_path_env(tmp_path, monkeypatch):
    dummy = tmp_path / "soffice.exe"
    dummy.write_bytes(b"")
    monkeypatch.setenv("SOFFICE_PATH", str(dummy))
    monkeypatch.delenv("LIBREOFFICE_HOME", raising=False)
    assert find_soffice() == str(dummy)


def test_find_soffice_from_libreoffice_home(tmp_path, monkeypatch):
    home = tmp_path / "lo"
    (home / "program").mkdir(parents=True, exist_ok=True)
    exe = home / "program" / "soffice.exe"
    exe.write_bytes(b"")
    monkeypatch.delenv("SOFFICE_PATH", raising=False)
    monkeypatch.setenv("LIBREOFFICE_HOME", str(home))
    assert find_soffice() == str(exe)

