# Placeholder for test_pw3365_parser.py
from src.utils.pw3365_parser import convert_e_notation, parse_raw_data

def test_convert_e_notation():
    assert convert_e_notation("1.23E+03") == 1230.0
    assert convert_e_notation("invalid") == "invalid"

def test_parse_raw_data():
    raw = "U1 1.23E+03;I1 2.34E+00"
    parsed = parse_raw_data(raw)
    assert "U1" in parsed
    assert "I1" in parsed
