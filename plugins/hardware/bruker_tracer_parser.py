# bruker_tracer_parser.py
# Bruker Tracer 5g / S1 Titan series

import re

class BrukerTracerParser:
    """Parser for Bruker Tracer / S1 Titan pXRF output"""

    def parse(self, raw_text: str) -> dict[str, float]:
        result = {}
        lines = raw_text.splitlines()

        for line in lines:
            line = line.strip()
            if not line or 'Element' in line or line.startswith('---'):
                continue

            # Zr: 145.2 ppm
            m = re.match(r'([A-Z][a-z]?):?\s*([\d\.]+)\s*(ppm|%)?', line, re.I)
            if m:
                elem, value, unit = m.groups()
                try:
                    val = float(value)
                    if unit and '%' in unit.lower():
                        val *= 10000
                    result[f"{elem}_ppm"] = val
                except:
                    pass

            # Zr 145.2 ppm    or    Zr   145.2
            m = re.search(r'([A-Z][a-z]?)\s+([\d\.]+)\s*(ppm|%)?', line, re.I)
            if m:
                elem, value, unit = m.groups()
                try:
                    val = float(value)
                    if unit and '%' in unit.lower():
                        val *= 10000
                    result[f"{elem}_ppm"] = val
                except:
                    pass

        return result
