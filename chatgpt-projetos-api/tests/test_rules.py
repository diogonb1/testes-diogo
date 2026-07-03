from app.rules import classify_text


def test_alvara():
    c = classify_text("Alvarás Sanitários Caucaia", "AVCB funcionamento")
    assert c["codigo"] == "BUI-004"


def test_luthieria():
    c = classify_text("Giannini MasterSonic", "escudo hardware preto")
    assert c["codigo"] == "LUT-001"


def test_jde():
    c = classify_text("Plano JDE L262", "Safefood EXH-002")
    assert c["codigo"] == "BUI-002"
