# niton_parser.py
# Thermo Scientific Niton XL2 / XL3 / XL5 series parser
# For Basalt Provenance Triage Toolkit

import re

class NitonParser:
    """
    Parser for Thermo Niton pXRF output (XL2/XL3/XL5 series).
    Handles common CSV-like and key-value formats.
    """

    def parse(self, raw_text: str) -> dict[str, float]:
        """
        Parse raw Niton output string into {element_ppm: value} dictionary.
        Returns empty dict if nothing useful found.
        """
        result = {}
        lines = raw_text.splitlines()

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or 'Analyte' in line or '====' in line:
                continue

            # Pattern 1: "Zr,145.2,ppm" or "Zr,145.2"
            m = re.match(r'^([A-Z][a-z]?),?\s*([\d\.]+),?\s*(ppm|%)?', line, re.IGNORECASE)
            if m:
                elem, value, unit = m.groups()
                try:
                    val = float(value)
                    if unit and '%' in unit.lower():
                        val *= 10000  # convert % to ppm
                    result[f"{elem}_ppm"] = val
                except ValueError:
                    pass
                continue

            # Pattern 2: "Zr = 145.2 ppm" or "Zr: 145.2 ppm" or "Zr 145.2 ppm"
            m = re.search(r'([A-Z][a-z]?)\s*[=: ]+\s*([\d\.]+)\s*(ppm|%)?', line, re.IGNORECASE)
            if m:
                elem, value, unit = m.groups()
                try:
                    val = float(value)
                    if unit and '%' in unit.lower():
                        val *= 10000
                    result[f"{elem}_ppm"] = val
                except ValueError:
                    pass

        return result


# Quick self-test when run directly (optional)
if __name__ == "__main__":
    sample_output = """
Analyte, Concentration, Unit
Zr,145.2,ppm
Nb,18.7,ppm
Ba,260.0,ppm
Fe,12.4,%
    """

    parser = NitonParser()
    parsed = parser.parse(sample_output)
    print("Parsed elements:")
    for elem, val in sorted(parsed.items()):
        print(f"  {elem:8} = {val:.1f}")
