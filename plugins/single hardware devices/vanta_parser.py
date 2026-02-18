# vanta_parser.py
# Evident / Olympus Vanta series

import re

class VantaParser:
    """Parser for Olympus / Evident Vanta pXRF output"""

    def parse(self, raw_text: str) -> dict[str, float]:
        result = {}
        lines = raw_text.splitlines()

        in_data = False

        for line in lines:
            line = line.strip()

            if 'Element' in line and 'Concentration' in line:
                in_data = True
                continue

            if in_data and line:
                # Zr   152.4 ppm
                parts = re.split(r'\s+', line)
                if len(parts) >= 2:
                    elem = parts[0].strip()
                    try:
                        val_str = parts[1].replace(',', '')
                        val = float(val_str)
                        if len(parts) > 2 and '%' in parts[2].lower():
                            val *= 10000
                        result[f"{elem}_ppm"] = val
                    except:
                        pass

            # Fallback: any line with element + number + optional unit
            m = re.search(r'([A-Z][a-z]?)\s+([\d\.,]+)\s*(ppm|%)?', line, re.I)
            if m:
                elem, value, unit = m.groups()
                try:
                    val = float(value.replace(',', ''))
                    if unit and '%' in unit.lower():
                        val *= 10000
                    result[f"{elem}_ppm"] = val
                except:
                    pass

        return result
