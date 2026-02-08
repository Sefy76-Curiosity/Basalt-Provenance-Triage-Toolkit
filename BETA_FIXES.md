# BETA TESTER FIXES - v10.1.1
# This script documents all fixes needed based on beta feedback

## ISSUE 1: PDF Export - Missing attribute 'report_include_samples'
**STATUS:** ✅ FIXED
**FILE:** plugins/advanced_export.py
**FIX:** Added missing checkbox for report_include_samples between lines 173-178

## ISSUE 2: Advanced Filter - IoGAS name copyright issue
**STATUS:** ✅ FIXED  
**FILES:** plugins/advanced_filter.py
**FIX:** Removed all "IoGAS" references, changed to "Advanced Filter" and "Logical Query Language"

## ISSUE 3: Advanced Filter - Opens empty
**STATUS:** ⚠️ NEEDS INVESTIGATION
**NOTES:** Method name is correct (open_advanced_filter_window), _create_interface() is called
**POSSIBLE CAUSES:**
- Runtime error in _create_interface() being silently caught
- User needs to enable plugin in Plugin Manager first
- Missing dependencies (but should show error)

## ISSUE 4: Data Validation - Opens empty
**STATUS:** ⚠️ NEEDS INVESTIGATION
**NOTES:** Similar to Advanced Filter issue

## ISSUE 5: Discrimination Diagrams - Plot windows go behind
**STATUS:** ❌ NEEDS FIX
**FILES:** plugins/discrimination_diagrams.py
**FIX NEEDED:** Add parent=self.window to all messagebox calls (lines 337, 427, 468, 573)

## ISSUE 6: TAS, Wood, Shervais - Button not greyed when no samples
**STATUS:** ❌ NEEDS FIX
**FILES:** plugins/discrimination_diagrams.py and others
**FIX NEEDED:** Disable buttons when no valid data detected

## ISSUE 7: 3D/GIS Viewer - Opens empty
**STATUS:** ⚠️ CHECK IF SAMPLES HAVE LAT/LONG
**NOTES:** This plugin requires Latitude/Longitude data in samples
**FIX NEEDED:** Show helpful message if no coordinates found

## ISSUE 8: Google Earth - Opens empty
**STATUS:** ⚠️ CHECK IF SAMPLES HAVE LAT/LONG
**NOTES:** Requires Latitude/Longitude data
**FIX NEEDED:** Show helpful message if no coordinates found

## ISSUE 9: Literature Comparison - Opens empty
**STATUS:** ⚠️ NEEDS INVESTIGATION
**NOTES:** May require numpy

## ISSUE 10: Photo Manager - Opens empty
**STATUS:** ⚠️ NEEDS INVESTIGATION

## ISSUE 11: Report Generator - Opens empty
**STATUS:** ⚠️ CHECK IF python-docx INSTALLED
**NOTES:** Early return if HAS_DOCX is False

## ISSUE 12: DFA - Button doesn't do anything
**STATUS:** ❌ NEEDS FIX
**FILES:** plugins/statistical_analysis.py
**FIX NEEDED:** Check _run_dfa method, add validation

## ISSUE 13: Ternary Diagrams - Button not greyed when no samples
**STATUS:** ❌ NEEDS FIX
**FILES:** plugins/ternary_diagrams.py
**FIX NEEDED:** Disable button when no major element data

---

## PRIORITY FIXES (DO NOW):
1. Fix messagebox parent parameters (discrimination_diagrams)
2. Add button disabling when no data
3. Add helpful error messages for plugins that need specific data
4. Fix DFA button

## INVESTIGATION NEEDED:
- Why multiple plugins show "empty" - need to test with actual data
- May be user not enabling plugins
- May be missing dependencies not being caught properly
