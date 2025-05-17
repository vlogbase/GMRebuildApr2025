# Mobile Text Input Height Fix

## Problem
The mobile text entry box (`#message-input`) was not properly growing to its intended maximum height of at least 500 pixels as text was entered. This was due to conflicts between CSS fixed height rules and JavaScript's dynamic height calculations.

## Root Causes

1. **Fixed CSS Height Constraint**: 
   - A `height: 100px` CSS rule in the mobile media query was preventing the textarea from growing beyond 100px.

2. **Restrictive CSS Max-Height**: 
   - The rule `.chat-input-container.keyboard-visible #message-input { max-height: calc(100vh - 240px); }` could result in a max-height less than the desired 500px on smaller devices.

3. **JavaScript/CSS Mismatch**: 
   - The JavaScript was attempting to allow growth up to at least 500px, but CSS constraints were overriding this.

## Solution Implemented

### CSS Changes:

1. **Removed Fixed Height**:
   - Changed the mobile media query from fixed `height: 100px` to `min-height: 80px`
   - This allows the textarea to grow dynamically based on content

2. **Improved Keyboard CSS**:
   - Removed the fixed `max-height: calc(100vh - 240px)` constraint
   - Added a CSS variable `--viewport-keyboard-max-height` with the calculated value
   - This allows JavaScript to respect viewport constraints while still attempting to reach target heights

### JavaScript Enhancements:

1. **CSS Variable Integration**:
   - Modified `autoResizeTextarea()` to read the CSS variable for viewport constraints
   - Added dynamic calculation that respects both target height (500px) and available viewport space
   - Implemented a minimum usable height (150px) even when keyboard is visible

2. **Improved Mobile Detection**:
   - Maintained existing keyboard visibility detection
   - Added enhanced logging to help diagnose sizing issues
   - Implemented fallbacks when CSS variables aren't available

## Benefits

1. The text entry box now properly grows as content is added, up to the target height of 500px when space allows.
2. The textarea maintains a usable minimum height even when the on-screen keyboard is visible.
3. Layout is preserved across different mobile device sizes and orientations.
4. The solution harmonizes CSS and JavaScript approaches rather than having them conflict.

## Testing Notes

This change should be tested on various mobile devices with different viewport sizes to ensure:
- The textarea grows properly as text is entered
- The text area maintains appropriate size when keyboard appears/disappears
- The layout remains consistent and usable across different device orientations