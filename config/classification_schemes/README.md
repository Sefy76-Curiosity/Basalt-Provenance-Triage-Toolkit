# Classification Schemes for Basalt Provenance Triage Toolkit

This folder contains classification schemes that define how samples are automatically classified based on their geochemical data.

## 📁 What's in This Folder

Each `.json` file is a classification scheme that can be loaded and run by the tool.

**Built-in Schemes:**
- `regional_triage.json` - Standard Levantine classification (Egyptian, Sinai, Local)
- `western_saharan.json` - Richat, Macaronesian, Central Saharan sources
- `tectonic_environment.json` - Geological origin (Rift, OIB, MORB, Arc, etc.)
- `_TEMPLATE.json` - Template for creating your own schemes

## 🎯 How It Works

1. The tool auto-discovers all `.json` files in this folder
2. When you click "Classify All", you choose which scheme to run
3. The scheme's rules are applied to your samples
4. Results appear in a new column in your data

## 🔧 Creating Your Own Scheme

1. Copy `_TEMPLATE.json` to a new file (e.g., `my_custom_scheme.json`)
2. Edit the JSON file:
   - Change `scheme_name`, `author`, `description`
   - Define your `classifications` with rules
   - Specify `output_column_name`
3. Save the file
4. Restart the app or click "Refresh Schemes"
5. Your scheme appears in the menu!

## 📝 JSON Structure

```json
{
  "scheme_name": "Your Scheme Name",
  "classifications": [
    {
      "name": "CATEGORY NAME",
      "rules": [
        {"field": "Zr_ppm", "operator": ">", "value": 100},
        {"field": "Nb_ppm", "operator": "<", "value": 20}
      ],
      "logic": "AND"
    }
  ]
}
```

## 🔢 Supported Operators

- `>` - Greater than
- `<` - Less than
- `>=` - Greater than or equal
- `<=` - Less than or equal
- `==` - Equal to
- `!=` - Not equal to
- `between` - Between min and max (inclusive)

## 📊 Available Fields

Any column in your data can be used! Common fields:

**Elements (ppm):**
- Zr_ppm, Nb_ppm, Ti_ppm, Y_ppm, V_ppm
- Ba_ppm, Rb_ppm, Sr_ppm, Cr_ppm, Ni_ppm

**Ratios:**
- Zr_Nb_Ratio, Cr_Ni_Ratio, Ba_Rb_Ratio
- Ti_V_Ratio, Nb_Y_Ratio, Zr_Y_Ratio

**Physical:**
- Wall_Thickness_mm, Weight_g

**Location:**
- Latitude, Longitude, Elevation

## 🎨 Colors

Choose from: red, blue, green, orange, purple, brown, gray, cyan, teal, pink, yellow, etc.

## 💡 Tips

**Priority:** Lower numbers run first. Set priority=1 for most specific rules.

**Confidence:** Higher scores (1-5) indicate stronger matches.

**Logic:** 
- "AND" = All rules must match
- "OR" = Any rule can match
- "DEFAULT" = Catch-all for samples that don't match anything

## 🌍 Sharing Schemes

To share your scheme with others:
1. Upload your `.json` file to GitHub, email, or cloud storage
2. Others download and place in their `classification_schemes/` folder
3. Instant access to your classification logic!

## 📚 Examples

### Simple Two-Category Scheme:
```json
{
  "scheme_name": "High vs Low Zr",
  "classifications": [
    {
      "name": "HIGH ZIRCONIUM",
      "rules": [{"field": "Zr_ppm", "operator": ">", "value": 150}]
    },
    {
      "name": "LOW ZIRCONIUM",
      "rules": [{"field": "Zr_ppm", "operator": "<=", "value": 150}]
    }
  ]
}
```

### Multi-Rule Scheme:
```json
{
  "classifications": [
    {
      "name": "EGYPTIAN TYPE",
      "rules": [
        {"field": "Zr_Nb_Ratio", "operator": ">", "value": 8},
        {"field": "Ba_ppm", "operator": "between", "min": 240, "max": 300}
      ],
      "logic": "AND"
    }
  ]
}
```

## 🚀 Advanced Features

**Confidence Thresholds:**
```json
"confidence_threshold": 0.75
```
Only classify if confidence > 75%

**Flag Uncertain:**
```json
"flag_uncertain": true,
"uncertain_threshold": 2
```
Flag samples with confidence < 2 for review

**Multiple Output Columns:**
Run multiple schemes! Each creates its own column:
- Regional Triage → `Auto_Classification`
- Western Saharan → `Saharan_Classification`
- Tectonic → `Tectonic_Origin`

Compare results across different classification approaches!

## 📖 Further Reading

For detailed documentation on creating schemes, see:
- User Manual (in docs/)
- Example schemes in this folder
- Community schemes on GitHub

## 🤝 Contributing

Created a useful classification scheme? Share it!
- GitHub: basalt-classification-schemes repository
- Email to: toolkit@example.com
- Community forum: [link]

Help build the ecosystem of classification schemes!

---

**Happy Classifying!** 🎉
